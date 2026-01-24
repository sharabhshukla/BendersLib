# coding:utf-8

import pyomo.environ as pyo
from pyomo.core import Var, Objective, Constraint, Suffix
from pyomo.core.expr.visitor import identify_variables
from pyomo.repn import generate_standard_repn

from ..consts import BendersConsts as CST
from ._base import SolverBase


class Pyomo(SolverBase):
    """Pyomo solver interface for BendersLib.

    This class provides an interface to Pyomo for use with BendersLib.
    It implements the methods defined in the :class:`~benderslib.SolverBase` class.
    Refer to :ref:`solver-table` for the supported features of this interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------

    model: pyomo.environ.ConcreteModel
        An instance of Pyomo's ``ConcreteModel``.
    solver: str
        The solver to be used with Pyomo (e.g., ``'gurobi'``, ``'gurobi_direct'``, etc.,
        see :ref:`supported solvers <solver-table>`).
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: pyo.ConcreteModel, solver: str, solver_options: dict = None) -> None:
        super().__init__(model)

        self.__solver_name = solver.lower()
        self.__solver_options = solver_options if solver_options is not None else {}
        self.solver_factory = self.__init_solver_factory()

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        self._sense = CST.MIN if model.obj.sense == pyo.minimize else CST.MAX
        self._all_vars = [v.name for v in model.component_data_objects(Var)]
        self._bin_vars = [v.name for v in model.component_data_objects(Var) if v.is_binary()]
        self._int_vars = [v.name for v in model.component_data_objects(Var) if v.is_integer() and not v.is_binary()]

        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {}
        for v in model.component_data_objects(Var):
            lb = v.lb if v.lb is not None else -float('inf')
            ub = v.ub if v.ub is not None else float('inf')
            if lb != 0 or ub != float('inf'):
                self._var_bounds[v.name] = (lb, ub)

        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(list(model.component_data_objects(Constraint, active=True)))

        # If the model has no integer and binary variables, we can access dual values
        if len(self._bin_vars) + len(self._int_vars) == 0:
            if not hasattr(self.model, 'dual'):
                self.model.dual = Suffix(direction=Suffix.IMPORT)

    def __init_solver_factory(self) -> pyo.SolverFactory:
        if '_persistent' in self.__solver_name:
            raise NotImplementedError("BendersLib currently does not support Pyomo persistent solvers.")

        _solver_options = {
            # Hide solver output
            'gurobi': {'OutputFlag': 0, 'LogToConsole': 0, 'InfUnbdInfo': 1, 'QCPDual': 1},
            'gurobi_direct': {'OutputFlag': 0, 'LogToConsole': 0, 'InfUnbdInfo': 1, 'QCPDual': 1},
            'scip': {
                'presolving/maxrounds': 0, 'separating/maxrounds': 0, 'propagating/maxrounds': 0,
                'lp/alwaysgetduals': True
            },
        }
        _options = _solver_options.get(self.__solver_name, {})
        _options.update(self.__solver_options)

        solver_factory = pyo.SolverFactory(self.__solver_name, options=_options)
        return solver_factory

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self._sense == CST.MAX:
            raise NotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            # From here, the default variable bounds become (0, +inf), despite that the Pyomo default is (-inf, +inf).
            raise NotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.find_component(var_name)
            if lb > 0:
                self.model.add_component(f"_{var_name}_lb", Constraint(expr=var >= lb))
                var.setlb(0)
            if ub < float('inf'):
                self.model.add_component(f"_{var_name}_ub", Constraint(expr=var <= ub))
                var.setub(None)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            prob = [1.0] * len(estimators)

        if len(prob) != len(estimators):
            raise ValueError("Length of 'prob' must match length of 'estimators'.")

        obj = next(self.model.component_data_objects(Objective, active=True))

        for name, p in zip(estimators, prob):
            self.model.add_component(name, Var(within=pyo.NonNegativeReals, initialize=lb))
            obj.expr += p * self.model.find_component(name)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            var = self.model.find_component(var_name)
            var.fix(var_value)

    def unfix_vars(self, vars: list[str]) -> None:
        for var_name in vars:
            var = self.model.find_component(var_name)
            var.set_value(None)
            var.unfix()

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {var_name: pyo.value(self.model.find_component(var_name)) for var_name in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        vars_to_get = vars or self._all_vars
        coefs = {v: [] for v in vars_to_get}

        cons = self.model.component_data_objects(Constraint, active=True)
        for c in cons:
            repn = generate_standard_repn(c.body)
            coef_dict = {var.name: coef for var, coef in zip(repn.linear_vars, repn.linear_coefs)}
            for v in vars_to_get:
                coefs[v].append(coef_dict.get(v, 0.0))

        return coefs

    def get_rhs(self) -> list[float]:
        cons = self.model.component_data_objects(Constraint, active=True)
        rhs = []
        for c in cons:
            if c.equality:
                rhs.append(pyo.value(c.lower))
            elif c.has_ub() and not c.has_lb():
                rhs.append(pyo.value(c.upper))
            elif c.has_lb() and not c.has_ub():
                rhs.append(pyo.value(c.lower))
            else:
                raise ValueError(f"Constraint has both bounds ({c.lower, c.upper}). Cannot determine RHS.")
        return rhs

    def get_dual_values(self) -> list[float]:
        # if self.__solver_name == 'scip':
        #     raise NotImplementedError("BendersLib cannot get correct dual values with Pyomo(solver='scip').")

        # Dual values are only available from a subset of Pyomo supported solvers.
        duals = [self.model.dual[c] for c in self.model.component_data_objects(Constraint, active=True)]
        return duals

    def get_extreme_ray(self) -> list[float]:
        # Pyomo does not provide Farkas duals (extreme rays).
        raise NotImplementedError("Farkas dual (for feasibility cuts) is not supported in the Pyomo interface yet.")

    def get_obj(self) -> float:
        obj = next(self.model.component_data_objects(Objective, active=True))
        return pyo.value(obj.expr)

    def add_cut(self, cut, name=None) -> None:
        vars = [self.model.find_component(v) for v in cut.vars]
        expr = sum(coef * var for coef, var in zip(cut.coefs, vars))

        if cut.sense == CST.EQ:
            self.model.add_component(name, Constraint(expr=expr == cut.rhs))
        elif cut.sense == CST.LE:
            self.model.add_component(name, Constraint(expr=expr <= cut.rhs))
        elif cut.sense == CST.GE:
            self.model.add_component(name, Constraint(expr=expr >= cut.rhs))

    def remove_cut(self, cut_name: str) -> None:
        self.model.del_component(cut_name)

    def solve(self) -> None:
        # Solve the model
        results = self.solver_factory.solve(self.model, tee=False, load_solutions=False)
        term_cond = results.solver.termination_condition

        # Update status
        _pyomo_status_map = {
            pyo.TerminationCondition.optimal: CST.OPTIMAL,
            pyo.TerminationCondition.infeasible: CST.INFEASIBLE,
        }
        self.status = _pyomo_status_map.get(term_cond, CST.UNKNOWN)

        if self.status == CST.OPTIMAL:
            # Load solution back to the model
            self.model.solutions.load_from(results)

    @staticmethod
    def make_master_problem(original_model: pyo.ConcreteModel, master_vars: list[str]) -> pyo.ConcreteModel:
        master = original_model.clone()

        # Remove non-master variables from objective (ONLY handle linear case)
        obj = next(master.component_data_objects(Objective, active=True))
        repn = generate_standard_repn(obj.expr)
        new_expr = sum(
            coef * master.find_component(var.name)
            for coef, var in zip(repn.linear_coefs, repn.linear_vars)
            if var.name in master_vars
        )
        master.del_component(obj)
        master.obj = Objective(expr=new_expr, sense=pyo.minimize)

        # Remove constraints that contains non-master variables
        _cons_to_remove_idx = []
        constrs = list(master.component_data_objects(Constraint, active=True))

        for i, constr in enumerate(constrs):
            for var in identify_variables(constr.expr):
                if var.name not in master_vars:
                    _cons_to_remove_idx.append(i)
                    break

        # Execute removal
        for i in reversed(_cons_to_remove_idx):
            # constrs[i].deactivate()
            cons = constrs[i]
            del cons.parent_component()[cons.index()]

        # Remove non-master variables
        _vars_to_remove_idx = []
        vars = list(master.component_data_objects(Var, active=True))

        for i, var in enumerate(vars):
            if var.name not in master_vars:
                _vars_to_remove_idx.append(i)

        # Execute removal
        for i in reversed(_vars_to_remove_idx):
            var = vars[i]
            del var.parent_component()[var.index()]

        return master

    @staticmethod
    def make_sub_problem(original_model: pyo.ConcreteModel, master_vars: list[str]) -> pyo.ConcreteModel:
        sub = original_model.clone()

        # Set master variables to continuous
        for var_name in master_vars:
            var = sub.find_component(var_name)
            # Set potentially binary/integer master variables to continuous for obtaining duals
            var.domain = pyo.Reals

        # Remove master variables from objective (ONLY handle linear case)
        obj = next(sub.component_data_objects(Objective, active=True))
        repn = generate_standard_repn(obj.expr)
        new_expr = sum(
            coef * var
            for coef, var in zip(repn.linear_coefs, repn.linear_vars)
            if var.name not in master_vars
        )
        sub.del_component(obj)
        sub.obj = Objective(expr=new_expr, sense=pyo.minimize)

        # Remove constraints that contains only master variables
        _cons_to_remove_idx = []
        constrs = list(sub.component_data_objects(Constraint, active=True))

        for i, constr in enumerate(constrs):
            is_master_only = True
            for var in identify_variables(constr.expr):
                if var.name not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                _cons_to_remove_idx.append(i)

        # Execute removal
        for i in reversed(_cons_to_remove_idx):
            # constrs[i].deactivate()
            cons = constrs[i]
            del cons.parent_component()[cons.index()]

        return sub


if __name__ == "__main__":
    pass

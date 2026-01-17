# coding:utf-8

try:
    import pyomo.environ as pyo
    from pyomo.core import Var, Objective, Constraint, Suffix
    from pyomo.core.expr.visitor import identify_variables
    from pyomo.repn import generate_standard_repn
except ImportError:
    raise ImportError("Pyomo is not installed. Install it via 'pip install pyomo'.")

from ..consts import BendersConsts as CST
from .base import SolverBase


class Pyomo(SolverBase):
    """Pyomo solver interface for BendersLib.

    This class provides an interface to Pyomo for use with BendersLib.
    It implements the methods defined in the :class:`~benderslib.SolverBase` class.

    Parameters
    ---------------
    model: pyomo.environ.ConcreteModel
        An instance of Pyomo's ``ConcreteModel``.
    """

    def __init__(self, model: pyo.ConcreteModel, solver=None) -> None:
        if not solver:
            # solver = 'gurobi'
            raise ValueError("A solver must be specified for the Pyomo interface.")
        solver_name_map = {
            'gurobi': 'gurobi_direct',
        }
        self.solver = solver_name_map.get(solver, solver)

        super().__init__(model)

        # Attributes required by SolverBase
        self.status = CST.UNSOLVED
        self._solver_model = model
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
        _all_constrs = list(model.component_data_objects(Constraint, active=True))
        self._constr_num = len(_all_constrs)

        # If the model has no integer and binary variables, we can access dual values
        if len(self._bin_vars) + len(self._int_vars) == 0:
            if not hasattr(self.model, 'dual'):
                self.model.dual = Suffix(direction=Suffix.IMPORT)

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
        # Dual values are only available from a subset of Pyomo supported solvers.
        duals = [self.model.dual[c] for c in self.model.component_data_objects(Constraint, active=True)]
        return duals

    def get_extreme_ray(self) -> list[float]:
        # Pyomo does not provide Farkas duals (extreme rays).
        raise NotImplementedError("Farkas dual is not supported in the Pyomo interface yet.")

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
        # Hide solver output
        options = {'OutputFlag': 0, 'LogToConsole': 0}
        solver_factory = pyo.SolverFactory(self.solver, options=options, manage_env=True)

        # Solve the model
        results = solver_factory.solve(self.model, tee=False)

        # Update status
        term_cond = results.solver.termination_condition
        if term_cond == pyo.TerminationCondition.optimal:
            self.status = CST.OPTIMAL
        elif term_cond == pyo.TerminationCondition.infeasible:
            self.status = CST.INFEASIBLE
        else:
            self.status = CST.ERROR
            raise Exception(f"Solver terminated with unexpected condition: {term_cond}")

    @staticmethod
    def make_master_problem(original_model: pyo.ConcreteModel, master_vars: list[str]) -> pyo.ConcreteModel:
        master = original_model.clone()

        # Remove non-master variables from objective (ONLY handle linear case)
        obj = next(master.component_data_objects(Objective, active=True))
        new_expr = sum(
            coef * master.find_component(var.name)
            for coef, var in zip(obj.expr.linear_coefs, obj.expr.linear_vars)
            if var.name in master_vars
        )
        master.del_component(obj)
        master.obj = Objective(expr=new_expr, sense=pyo.minimize)

        # Remove constraints that contains non-master variables
        for constr in master.component_data_objects(Constraint, active=True):
            for var in identify_variables(constr.expr):
                if var.name not in master_vars:
                    master.del_component(constr)
                    break

        # Remove non-master variables
        for var in master.component_data_objects(Var):
            if var.name not in master_vars:
                master.del_component(var)

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
        new_expr = sum(
            coef * var
            for coef, var in zip(obj.expr.linear_coefs, obj.expr.linear_vars)
            if var.name not in master_vars
        )
        sub.del_component(obj)
        sub.obj = Objective(expr=new_expr, sense=pyo.minimize)

        # Remove constraints that contains only master variables
        for constr in sub.component_data_objects(Constraint, active=True):
            is_master_only = True
            for var in identify_variables(constr.expr):
                if var.name not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                sub.del_component(constr)

        return sub


if __name__ == "__main__":
    pass

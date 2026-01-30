# coding:utf-8

from cplex import Cplex as CplexModel, infinity as CPLEX_INFINITY

from ..consts import BendersConsts as CST
from ._base import SolverBase


class Cplex(SolverBase):
    """CPLEX solver interface for BendersLib.

    This class provides an interface to the CPLEX solver for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------
    model: cplex.Cplex
        An instance of CPLEX's ``cplex.Cplex``.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: CplexModel, solver_options: dict = None) -> None:
        super().__init__(model)

        # Attributes in CPLEX Model
        sense = self.model.objective.get_sense()
        vars = self.model.variables.get_names()

        if self.model.get_problem_type() == 0:
            # 0: LP
            vtypes = ['C'] * len(vars)
        else:
            # MIP
            vtypes = self.model.variables.get_types(vars)

        lbs = self.model.variables.get_lower_bounds(vars)
        ubs = self.model.variables.get_upper_bounds(vars)

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        self._sense = CST.MIN if sense == self.model.objective.sense.minimize else CST.MAX
        self._all_vars = vars
        self._bin_vars = [v for v, t in zip(self._all_vars, vtypes) if t == self.model.variables.type.binary]
        self._int_vars = [v for v, t in zip(self._all_vars, vtypes) if t == self.model.variables.type.integer]
        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {
            v: (lb, ub) for v, lb, ub in zip(self._all_vars, lbs, ubs) if lb != 0 or ub < CPLEX_INFINITY}
        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = self.model.linear_constraints.get_num()

        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self._sense == CST.MAX:
            raise NotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise NotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            if lb != 0:
                self.model.linear_constraints.add(
                    lin_expr=[[[var_name], [1.0]]],
                    senses=["G"],
                    rhs=[lb]
                )
                self.model.variables.set_lower_bounds(var_name, 0.0)
            if ub < CPLEX_INFINITY:
                self.model.linear_constraints.add(
                    lin_expr=[[[var_name], [1.0]]],
                    senses=["L"],
                    rhs=[ub]
                )
                self.model.variables.set_upper_bounds(var_name, CPLEX_INFINITY)

    def __setup_model(self, solver_options: dict = None):
        # Hide solver output
        self.model.set_log_stream(None)
        self.model.set_error_stream(None)
        self.model.set_warning_stream(None)
        self.model.set_results_stream(None)

        # Parameter for obtaining Farkas certificate
        self.model.parameters.preprocessing.presolve.set(0)
        self.model.parameters.lpmethod.set(2)

        # Setup solver options
        if solver_options:
            for option, value in solver_options.items():
                # This is a bit tricky as cplex parameters are nested
                # e.g. model.parameters.mip.tolerances.mipgap.set(0.01)
                # We assume solver_options is a dict like {'mip.tolerances.mipgap': 0.01}
                keys = option.split('.')
                param = self.model.parameters
                for key in keys[:-1]:
                    param = getattr(param, key)
                getattr(param, keys[-1]).set(value)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1]
            else:
                prob = [1 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise ValueError("Length of 'prob' must match length of 'estimators'.")

        self.model.variables.add(
            obj=prob,
            lb=[lb] * len(estimators),
            names=estimators,
            types=[self.model.variables.type.continuous] * len(estimators)
        )

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            self.model.variables.set_lower_bounds(var_name, var_value)
            self.model.variables.set_upper_bounds(var_name, var_value)

    def unfix_vars(self, vars: list[str]) -> None:
        for var_name in vars:
            lb, ub = self._var_bounds.get(var_name, (0, CPLEX_INFINITY))
            self.model.variables.set_lower_bounds(var_name, lb)
            self.model.variables.set_upper_bounds(var_name, ub)

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        values = self.model.solution.get_values(vars_to_get)
        return dict(zip(vars_to_get, values))

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        vars_to_get = vars or self._all_vars
        num_constrs = self.model.linear_constraints.get_num()
        res = {v: [0.0] * num_constrs for v in vars_to_get}
        for i in range(num_constrs):
            row = self.model.linear_constraints.get_rows(i)
            for var_idx, coef in zip(row.ind, row.val):
                var_name = self.model.variables.get_names(var_idx)
                if var_name in res:
                    res[var_name][i] = coef
        return res

    def get_rhs(self) -> list[float]:
        rhs = self.model.linear_constraints.get_rhs()
        return rhs

    def get_dual_values(self) -> list[float]:
        dual = self.model.solution.get_dual_values()
        return dual

    def get_extreme_ray(self) -> list[float]:
        ray, _ = self.model.solution.advanced.dual_farkas()
        ray = [-r for r in ray]
        return ray

    def get_obj(self) -> float:
        return self.model.solution.get_objective_value()

    def add_cut(self, cut, name=None) -> None:
        sense_map = {
            CST.EQ: "E",
            CST.LE: "L",
            CST.GE: "G"
        }
        self.model.linear_constraints.add(
            lin_expr=[[cut.vars, cut.coefs]],
            senses=[sense_map[cut.sense]],
            rhs=[cut.rhs],
            names=[name] if name else []
        )

    def remove_cut(self, cut_name: str) -> None:
        self.model.linear_constraints.delete(cut_name)

    def solve(self) -> None:
        # Change the problem type to LP to get dual values or extreme rays
        if len(self._int_vars) + len(self._bin_vars) == 0:
            problem_type = self.model.get_problem_type()
            if problem_type != self.model.problem_type.LP:
                self.model.set_problem_type(self.model.problem_type.LP)

        self.model.solve()

        status = self.model.solution.get_status()
        sol_status = self.model.solution.status

        _cplex_status_map = {
            sol_status.optimal: CST.OPTIMAL,
            sol_status.MIP_optimal: CST.OPTIMAL,
            sol_status.infeasible: CST.INFEASIBLE,
            sol_status.MIP_infeasible: CST.INFEASIBLE,
            102: CST.OPTIMAL
        }
        self.status = _cplex_status_map.get(status, CST.UNKNOWN)

    def compute_iis(self) -> set[str]:
        self.model.conflict.refine()

        vars = set()

        for i, row in enumerate(self.model.linear_constraints.get_rows()):

            # 3: the constraint is in the IIS; -1: the constraint is not in the IIS
            is_in_iis = self.model.conflict.get(i) == 3
            # print(i, row, self.model.conflict.get(i))

            if is_in_iis:
                for var_idx in row.ind:
                    var_name = self.model.variables.get_names(var_idx)
                    vars.add(var_name)

        return vars

    @staticmethod
    def make_master_problem(original_model: CplexModel, master_vars: list[str]) -> CplexModel:
        master = CplexModel(original_model)
        non_master_vars = list(set(master.variables.get_names()) - set(master_vars))

        # Remove constraints that contains non-master variables
        _cons_to_remove_name = []
        constrs = master.linear_constraints.get_names()

        for constr_name in constrs:
            row = master.linear_constraints.get_rows(constr_name)
            for var_idx in row.ind:
                var_name = master.variables.get_names(var_idx)
                if var_name in non_master_vars:
                    _cons_to_remove_name.append(constr_name)
                    break

        # Execute removal
        master.linear_constraints.delete(_cons_to_remove_name)

        # Remove non-master variables & remove them from objective (will be handled automatically)
        master.variables.delete(non_master_vars)

        return master

    @staticmethod
    def make_sub_problem(original_model: CplexModel, master_vars: list[str]) -> CplexModel:
        sub = CplexModel(original_model)

        # Set master variables to continuous & remove them from objective
        for var_name in master_vars:
            sub.variables.set_types(var_name, sub.variables.type.continuous)
            sub.objective.set_linear(var_name, 0.0)

        # Remove constraints that contains only master variables
        _cons_to_remove_name = []
        constrs = sub.linear_constraints.get_names()

        for constr_name in constrs:
            row = sub.linear_constraints.get_rows(constr_name)
            only_master_vars = True
            for var_idx in row.ind:
                var_name = sub.variables.get_names(var_idx)
                if var_name not in master_vars:
                    only_master_vars = False
                    break
            if only_master_vars:
                _cons_to_remove_name.append(constr_name)

        # Execute removal
        sub.linear_constraints.delete(_cons_to_remove_name)

        return sub


if __name__ == '__main__':
    pass

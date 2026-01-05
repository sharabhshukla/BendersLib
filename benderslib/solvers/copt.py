# coding:utf-8

from ..consts import BendersConsts as CST
from .base import SolverBase

try:
    import coptpy as cp
    from coptpy import COPT
except ImportError:
    raise ImportError("COPT is not installed. Please install it to use the COPT solver interface.")


class Copt(SolverBase):
    """COPT solver interface for BendersLib.

    This class provides an interface to the COPT solver for use with BendersLib.
    It implements the abstract methods defined in the :class:`~benderslib.SolverBase` class.
    Two additional methods, :func:`make_master_problem` and :func:`make_sub_problem`,
    are provided for automatic decomposition by :class:`~benderslib.AnnotationBenders`.

    Parameters
    ---------------
    model: coptpy.Model
        An instance of COPT's ``coptpy.Model``.
    """

    def __init__(self, model: cp.Model) -> None:
        # model.update()
        super().__init__(model)

        # Attributes in COPT Model
        sense = model.objsense
        variables = model.getVars()
        vtypes = [v.getType() for v in variables]
        lbs = [v.getInfo(COPT.Info.LB) for v in variables]
        ubs = [v.getInfo(COPT.Info.UB) for v in variables]

        # Attributes required by SolverBase
        self.status = CST.UNSOLVED
        self._solver_model = model
        self._sense = CST.MIN if sense == COPT.MINIMIZE else CST.MAX
        self._all_vars = [v.getName() for v in variables]
        self._bin_vars = [v for v, t in zip(self._all_vars, vtypes) if t == COPT.BINARY]
        self._int_vars = [v for v, t in zip(self._all_vars, vtypes) if t == COPT.INTEGER]
        self._var_bounds = {v: (lb, ub) for v, lb, ub in zip(self._all_vars, lbs, ubs) if
                            lb != 0 or ub != COPT.INFINITY}
        self.__standardize()
        self._rhs = self.get_rhs()

    def __standardize(self):
        # self.__sense_to_minimize()
        # self.__bounds_to_constrs()
        ...

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self.model.objsense == COPT.MAXIMIZE:
            self.model.setObjective(self.model.getObjective(), sense=COPT.MINIMIZE)

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise ValueError("COPT interface currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.getVarByName(var_name)
            if lb != 0:
                self.model.addConstr(var >= lb)
                var.lb = 0
            if ub < COPT.INFINITY:
                self.model.addConstr(var <= ub)
                var.ub = COPT.INFINITY

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1]
            else:
                prob = [1 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise ValueError("Length of 'prob' must match length of 'estimators'.")

        for var_name, obj in zip(estimators, prob):
            self.model.addVar(lb=lb, vtype=COPT.CONTINUOUS, obj=obj, name=var_name)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            var = self.model.getVarByName(var_name)
            var.lb = var_value
            var.ub = var_value

    def unfix_vars(self, vars: list[str]) -> None:
        print(self._var_bounds)
        for var_name in vars:
            var = self.model.getVarByName(var_name)
            var.lb, var.ub = self._var_bounds.get(var_name, (0, COPT.INFINITY))

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {var_name: self.model.getVarByName(var_name).x for var_name in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        A_matrix = self.model.getA()
        model_vars = self.model.getVars()
        var_to_col_idx = {v.name: i for i, v in enumerate(model_vars)}
        vars_to_process = vars or self._all_vars
        res = {}
        for v_name in vars_to_process:
            col_idx = var_to_col_idx.get(v_name)
            if col_idx is not None:
                var_coeffs = A_matrix[:, col_idx]
                res[v_name] = var_coeffs.toarray().flatten().tolist()
        return res

    def get_rhs(self) -> list[float]:
        cons = self.model.getConstrs()
        rhs = []
        for c in cons:
            if c.ub == COPT.INFINITY:
                rhs.append(c.lb)
            elif c.lb == -COPT.INFINITY:
                rhs.append(c.ub)
            elif c.lb == c.ub:
                rhs.append(c.lb)
            else:
                raise ValueError(f"Constraint {c.getName()} has both bounds ({c.lb}, {c.ub}). Cannot determine RHS.")
        return rhs

    def get_dual_values(self) -> list[float]:
        return self.model.getDuals()

    def get_extreme_ray(self) -> list[float]:
        ray = self.model.getInfo(COPT.Info.DualFarkas, self.model.getConstrs())
        # COPT returns Farkas Dual with opposite sign to Gurobi
        ray = [-r for r in ray]
        return ray

    def get_obj(self) -> float:
        return self.model.objval

    def add_cut(self, cut, name=None) -> None:
        lhs = cp.LinExpr()
        for var, coef in zip(cut.vars, cut.coefs):
            lhs.addTerm(self.model.getVarByName(var), coef)

        if cut.sense == CST.EQ:
            self.model.addConstr(lhs == cut.rhs, name=name)
        elif cut.sense == CST.LE:
            self.model.addConstr(lhs <= cut.rhs, name=name)
        elif cut.sense == CST.GE:
            self.model.addConstr(lhs >= cut.rhs, name=name)

    def remove_cut(self, cut_name: str) -> None:
        con = self.model.getConstrByName(cut_name)
        self.model.remove(con)

    def solve(self) -> None:
        # Hide solver output
        self.model.setParam(COPT.Param.Logging, 0)
        self.model.setParam(COPT.Param.LogToConsole, 0)

        # Request Farkas dual for infeasibility model
        self.model.setParam(COPT.Param.ReqFarkasRay, 1)

        self.model.solve()

        _copt_status_map = {
            COPT.OPTIMAL: CST.OPTIMAL,
            COPT.INFEASIBLE: CST.INFEASIBLE,
        }
        self.status = _copt_status_map.get(self.model.status, CST.ERROR)

    def make_master_problem(self, complicating_vars: list[str]) -> object:
        raise NotImplementedError("Automatic master problem creation is not implemented for COPT.")

    def make_sub_problem(self, complicating_vars: list[str]) -> object:
        raise NotImplementedError("Automatic subproblem creation is not implemented for COPT.")


if __name__ == '__main__':
    pass

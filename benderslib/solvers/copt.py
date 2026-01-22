# coding:utf-8

from coptpy import Model, LinExpr, COPT

from ..consts import BendersConsts as CST
from .base import SolverBase


class Copt(SolverBase):
    """COPT solver interface for BendersLib.

    This class provides an interface to the COPT solver for use with BendersLib.
    It implements the methods defined in the :class:`~benderslib.SolverBase` class.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------
    model: coptpy.Model
        An instance of COPT's ``coptpy.Model``.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: Model, solver_options: dict = None) -> None:
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
        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {
            v: (lb, ub) for v, lb, ub in zip(self._all_vars, lbs, ubs) if lb != 0 or ub != COPT.INFINITY}
        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(self.model.getConstrs())

        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self.model.objsense == COPT.MAXIMIZE:
            raise NotImplementedError("BendersLib currently only supports minimization problems.")
            # self.model.setObjective(-self.model.getObjective(), sense=COPT.MINIMIZE)

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise NotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.getVarByName(var_name)
            if lb != 0:
                self.model.addConstr(var >= lb)
                var.lb = 0
            if ub < COPT.INFINITY:
                self.model.addConstr(var <= ub)
                var.ub = COPT.INFINITY

    def __setup_model(self, solver_options: dict = None):
        # Hide solver output
        self.model.setParam(COPT.Param.Logging, 0)
        self.model.setParam(COPT.Param.LogToConsole, 0)

        # Request Farkas dual for infeasible problems
        self.model.setParam(COPT.Param.ReqFarkasRay, 1)

        # Setup solver options
        if solver_options:
            for option, value in solver_options.items():
                self.model.setParam(option, value)

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
        for var_name in vars:
            var = self.model.getVarByName(var_name)
            var.lb, var.ub = self._var_bounds.get(var_name, (0, COPT.INFINITY))

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {var_name: self.model.getVarByName(var_name).x for var_name in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        res = {}
        for v in vars:
            var = self.model.getVarByName(v)
            coefs = [self.model.getCoeff(cons, var) for cons in self.model.getConstrs()]
            res[v] = coefs
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
        # ONLY available for LP problems
        return self.model.getDuals()

    def get_extreme_ray(self) -> list[float]:
        has_nl_cons = not self.model.getAttr("Rows") == len(self.model.getConstrs())

        if has_nl_cons:
            raise Exception("Unable to obtain FarkasDual from COPT model with nonlinear constraints.")

        else:
            has_nl_obj = (
                    self.model.getAttr("HasQObj")
                    or self.model.getAttr("HasNLObj")
                    or self.model.getAttr("HasPSDObj")
            )

            if has_nl_obj:
                _m = self.model.clone()
                _m.setObjective(0, sense=COPT.MINIMIZE)
                _m.solve()
                ray = _m.getInfo(COPT.Info.DualFarkas, _m.getConstrs())
            else:
                ray = self.model.getInfo(COPT.Info.DualFarkas, self.model.getConstrs())

            # COPT returns Farkas Dual with opposite sign to Gurobi
            ray = [-r for r in ray]
            return ray

    def get_obj(self) -> float:
        return self.model.objval

    def add_cut(self, cut, name=None) -> None:
        lhs = LinExpr()
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
        self.model.solve()

        _copt_status_map = {
            COPT.OPTIMAL: CST.OPTIMAL,
            COPT.INFEASIBLE: CST.INFEASIBLE,
        }
        self.status = _copt_status_map.get(self.model.status, CST.UNKNOWN)

    @staticmethod
    def make_master_problem(original_model: Model, master_vars: list[str]) -> Model:
        master = original_model.clone()

        # Non-master variables
        non_master_vars = set(v.getName() for v in master.getVars()) - set(master_vars)

        # Remove non-master variables
        for var_name in non_master_vars:
            var = master.getVarByName(var_name)
            master.remove(var)

        # Remove constraints that contains non-master variables
        for constr in master.getConstrs():
            expr = master.getRow(constr)
            contains_non_master = False
            for i in range(expr.getSize()):
                var = expr.getVar(i)
                if var.getName() in non_master_vars:
                    contains_non_master = True
                    break
            if contains_non_master:
                master.remove(constr)

        return master

    @staticmethod
    def make_sub_problem(original_model: Model, master_vars: list[str]) -> Model:
        sub = original_model.clone()

        # Set master variables to continuous & remove them from objective
        for var_name in master_vars:
            var = sub.getVarByName(var_name)
            var.vtype = COPT.CONTINUOUS
            var.obj = 0

        # Remove constraints that contains only master variables
        for constr in sub.getConstrs():
            expr = sub.getRow(constr)
            is_master_only = True
            for i in range(expr.getSize()):
                var = expr.getVar(i)
                if var.getName() not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                sub.remove(constr)

        return sub


if __name__ == '__main__':
    pass

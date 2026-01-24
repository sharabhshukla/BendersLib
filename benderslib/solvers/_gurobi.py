# coding:utf-8

from gurobipy import Model, GRB

from ..consts import BendersConsts as CST
from ._base import SolverBase


class Gurobi(SolverBase):
    """Gurobi solver interface for BendersLib.

    This class provides an interface to the Gurobi solver for use with BendersLib.
    It implements the methods defined in the :class:`~benderslib.SolverBase` class.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------
    model: gurobipy.Model
        An instance of Gurobi's ``gurobipy.Model``.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: Model, solver_options: dict = None) -> None:
        model.update()
        super().__init__(model)

        # Attributes in Gurobi Model
        sense = self.model.ModelSense
        vars = self.model.getVars()
        vtypes = self.model.getAttr('VType', vars)
        lbs = self.model.getAttr('LB', vars)
        ubs = self.model.getAttr('UB', vars)

        # Attributes required by SolverBase
        self.status = CST.UNSOLVED
        self._solver_model = model
        self._sense = CST.MIN if sense == GRB.MINIMIZE else CST.MAX
        self._all_vars = self.model.getAttr('VarName', vars)
        self._bin_vars = [v for v, t in zip(self._all_vars, vtypes) if t == GRB.BINARY]
        self._int_vars = [v for v, t in zip(self._all_vars, vtypes) if t == GRB.INTEGER]
        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {
            v: (lb, ub) for v, lb, ub in zip(self._all_vars, lbs, ubs) if lb != 0 or ub != GRB.INFINITY}
        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(self.model.getConstrs())

        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self.model.ModelSense == GRB.MAXIMIZE:
            raise NotImplementedError("BendersLib currently only supports minimization problems.")
            # self.model.setObjective(-self.model.getObjective(), sense=GRB.MINIMIZE)

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise NotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.getVarByName(var_name)
            if lb != 0:
                self.model.addConstr(var >= lb)
                var.lb = 0
            if ub < GRB.INFINITY:
                self.model.addConstr(var <= ub)
                var.ub = GRB.INFINITY

        self.model.update()

    def __setup_model(self, solver_options: dict = None):
        # Hide solver output
        self.model.Params.OutputFlag = 0
        self.model.Params.LogToConsole = 0

        # Get Model.FarkasDual requires InfUnbdInfo = 1
        self.model.Params.InfUnbdInfo = 1

        # Gurobi model status code 4 (INF_OR_UNBD)
        self.model.Params.DualReductions = 0

        # QCPi requires QCPDual = 1
        self.model.Params.QCPDual = 1

        # Setup solver options
        if solver_options:
            for option, value in solver_options.items():
                setattr(self.model.Params, option, value)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1]
            else:
                prob = [1 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise ValueError("Length of 'prob' must match length of 'estimators'.")

        for name, obj in zip(estimators, prob):
            self.model.addVar(lb=lb, vtype=GRB.CONTINUOUS, obj=obj, name=name)

        self.model.update()

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            var = self.model.getVarByName(var_name)
            var.lb = var_value
            var.ub = var_value

    def unfix_vars(self, vars: list[str]) -> None:
        for var_name in vars:
            var = self.model.getVarByName(var_name)
            var.lb, var.ub = self._var_bounds.get(var_name, (0, GRB.INFINITY))

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars = vars or self._all_vars
        return {var_name: self.model.getVarByName(var_name).X for var_name in vars}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        # vars = vars or self._all_vars
        # _all_cons = self.model.getConstrs()
        # res = {v: [0.0] * len(_all_cons) for v in vars}
        # for i, con in enumerate(_all_cons):
        #     row = self.model.getRow(con)
        #     for j in range(row.size()):
        #         var = row.getVar(j)
        #         if var.VarName in vars:
        #             coef = row.getCoeff(j)
        #             res[var.VarName][i] = coef

        # More efficient for large model
        A_matrix = self.model.getA()
        model_vars = self.model.getVars()
        var_to_col_idx = {v.VarName: v.index for v in model_vars}
        vars_to_process = vars or self._all_vars
        res = {}
        for v_name in vars_to_process:
            col_idx = var_to_col_idx.get(v_name)
            if col_idx is not None:
                var_coeffs = A_matrix[:, col_idx]
                res[v_name] = var_coeffs.toarray().flatten().tolist()

        return res

    def get_rhs(self) -> list[float]:
        l_rhs = self.model.getAttr('RHS', self.model.getConstrs())
        q_rhs = self.model.getAttr('QCRHS', self.model.getQConstrs())
        return l_rhs + q_rhs

    def get_dual_values(self) -> list[float]:
        l_dual = self.model.getAttr('Pi', self.model.getConstrs())
        q_dual = self.model.getAttr('QCPi', self.model.getQConstrs())
        return l_dual + q_dual

    def get_extreme_ray(self) -> list[float]:
        if self.model.IsQCP:
            # FarkasDual cannot be obtained from Quadratically Constrained models
            raise Exception("Unable to obtain FarkasDual from Gurobi model with quadratic constraints.")

        elif self.model.IsQP:
            # For model with only quadratic objective and linear constraints,
            # FarkasDual can be obtained by solving a linear system with zero objective.
            _m = self.model.copy()
            _m.setObjective(0)
            _m.computeIIS()
            return _m.FarkasDual

        else:
            # For linear models, FarkasDual can be directly obtained after optimization
            return self.model.FarkasDual

    def get_obj(self) -> float:
        return self.model.ObjVal

    def add_cut(self, cut, name=None) -> None:
        lhs = sum(coef * self.model.getVarByName(var) for var, coef in zip(cut.vars, cut.coefs))

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
        self.model.optimize()

        _grb_status_map = {
            GRB.OPTIMAL: CST.OPTIMAL,
            GRB.INFEASIBLE: CST.INFEASIBLE,
        }
        self.status = _grb_status_map.get(self.model.Status, CST.UNKNOWN)

    @staticmethod
    def make_master_problem(original_model: Model, master_vars: list[str]) -> Model:
        master = original_model.copy()

        # Remove non-master variables & remove them from objective (will be handled automatically)
        non_master_vars = set(master.getAttr('VarName', master.getVars())) - set(master_vars)
        for var_name in non_master_vars:
            var = master.getVarByName(var_name)
            master.remove(var)

        # Remove constraints that contains non-master variables
        _cons_to_remove_idx = []
        constrs = master.getConstrs()

        for idx, constr in enumerate(constrs):
            row = master.getRow(constr)
            for i in range(row.size()):
                var = row.getVar(i)
                if var.VarName not in master_vars:
                    _cons_to_remove_idx.append(idx)
                    break

        # Execute removal
        for idx in reversed(_cons_to_remove_idx):
            master.remove(constrs[idx])

        master.update()
        return master

    @staticmethod
    def make_sub_problem(original_model: Model, master_vars: list[str]) -> Model:
        sub = original_model.copy()

        # Set master variables to continuous & remove them from objective
        for var_name in master_vars:
            var = sub.getVarByName(var_name)
            var.vtype = GRB.CONTINUOUS
            var.obj = 0

        # Remove constraints that contains only master variables
        _cons_to_remove_idx = []
        constrs = sub.getConstrs()

        for idx, constr in enumerate(constrs):
            row = sub.getRow(constr)
            is_master_only = True
            for i in range(row.size()):
                var = row.getVar(i)
                if var.VarName not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                _cons_to_remove_idx.append(idx)

        # Execute removal
        for idx in reversed(_cons_to_remove_idx):
            sub.remove(constrs[idx])

        sub.update()
        return sub


if __name__ == '__main__':
    pass

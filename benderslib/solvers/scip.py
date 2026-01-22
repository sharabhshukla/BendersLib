# coding:utf-8

from pyscipopt import Model, Expr, SCIP_PARAMSETTING

from ..consts import BendersConsts as CST
from .base import SolverBase


class Scip(SolverBase):
    """SCIP solver interface for BendersLib.

    This class provides an interface to the SCIP solver for use with BendersLib.
    It implements the methods defined in the :class:`~benderslib.SolverBase` class.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    Parameters
    ---------------
    model: pyscipopt.Model
        An instance of SCIP's ``pyscipopt.Model``.
    """

    SCIP_VAR_UB = 1e20
    """Default upper bound for SCIP variables."""

    def __init__(self, model: Model) -> None:
        super().__init__(model)

        # Supporting method like getVarByName and getConsByName
        _vars_dict = {v.name: v for v in self.model.getVars(transformed=False)}
        _cons_dict = {c.name: c for c in self.model.getConss(transformed=False)}

        for var in _vars_dict.values():
            print(var.getLbGlobal(), var.getUbGlobal())

        # Attributes required by SolverBase
        self.status = CST.UNSOLVED
        self._solver_model = model
        self._sense = CST.MIN if self.model.getObjectiveSense() == 'minimize' else CST.MAX
        self._all_vars = list(_vars_dict.keys())
        self._bin_vars = [var_name for var_name, var in _vars_dict.items() if var.vtype() == 'BINARY']
        self._int_vars = [var_name for var_name, var in _vars_dict.items() if var.vtype() == 'INTEGER']

        # Record only non-trivial bounds, i.e., lb != 0 or ub != +inf
        self._var_bounds = {
            var_name: (var.getLbGlobal(), var.getUbGlobal())
            for var_name, var in _vars_dict.items()
            if var.getLbGlobal() != 0 or var.getUbGlobal() < self.SCIP_VAR_UB}

        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(self.model.getConss(transformed=False))

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()
        self.__setup_model()

    def __sense_to_minimize(self):
        if self.model.getObjectiveSense() == 'maximize':
            raise NotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        # Workaround to fix wrong dual values when bound constraints are present
        # https://pyscipopt.readthedocs.io/en/latest/tutorials/constypes.html#id4
        # https://stackoverflow.com/questions/79463159/unable-to-get-dual-values-from-scip-solver

        # If there are variable bounds
        if self._var_bounds:
            raise NotImplementedError(
                "BendersLib currently does not support variable bounds in SCIP, due to a SCIP limitation.")

        # If there are bound constraints
        # for cons in self.model.getConss(transformed=False):
        #     if len(self.model.getConsVars(cons)) == 1:
        #         raise NotImplementedError(
        #             "BendersLib currently does not support bound constraints in SCIP, due to a SCIP limitation.")

        ...

    def __setup_model(self):
        # Hide output
        self.model.hideOutput()

        # Turn off presolve to get correct dual values
        self.model.setPresolve(SCIP_PARAMSETTING.OFF)
        self.model.setHeuristics(SCIP_PARAMSETTING.OFF)
        self.model.disablePropagation()

        # Get Farkas duals for infeasible problems
        self.model.setBoolParam("lp/alwaysgetduals", True)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1.0]
            else:
                prob = [1 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise ValueError("Length of 'prob' must match length of 'estimators'.")

        for name, obj in zip(estimators, prob):
            self.model.addVar(name=name, vtype='C', lb=lb, obj=obj)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        self.model.freeTransform()
        _vars_dict = {v.name: v for v in self.model.getVars(transformed=False)}
        for var_name, value in var_values.items():
            var = _vars_dict[var_name]
            self.model.chgVarLb(var, value)
            self.model.chgVarUb(var, value)
            # self.model.fixVar(var, value)

    def unfix_vars(self, vars: list[str]) -> None:
        self.model.freeTransform()
        _vars_dict = {v.name: v for v in self.model.getVars(transformed=False)}
        for var_name in vars:
            var = _vars_dict[var_name]
            lb, ub = self._var_bounds.get(var_name, (0, self.SCIP_VAR_UB))
            self.model.chgVarLb(var, lb)
            self.model.chgVarUb(var, ub)

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        all_var_values = self.model.getVarDict()
        if vars is not None:
            return {var_name: all_var_values[var_name] for var_name in vars}
        return all_var_values

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        result = {vars: [] for vars in (vars or self._all_vars)}

        _cons_dict = {c.name: c for c in self.model.getConss(transformed=False)}
        for cons in _cons_dict.values():
            var_coefs = self.model.getValsLinear(cons)
            for var_name in result.keys():
                coef = var_coefs.get(var_name, 0.0)
                result[var_name].append(coef)

        return result

    def get_rhs(self) -> list[float]:
        cons = self.model.getConss(transformed=False)
        lhs = [self.model.getLhs(c) for c in cons]
        rhs = [self.model.getRhs(c) for c in cons]

        res = []
        self._sense = []
        for l, r in zip(lhs, rhs):
            if l <= -self.SCIP_VAR_UB:
                res.append(r)
                self._sense.append('<=')
            elif r >= self.SCIP_VAR_UB:
                res.append(l)
                self._sense.append('>=')

        return res

    def get_dual_values(self) -> list[float]:
        cons = self.model.getConss(transformed=False)
        duals = [self.model.getDualSolVal(c) for c in cons]
        return duals

    def get_extreme_ray(self) -> list[float]:
        cons = self.model.getConss(transformed=False)
        ray = [self.model.getDualfarkasLinear(c) for c in cons]

        # SCIP returns Farkas Dual with opposite sign to Gurobi
        ray = [-r for r in ray]
        return ray

    def get_obj(self) -> float:
        return self.model.getObjVal()

    def add_cut(self, cut, name=None) -> None:
        _vars_dict = {v.name: v for v in self.model.getVars(transformed=False)}
        lhs = sum(coef * _vars_dict[var] for var, coef in zip(cut.vars, cut.coefs))

        # Cut cannot be added in the "problem solved stage"
        self.model.freeTransform()

        if cut.sense == CST.EQ:
            self.model.addCons(lhs == cut.rhs, name=name)
        elif cut.sense == CST.LE:
            self.model.addCons(lhs <= cut.rhs, name=name)
        elif cut.sense == CST.GE:
            self.model.addCons(lhs >= cut.rhs, name=name)

    def remove_cut(self, cut_name: str) -> None:
        raise NotImplementedError("Removing cuts is not supported by the SCIP interface yet.")

    def solve(self) -> None:
        # self.model.freeTransform()
        self.model.optimize()

        _scip_status_map = {
            'optimal': CST.OPTIMAL,
            'infeasible': CST.INFEASIBLE,
        }
        self.status = _scip_status_map.get(self.model.getStatus(), CST.ERROR)

    @staticmethod
    def make_master_problem(original_model: Model, master_vars: list[str]) -> Model:
        master = Model(sourceModel=original_model)

        non_master_vars = [v.name for v in master.getVars(transformed=False) if v.name not in master_vars]

        # Remove non-master variables & remove them from objective (will be handled automatically)
        vars = master.getVars(transformed=False)
        _vars_to_del_idx = []
        for i, var in enumerate(vars):
            if var.name not in master_vars:
                _vars_to_del_idx.append(i)

        # Remove constraints that contains non-master variables
        conss = master.getConss(transformed=False)
        _conss_to_del_idx = []
        for i, cons in enumerate(conss):
            contains_non_master = False
            for var in master.getConsVars(cons):
                if var.name in non_master_vars:
                    contains_non_master = True
                    break
            if contains_non_master:
                _conss_to_del_idx.append(i)

        # Execute deletions in reverse order to avoid index shifting
        for i in reversed(_vars_to_del_idx):
            master.delVar(vars[i])
        for i in reversed(_conss_to_del_idx):
            master.delCons(conss[i])

        return master

    @staticmethod
    def make_sub_problem(original_model: Model, master_vars: list[str]) -> Model:
        sub = Model(sourceModel=original_model)

        # Set master variables to continuous & remove them from objective
        obj = sub.getObjective()
        new_obj = Expr()
        for var in sub.getVars(transformed=False):
            if var.name in master_vars:
                sub.chgVarType(var, 'C')
            else:
                new_obj += obj[var] * var
        sub.setObjective(new_obj, 'minimize')

        # Remove constraints that contains only master variables
        conss = sub.getConss(transformed=False)
        _cons_to_del_idx = []
        for i, cons in enumerate(conss):
            is_master_only = True
            for var in sub.getConsVars(cons):
                if var.name not in master_vars:
                    is_master_only = False
                    break
            if is_master_only:
                _cons_to_del_idx.append(i)

        # Execute deletions in reverse order to avoid index shifting
        for i in reversed(_cons_to_del_idx):
            sub.delCons(conss[i])

        return sub


if __name__ == '__main__':
    pass

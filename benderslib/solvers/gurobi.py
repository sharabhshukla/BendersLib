# coding:utf-8

from ..consts import BendersConsts as CST
from .base import SolverBase

from gurobipy import Model, GRB, LinExpr


class Gurobi(SolverBase):
    """Gurobi solver interface for BendersLib.

    This class provides an interface to the Gurobi solver for use with BendersLib.
    It implements the abstract methods defined in the :class:`SolverBase` class.
    Two additional methods, :func:`make_master_problem` and :func:`make_sub_problem`,
    are provided for automatic decomposition by :class:`AnnotationBenders`.

    Parameters
    ---------------
    model: gurobipy.Model
        An instance of Gurobi's ``gurobipy.Model``.
    """

    def __init__(self, model: Model) -> None:
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
        self._var_bounds = {v: (lb, ub) for v, lb, ub in zip(self._all_vars, lbs, ubs) if lb != 0 or ub != GRB.INFINITY}
        self.__standardize()
        self._rhs = self.get_rhs()

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()
        self.model.update()

    def __sense_to_minimize(self):
        # BendersLib will automatically convert maximization problems to minimization problems
        if self.model.ModelSense == GRB.MAXIMIZE:
            self.model.setObjective(-self.model.getObjective(), sense=GRB.MINIMIZE)

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise ValueError("Gurobi interface currently only supports non-negative variable bounds.")

        # BendersLib will automatically convert variable bounds to explicit constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self.model.getVarByName(var_name)
            if lb != 0:
                self.model.addConstr(var >= lb)
                var.lb = 0
            if ub < GRB.INFINITY:
                self.model.addConstr(var <= ub)
                var.ub = GRB.INFINITY

    def add_vars(self, var_names: list[str], var_types: list[str], lb: list[float], ub: list[float]) -> list[str]:
        _var_type_map = {
            CST.BINARY: GRB.BINARY,
            CST.INTEGER: GRB.INTEGER,
            CST.CONTINUOUS: GRB.CONTINUOUS
        }

        for var_name, var_type, lower, upper in zip(var_names, var_types, lb, ub):
            grb_var_type = _var_type_map.get(var_type, GRB.CONTINUOUS)
            self.model.addVar(lb=lower, ub=upper, vtype=grb_var_type, name=var_name)

            if var_type == CST.BINARY:
                self._bin_vars.append(var_name)
            elif var_type == CST.INTEGER:
                self._int_vars.append(var_name)
            self._all_vars.append(var_name)
            self._var_bounds[var_name] = (lower, upper)

        self.model.update()
        return var_names

    def get_obj_expr(self) -> dict[str, float]:
        expr = self.model.getObjective()
        res = {expr.getVar(i).VarName: expr.getCoeff(i) for i in range(expr.size())}
        return res

    def set_obj(self, var_coefs: dict[str, float]) -> None:
        coefs = list(var_coefs.values())
        vars = [self.model.getVarByName(var) for var in var_coefs.keys()]
        obj_expr = LinExpr(coefs, vars)
        self.model.setObjective(obj_expr, sense=GRB.MINIMIZE if self._sense == CST.MIN else GRB.MAXIMIZE)
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
        return self.model.getAttr('RHS', self.model.getConstrs())

    def get_dual_values(self) -> list[float]:
        return self.model.getAttr('Pi', self.model.getConstrs())

    def get_extreme_ray(self) -> list[float]:
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
        # Hide solver output
        self.model.Params.OutputFlag = 0
        self.model.Params.LogToConsole = 0

        # Get Model.FarkasDual requires InfUnbdInfo = 1
        self.model.Params.InfUnbdInfo = 1

        self.model.optimize()

        _grb_status_map = {
            GRB.OPTIMAL: CST.OPTIMAL,
            GRB.INFEASIBLE: CST.INFEASIBLE,
        }
        self.status = _grb_status_map.get(self.model.Status, CST.ERROR)

    @staticmethod
    def is_available() -> bool:
        """Check if Gurobi is available in the current environment.

        Returns
        ---------------
        bool
            True if Gurobi is available, False otherwise.

        Example
        ---------------
        .. code-block:: python

            if Gurobi.is_available():
                print("Gurobi solver is available.")
            else:
                print("Gurobi solver is not available.")
        """
        try:
            import gurobipy  # noqa: F401
            return True
        except ImportError:
            return False

    def make_master_problem(self, master_vars: list[str]) -> Model:
        """Build the master problem from the original problem.
        
        This function generates the master problem from the original problem by extracting 
        the specified master problem variables,
        constraints that only involve these variables, objective terms associated with these variables.

        .. Note::
           This method is required for :class:`AnnotationBenders`, which automatically decomposes the original problem
           into master and subproblems based on the provided complicating variables.
           This suggests that you do not need to implement this method when manually defining master and subproblems.

        Parameters
        ---------------
        master_vars : list[str]
            Complicating variables that only appear in the master problem.

        Returns
        ---------------
        ``gurobipy.Model``
            A Gurobi Model object representing the master problem.

        Example
        ---------------
        .. code-block:: python

            original_problem = Model()
            Model.addVar(...)
            Model.addConstr(...)
            Model.setObjective(...)

            master_vars = ['x1', 'x2']
            Solver = Gurobi(original_problem)
            master_problem = Solver.make_master_problem(master_vars)
        """
        vars_dict = {var: self.model.getVarByName(var) for var in master_vars}
        cons_dict = {con.ConstrName: con for con in self.model.getConstrs()}

        master = Model()
        # Copy variables to master model
        for v in vars_dict.values():
            master.addVar(lb=v.lb, ub=v.ub, obj=v.obj, vtype=v.vtype, name=v.VarName, column=None)
        master.update()
        master_vars_dict = {var.VarName: var for var in master.getVars()}

        # Copy constraints to master model
        for c in cons_dict.values():
            expr = self.model.getRow(c)
            var_set = {expr.getVar(i).VarName for i in range(expr.size())}
            if var_set.issubset(set(master_vars)):
                # Only involve constraints with master variables
                var_list = [master_vars_dict[expr.getVar(i).VarName] for i in range(expr.size())]
                coefficient_list = [expr.getCoeff(i) for i in range(expr.size())]
                new_expr = LinExpr(coefficient_list, var_list)
                master.addLConstr(new_expr, c.Sense, c.RHS, name=c.ConstrName)

        # Copy objective to master model
        obj_expr = LinExpr(
            [v.Obj for v in master_vars_dict.values()],
            [v for v in master_vars_dict.values()]
        )
        master.setObjective(obj_expr)

        master.update()
        return master

    def make_sub_problem(self, master_vars: list[str]) -> Model:
        """Build the subproblem from the original problem.
        
        This function generates the subproblem from the original problem by extracting all variables from the original problem
        (master problem variables are treated as continuous and their ``lb`` and ``ub`` are fixed based on the
        master problem solution), constraints excepting those that only involve master problem variables,
        and the objective terms associated with the non-master problem variables.

        .. Note::
           This method is required for :class:`AnnotationBenders`, which automatically decomposes the original problem
           into master and subproblems based on the provided complicating variables.
           This suggests that you do not need to implement this method when manually defining master and subproblems.

        Parameters
        ---------------
        master_vars : list[str]
            Complicating variables that only appear in the master problem.

        Returns
        ---------------
        ``gurobipy.Model``
            A Gurobi Model object representing the subproblem.

        Example
        ---------------
        .. code-block:: python

            original_problem = Model()
            Model.addVar(...)
            Model.addConstr(...)
            Model.setObjective(...)

            master_vars = ['x1', 'x2']
            Solver = Gurobi(original_problem)
            sub_problem = Solver.make_sub_problem(master_vars)
        """
        cons_dict = {con.ConstrName: con for con in self.model.getConstrs()}

        sub = Model()
        # Copy variables to sub model
        for v in self.model.getVars():
            vtype = GRB.CONTINUOUS if v.VarName in master_vars else v.vtype
            sub.addVar(lb=v.lb, ub=v.ub, obj=v.obj, vtype=vtype, name=v.VarName, column=None)
        sub.update()
        sub_vars_dict = {var.VarName: var for var in sub.getVars()}

        # Copy constraints to sub model
        for c in cons_dict.values():
            expr = self.model.getRow(c)
            var_set = {expr.getVar(i).VarName for i in range(expr.size())}
            if not var_set.issubset(set(master_vars)):
                # Ignoring constraints with only master variables
                var_list = [sub_vars_dict[expr.getVar(i).VarName] for i in range(expr.size())]
                coefficient_list = [expr.getCoeff(i) for i in range(expr.size())]
                new_expr = LinExpr(coefficient_list, var_list)
                sub.addLConstr(new_expr, c.Sense, c.RHS, name=c.ConstrName)

        # Copy objective to sub model
        obj_expr = LinExpr(
            [v.Obj for v in sub_vars_dict.values() if v.VarName not in master_vars],
            [v for v in sub_vars_dict.values() if v.VarName not in master_vars]
        )
        sub.setObjective(obj_expr)

        sub.update()
        return sub


if __name__ == '__main__':
    pass

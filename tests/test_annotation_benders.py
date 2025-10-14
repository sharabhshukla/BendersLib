# coding:utf-8

import pytest
from gurobipy import Model, GRB
from benderslib import AnnotationBenders, ClassicalBenders, Gurobi


class TestAnnotationBenders:

    def make_original_problem(self):
        model = Model("Original")

        n_vars = 20
        y = model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
        z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

        model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr")
        model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
        model.addConstrs((2 * y[i] + z[i] >= i for i in range(n_vars)), name="constr_yz")
        model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_zx")

        model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

        model.Params.OutputFlag = 0
        model.Params.LogToConsole = 0

        model.update()
        complicating_vars = [v.VarName for v in y.values()]
        return model, complicating_vars

    def test_annotation_benders(self):
        model, complicating_vars = self.make_original_problem()

        # Solve with Benders Decomposition
        ab = AnnotationBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)
        ab.solve()

        model.optimize()
        obj = model.ObjVal if model.Status == GRB.OPTIMAL else None
        assert ab.result.status == 'OPTIMAL'
        assert ab.result.obj == pytest.approx(obj)


if __name__ == "__main__":
    pytest.main([__file__])

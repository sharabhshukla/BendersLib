# coding:utf-8

import pytest
from benderslib import AnnotationBenders, CombinatorialBenders
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB


class TestCombinatorialBenders:

    def make_original_problem(self, has_sub_objective):
        model = Model()

        n_vars = 8
        # Master problem variables (complicating variables)
        x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
        # Subproblem variables
        y = model.addVars(n_vars, name="y", vtype=GRB.BINARY)
        z = model.addVars(n_vars, name="z", lb=0, vtype=GRB.CONTINUOUS)

        # Master problem constraint
        model.addConstr(x.sum() <= 5, "master_constr")
        # Linking constraints
        model.addConstrs((z[i] <= 10 * x[i] for i in range(n_vars)), name="linking_constr")
        # Subproblem constraints
        model.addConstr(y.sum() <= 8, "sub_constr_1")
        model.addConstr(z.sum() >= 15, "sub_constr_2")
        model.addConstrs((z[i] >= 2 * y[i] for i in range(n_vars)), name="sub_constr_3")

        # Objective function
        if has_sub_objective:
            # When the subproblem has its own objective, optimality cuts are generated.
            model.setObjective(x.sum() + y.sum() + z.sum(), sense=GRB.MINIMIZE)
        else:
            # When the subproblem has no objective, only feasibility cuts are generated.
            model.setObjective(x.sum(), sense=GRB.MINIMIZE)

        model.Params.OutputFlag = 0
        model.Params.LogToConsole = 0

        model.update()
        complicating_vars = [v.VarName for v in x.values()]
        return model, complicating_vars

    def test_combinatorial_benders_with_objective(self):
        model, complicating_vars = self.make_original_problem(has_sub_objective=True)

        # Solve with Gurobi
        model.optimize()
        obj = None
        if model.Status == GRB.OPTIMAL:
            obj = model.ObjVal

        # Solve with Benders Decomposition
        AB = AnnotationBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=CombinatorialBenders)
        AB.solve()

        assert AB.result.status == 'OPTIMAL'
        assert obj == pytest.approx(AB.result.obj)

    def test_combinatorial_benders_without_objective(self):
        model, complicating_vars = self.make_original_problem(has_sub_objective=False)

        # Solve with Gurobi
        model.optimize()
        obj = None
        if model.Status == GRB.OPTIMAL:
            obj = model.ObjVal

        # Solve with Benders Decomposition
        AB = AnnotationBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=CombinatorialBenders)
        AB.solve()

        assert AB.result.status == 'OPTIMAL'
        assert obj == pytest.approx(AB.result.obj)


if __name__ == "__main__":
    pytest.main([__file__])

# coding:utf-8

import pytest
from benderslib import BendersParams, MasterProblem, SubProblem, ClassicalBenders
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB


class TestClassicalBenders:

    def make_original_problem(self):
        model = Model("Original")

        x = model.addVar(name="x", vtype=GRB.INTEGER)
        y = model.addVar(name="y")
        z = model.addVar(name="z")

        model.setObjective(x + 2 * y)
        model.addConstr(x + y + z == 14)
        model.addConstr(x - y == 2)

        model.Params.OutputFlag = 0
        model.Params.LogToConsole = 0
        return model

    def make_master_problem(self):
        model = Model("Master")

        x = model.addVar(name="x", vtype=GRB.INTEGER)
        z = model.addVar(name="z")

        model.setObjective(x)

        model.update()
        return model, [x.VarName, z.VarName]

    def make_sub_problem(self):
        model = Model("Sub")

        master_x = model.addVar(name="x")
        y = model.addVar(name="y")
        master_z = model.addVar(name="z")

        model.setObjective(2 * y)
        model.addConstr(master_x + y + master_z == 14)
        model.addConstr(master_x - y == 2)

        model.update()
        return model

    def test_classical_benders(self):
        # Define master problem
        model, complicating_vars = self.make_master_problem()
        master_problem = MasterProblem(solver_backend=Gurobi(model))
        # Define subproblem
        model = self.make_sub_problem()
        sub_problem = SubProblem(solver_backend=Gurobi(model))
        # Create and solve Benders Decomposition instance
        BD = ClassicalBenders(master_problem, sub_problem, complicating_vars=complicating_vars)
        BD.solve()

        # Check results
        m = self.make_original_problem()
        m.optimize()
        obj = m.ObjVal if m.Status == GRB.OPTIMAL else None
        assert BD.result.status == 'OPTIMAL'
        assert obj == pytest.approx(BD.result.obj)


if __name__ == "__main__":
    pytest.main([__file__])

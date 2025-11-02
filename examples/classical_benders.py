# coding:utf-8

"""
Classical Benders Decomposition
==================================

"""

# %%
# This example explicitly defines master problem and subproblem for Benders decomposition.
#
# Define a simple MILP problem:
from benderslib import BendersParams, MasterProblem, SubProblem, Gurobi, ClassicalBenders

from gurobipy import Model, GRB


def make_original_problem():
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


# %%
# Define master problem and subproblem for Benders decomposition:
def make_master_problem():
    model = Model("Master")

    x = model.addVar(name="x", vtype=GRB.INTEGER)
    z = model.addVar(name="z")
    theta = model.addVar(name="theta", lb=BendersParams.theta_lb)

    model.setObjective(x + theta)

    model.update()
    return model, [x.VarName, z.VarName]


def make_sub_problem():
    model = Model("Sub")

    master_x = model.addVar(name="x")
    y = model.addVar(name="y")
    master_z = model.addVar(name="z")

    model.setObjective(2 * y)
    model.addConstr(master_x + y + master_z == 14)
    model.addConstr(master_x - y == 2)

    model.update()
    return model


# %%
# Solving using Gurobi and Benders Decomposition:
if __name__ == '__main__':
    # Solve original problem using Gurobi
    model = make_original_problem()
    model.optimize()
    if model.Status == GRB.OPTIMAL:
        print("Original Problem Solution:")
        print({v.VarName: v.X for v in model.getVars()})
        print(f"Obj: {model.ObjVal}\n")
    else:
        print("Original Problem Solution: Infeasible or Unbounded\n")

    # Solving using Benders Decomposition:

    # Define master problem
    master_model, complicating_vars = make_master_problem()
    # master_problem = MasterProblem(solver_backend=Gurobi(master_model))

    # Define subproblem
    sub_model = make_sub_problem()
    # sub_problem = SubProblem(solver_backend=Gurobi(sub_model))

    # Create and solve Benders Decomposition instance
    BD = ClassicalBenders.from_models(master_model, Gurobi, sub_model, Gurobi, complicating_vars=complicating_vars)
    # BD = ClassicalBenders(master_problem, sub_problem, complicating_vars=complicating_vars)

    BD.solve()
    print("\nBenders Decomposition Solution:")
    print(BD.result.solution)
    print(f"Obj: {BD.result.obj}\n")

# %%
#
# .. admonition:: References
#
#     * Tutorial of Classical Benders Decomposition: :doc:`../tutorials/classical`
#     * This example uses the following class: :ref:`api-classical`
#
# .. seealso::
#
#     * Automated decomposition based complicating variables: :doc:`annotation_benders`

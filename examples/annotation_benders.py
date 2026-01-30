# coding:utf-8

"""
Annotation Benders Decomposition
=======================================

"""

# %%
# This example automatically decomposes a mixed-integer programming problem into a master problem
# and a subproblem based on the specified complicating variables, and then solves it using
# the classical Benders decomposition method.
#
# Define the original problem:
from benderslib import AnnotationBenders, ClassicalBenders
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB
import matplotlib.pyplot as plt


def make_original_problem():
    model = Model("Original")

    n_vars = 20
    # BendersLib will automatically convert variable bounds (lb and ub) to explicit constraints.
    # However, your original model will not be changed. So, you can still access the original variable bounds.
    y = model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

    model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr_yz")
    model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
    model.addConstrs((2 * y[i] + z[i] >= i for i in range(n_vars)), name="constr_yz")
    model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_z")

    model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Solve the problem using Gurobi and Annotation Benders Decomposition:
if __name__ == '__main__':
    # Solve original problem for comparison
    model, complicating_vars = make_original_problem()
    model.optimize()
    if model.Status == GRB.OPTIMAL:
        print("Original Problem Solution:")
        # var_values = {v.VarName: v.X for v in model.getVars()}
        # print(var_values)
        print(f"Obj: {model.ObjVal}\n")
    else:
        print("Original Problem Solution: Infeasible or Unbounded\n")

    # Solve with Benders Decomposition
    AB = AnnotationBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)
    AB.solve()

    # # Another way: Manually decompose the model and create ClassicalBenders instance
    # master_model, sub_model = AnnotationBenders.decompose(model, Gurobi, complicating_vars, solver_model=True)
    # AB = ClassicalBenders.from_models(master_model, Gurobi, sub_model, Gurobi, complicating_vars=complicating_vars)
    # AB.solve()

    print("\nBenders Decomposition Solution:")
    # print(AB.result.solution)
    print(f"Obj: {AB.result.obj}")

    # Draw convergence curve
    plt.plot(AB.result.lb_list, label='Lower Bound')
    plt.plot(AB.result.ub_list, label='Upper Bound')
    plt.xlabel('Iteration')
    plt.ylabel('Objective Value')
    plt.title('Benders Decomposition')
    plt.legend()
    plt.grid(True)
    plt.show()

# %%
#
# .. admonition:: References
#
#     This example uses the following classes: :class:`~benderslib.AnnotationBenders`, :class:`~benderslib.ClassicalBenders`

# coding:utf-8

"""
L-shaped Method with Convex Recourse
============================================

This example solves a Two-stage Stochastic Programming problem with **convex**
second-stage problems using the L-shaped method.
This method is an extension of the L-shaped method for cases where the recourse
problem is a convex program (e.g., a Quadratic Programming problem).
"""

# %%
# Define the first-stage problem:

import random

from benderslib import MasterProblem, SubProblems, GeneLShaped, CST
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB, QuadExpr, quicksum
from matplotlib import pyplot as plt


def first_stage_model(n_plants):
    model = Model("FirstStage")

    capacity = model.addVars(n_plants, name="capacity")
    model.setObjective(capacity.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [capacity[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Define the second-stage problem with a convex objective:
def second_stage_model(n_plants, scenarios):
    """Defines the second-stage (sub) problems for each scenario."""
    for s, demand in enumerate(scenarios):
        model = Model(f"SecondStage_{s}")

        # Complicating variables must have the same names as in the first-stage model
        capacity = model.addVars(n_plants, name="capacity")
        shortage = model.addVars(n_plants, lb=0, name="shortage")

        # Constraints
        model.addConstrs((shortage[i] >= demand[i] - capacity[i] for i in range(n_plants)), name="shortage_constr")

        # Set a convex (quadratic) objective
        model.setObjective(quicksum(shortage[i] * shortage[i] for i in range(n_plants)))

        yield model


# %%
# Define the deterministic equivalent problem for verification:
def deterministic_equivalent_model(n_plants, scenarios, probs):
    model = Model('DE')

    capacity = model.addVars(n_plants, name="capacity")
    shortage = model.addVars(len(scenarios), n_plants, lb=0, name="shortage")

    # Objective: first-stage cost + expected second-stage cost (including quadratic term)
    second_stage_cost = QuadExpr()
    for s, data in enumerate(scenarios):
        for i in range(n_plants):
            second_stage_cost.add(probs[s] * shortage[s, i] * shortage[s, i])

    model.setObjective(capacity.sum() + second_stage_cost, GRB.MINIMIZE)

    # Constraints
    for s, demand in enumerate(scenarios):
        model.addConstrs(
            (shortage[s, i] >= demand[i] - capacity[i] for i in range(n_plants)),
            name=f"shortage_constr_s{s}"
        )

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    return model


# %%
# Solve the problem using the deterministic equivalent (for clarity and verification) and the L-shaped method:
if __name__ == '__main__':
    # Data
    random.seed(5)
    n_plants = 5
    n_scenarios = 10
    scenarios = [[random.randint(10, 220) for _ in range(n_plants)] for _ in range(n_scenarios)]
    probs = [1 / n_scenarios for _ in range(n_scenarios)]

    # --- Solve with Generalized L-shaped Method ---
    # Initialize Master and Subproblems
    fs_model, complicating_vars = first_stage_model(n_plants)
    ss_models = list(second_stage_model(n_plants, scenarios))

    master_problem = MasterProblem(Gurobi(fs_model))
    sub_problems = SubProblems([Gurobi(m) for m in ss_models], prob=probs)

    # Initialize and run the Benders solver
    BD = GeneLShaped(master_problem, sub_problems, complicating_vars)
    BD.solve()

    # Multi-cut version
    # Master and Sub models are required to be re-defined,
    # since they have been modified (by adding cuts) in the previous solve.
    fs_model, complicating_vars = first_stage_model(n_plants)
    ss_models = list(second_stage_model(n_plants, scenarios))
    master_problem = MasterProblem(Gurobi(fs_model))
    sub_problems = SubProblems([Gurobi(m) for m in ss_models], prob=probs)
    BD_multi = GeneLShaped(master_problem, sub_problems, complicating_vars)
    BD_multi.params.multi_opti_cut = True
    BD_multi.solve()

    # Plot convergence
    plt.plot(BD.result.lb_list, label='Lower Bound')
    plt.plot(BD.result.ub_list, label='Upper Bound')
    plt.xlabel('Iteration')
    plt.ylabel('Objective Value')
    plt.title('Benders Decomposition')
    plt.legend()
    plt.grid(True)
    plt.show()

    # --- Solve with Deterministic Equivalent ---
    de_model = deterministic_equivalent_model(n_plants, scenarios, probs)
    de_model.optimize()
    if de_model.Status == GRB.OPTIMAL:
        print(f"DE Obj: {de_model.ObjVal}")
    else:
        print("Deterministic Equivalent Problem is infeasible or unbounded.")

    if BD.result.status == CST.OPTIMAL:
        print(f"BD Obj: {BD.result.obj}")
    else:
        print("Benders Decomposition did not find an optimal solution.")

# %%
#
# .. admonition:: References
#
#     * Tutorial of the L-shaped method: :doc:`../tutorials/lshape`
#     * Tutorial of the Generalized Benders Decomposition: :doc:`../tutorials/gbd`
#     * This example uses the following class: :class:`~benderslib.benders.GeneLShaped`

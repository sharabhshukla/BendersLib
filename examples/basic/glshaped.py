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
# Define the first-stage problem.

import random

from benderslib import MasterProblem, SubProblems, GeneLShaped, CST, BendersParams
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from gurobipy import Model, GRB, QuadExpr, quicksum


def first_stage_model(n_plants):
    model = Model("FirstStage")

    capacity = model.addVars(n_plants, vtype=GRB.INTEGER, name="capacity")
    model.setObjective(capacity.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [capacity[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Define the second-stage problem with a convex objective.

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
# Define the deterministic equivalent problem for verification.

def deterministic_equivalent_model(n_plants, scenarios, probs):
    model = Model('DE')

    capacity = model.addVars(n_plants, vtype=GRB.INTEGER, name="capacity")
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
# Solve the problem using the single-cut Generalized L-shaped method.

# Data
random.seed(1)
n_plants = 5
n_scenarios = 10
scenarios = [[random.randint(10, 220) for _ in range(n_plants)] for _ in range(n_scenarios)]
probs = [1 / n_scenarios for _ in range(n_scenarios)]

# Master and subproblems
fs_model, complicating_vars = first_stage_model(n_plants)
ss_models = list(second_stage_model(n_plants, scenarios))

master_problem = MasterProblem(Gurobi(fs_model))
sub_problems = SubProblems([Gurobi(m) for m in ss_models], prob=probs)

BD = GeneLShaped(master_problem, sub_problems, complicating_vars)

# This example works well with the branch-and-check method, try it!
# BD.params.use_bnc = True

BD.solve()

draw_curve(BD.result)

# %%
# Solve the problem using the multi-cut Generalized L-shaped method.

# Multi-cut version
# Master and Sub models are required to be re-defined,
# since they have been modified (by adding cuts) in the previous solve.
fs_model, complicating_vars = first_stage_model(n_plants)
ss_models = list(second_stage_model(n_plants, scenarios))
BD = GeneLShaped.from_models(
    master_model=fs_model,
    master_solver=Gurobi,
    sub_model=ss_models,
    sub_solver=Gurobi,
    complicating_vars=complicating_vars,
    prob=probs,
    params=BendersParams(multi_opti_cut=True)
)

# This example works well with the branch-and-check method, try it!
# BD.params.use_bnc = True

BD.solve()

draw_curve(BD.result)

# %%
# Solve the deterministic equivalent problem for verification.

de_model = deterministic_equivalent_model(n_plants, scenarios, probs)
de_model.optimize()

print(f"Deterministic Equivalent Obj: {de_model.ObjVal:.4f}")
print(f"Benders Decomposition    Obj: {BD.result.obj:.4f}")

# %%
#
# .. seealso::
#
#     * Tutorial of the L-shaped method: :doc:`../../tutorials/lshaped`
#     * Tutorial of the Generalized Benders Decomposition: :doc:`../../tutorials/gbd`
#     * This example uses the following class: :class:`~benderslib.benders.GeneLShaped`
#
# .. tags:: benders: generalized, benders: l-shaped, solver: gurobi, stochastic, branch-and-check

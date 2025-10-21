# coding:utf-8

"""
L-shaped Method
============================================

This example solves a Two-stage Stochastic Programming problem using the L-shaped method.
The L-shaped method requires the second-stage problem to be a Linear Program.
"""

# %%
# Define the first-stage problem:

import random

from benderslib import MasterProblem, SubProblem, SubProblems, Gurobi, LShaped
from gurobipy import Model, GRB


# random.seed(1)


def first_stage_model(n_plants, n_scenarios, multi_cut=False):
    model = Model("FirstStage")

    capacity = model.addVars(n_plants, name="capacity")

    # Estimator for the second-stage cost
    if multi_cut:
        theta = model.addVars(n_scenarios, name="theta")
        model.setObjective(capacity.sum() + theta.sum(), GRB.MINIMIZE)
    else:
        theta = model.addVar(name='theta')
        model.setObjective(capacity.sum() + theta, GRB.MINIMIZE)

    # model.addConstr(capacity.sum() <= 10, name="total_capacity_constr")

    model.update()
    complicating_vars = [capacity[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Define the second-stage problem:
def second_stage_model(n_plants, scenarios):
    for s, data in enumerate(scenarios):
        demand = data["demand"]

        model = Model(f"SecondStage_{s}")

        # Complicating variables should have the **SAME names** as in the first-stage model
        capacity = model.addVars(n_plants, name="capacity")
        shortage = model.addVars(n_plants, lb=0, name="shortage")

        # Minimize shortage
        model.addConstrs((shortage[i] >= demand[i] - capacity[i] for i in range(n_plants)), name="shortage_constr")
        ROI = 1  # return on investment
        model.setObjective(ROI * shortage.sum(), GRB.MINIMIZE)

        model.addConstr(capacity.sum() >= 40, name="min_total_capacity_constr")

        yield model


# %%
# Define the deterministic equivalent problem for verification:
def deterministic_equivalent_model(n_plants, scenarios):
    model = Model('DE')

    capacity = model.addVars(n_plants, name="capacity")
    shortage = model.addVars(len(scenarios), n_plants, lb=0, name="shortage")

    # Objective
    model.setObjective(
        capacity.sum() +
        sum(data["prob"] * sum(shortage[s, i] for i in range(n_plants)) for s, data in enumerate(scenarios)),
        GRB.MINIMIZE)

    # Constraints
    for s, data in enumerate(scenarios):
        demand = data["demand"]
        model.addConstrs(
            (shortage[s, i] >= demand[i] - capacity[i] for i in range(n_plants)),
            name=f"shortage_constr_s{s}"
        )

    model.addConstr(capacity.sum() >= 40, name="min_total_capacity_constr")

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    return model


# %%
# Solve the problem using the deterministic equivalent (for clarity and verification):
if __name__ == '__main__':
    # Data
    n_plants = 5
    n_scenarios = 10
    scenarios = [
        {"demand": [random.randint(10, 20) for _ in range(n_plants)],
         "prob": 1.0 / n_scenarios}
        for _ in range(n_scenarios)]

    # Deterministic equivalent solution
    de_model = deterministic_equivalent_model(n_plants, scenarios)
    de_model.optimize()
    if de_model.Status == GRB.OPTIMAL:
        print(f"Deterministic Equivalent Obj: {de_model.ObjVal:.4f}\n")
    else:
        print("Deterministic Equivalent Problem is infeasible or unbounded.\n")

    # Master problem
    multi_cut = False
    master_model, complicating_vars = first_stage_model(n_plants, n_scenarios, multi_cut=multi_cut)
    MasterProblem = MasterProblem(solver_backend=Gurobi(master_model))

    # Subproblems
    sub_models = second_stage_model(n_plants, scenarios)
    sub_problems = (SubProblem(solver_backend=Gurobi(sub_model)) for sub_model in sub_models)
    SubProblems = SubProblems(sub_problems, prob=[data["prob"] for data in scenarios])

    # L-shaped method
    L = LShaped(
        master_problem=MasterProblem,
        sub_problems=SubProblems,
        complicating_vars=complicating_vars,
        multi_cut=multi_cut,
        parallel_sub=False,
        batch_size=n_scenarios
    )
    L.solve()

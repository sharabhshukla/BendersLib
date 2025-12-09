# coding:utf-8

"""
Integer L-shaped Method (IIS)
============================================

This example solves an integer Two-stage Stochastic Programming problem using the integer L-shaped method.
The integer L-shaped method is suitable for problems where the second-stage problem contains integer variables.
However, the complicating variables must be pure binary.
This example using the Irreducible Infeasible Subsystem (IIS) to generate stronger feasibility cuts.
"""

# %%
# Define the first-stage problem:

import random

from benderslib import Gurobi, IntegerLShaped, NoGoodFC, CST, SubProblems, MasterProblem
from gurobipy import Model, GRB
import matplotlib.pyplot as plt


# random.seed(1)

def first_stage_model(n_plants):
    model = Model("FirstStage")

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
    model.setObjective(open.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [open[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Define the second-stage problem:
def second_stage_model(n_plants, scenarios):
    models = []

    for s, demand in enumerate(scenarios):
        model = Model(f"SecondStage_{s}")

        # Complicating variables should have the **SAME names** as in the first-stage model
        open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")

        # Demand satisfaction constraints
        model.addConstrs((demand[i] <= open[i] for i in range(n_plants)), name="demand_satisfaction")

        models.append(model)

    return models


# %%
# Define the deterministic equivalent problem for verification:
def deterministic_equivalent_model(n_plants, scenarios):
    model = Model('DE')

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")

    # Objective
    model.setObjective(open.sum())

    # Constraints
    for s, demand in enumerate(scenarios):
        # Demand satisfaction constraints
        model.addConstrs((demand[i] <= open[i] for i in range(n_plants)), name=f"demand_satisfaction_s{s}")

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    return model


# %%
# **Define stronger customized Benders feasibility cut using IIS:**
def cut_generator(master_problem: MasterProblem, sub_problem: SubProblems):
    """
    Generate a stronger feasibility cut using the Irreducible Infeasible Subsystem (IIS) of the subproblem.
    Though `master_problem` is not used, it is required as a placeholder for the callback function.
    """

    # Avoid duplicate cuts
    cuts = set()

    for i, sub in enumerate(sub_problem):
        if sub.status == CST.INFEASIBLE:
            # Compute the IIS of the subproblem
            sp = sub.model._solver_model
            sp.Params.OutputFlag = 0
            sp.Params.LogToConsole = 0
            sp.computeIIS()
            # Save IIS to file
            # sp.write("subproblem.ilp")

            # Get the names of the variables in the IIS
            # v.IISLB and v.IISUB can be either 0 (False) or 1 (True), indicating whether the LB or UB is part of the IIS.
            iis_vars = [v.VarName for v in sp.getVars() if v.IISLB or v.IISUB]
            iis_var_values = master_problem.get_var_values(iis_vars)

            cut = NoGoodFC(iis_var_values)
            cuts.add(cut)

    return list(cuts)


# %%
# Solve the problem using the deterministic equivalent (for clarity and verification):
if __name__ == '__main__':
    # Data
    n_plants = 9
    n_scenarios = 2
    scenarios = [[random.choice([0, 1]) for _ in range(n_plants)] for _ in range(n_scenarios)]

    # Deterministic equivalent solution
    de_model = deterministic_equivalent_model(n_plants, scenarios)
    de_model.optimize()
    if de_model.Status == GRB.OPTIMAL:
        print(f"Deterministic Equivalent Obj: {de_model.ObjVal:.4f}\n")
    else:
        print("Deterministic Equivalent Problem is infeasible or unbounded.\n")

    # Without IIS-based cuts
    master_model, complicating_vars = first_stage_model(n_plants)
    sub_models = second_stage_model(n_plants, scenarios)
    L = IntegerLShaped.from_models(
        master_model=master_model,
        master_solver=Gurobi,
        sub_model=sub_models,
        sub_solver=Gurobi,
        complicating_vars=complicating_vars,
    )
    L.solve()

    # With IIS-based cuts
    master_model, complicating_vars = first_stage_model(n_plants)
    sub_models = second_stage_model(n_plants, scenarios)
    L_IIS = IntegerLShaped.from_models(
        master_model=master_model,
        master_solver=Gurobi,
        sub_model=sub_models,
        sub_solver=Gurobi,
        complicating_vars=complicating_vars,
        feasibility_cut=cut_generator,
    )
    L_IIS.solve()

    print()
    print(f"Sol. Time (IIS vs Naive): {L_IIS.result.time:.4f}, {L.result.time:.4f}")
    print(f"Num. Cuts (IIS vs Naive): {L_IIS.result.n_cuts}, {L.result.n_cuts}")

    # Plot cut added
    plt.bar(['IIS-based Cuts', 'Naive Cuts'], [L_IIS.result.n_cuts, L.result.n_cuts], color=['blue', 'orange'])
    plt.ylabel('Number of Feasibility Cuts Added')
    plt.title('Comparison of Feasibility Cuts Added')
    plt.show()

# %%
#
# .. admonition:: References
#
#     * Tutorial of the integer L-shaped method: :doc:`../tutorials/ilshape`
#     * This example uses the following class: :ref:`api-ilshape`
#
# .. seealso::
#
#     * Example of the L-shaped method: :doc:`lshape`

# coding:utf-8

"""
Stochastic Logic-Based Benders Decomposition
============================================

.. currentmodule:: benderslib

This example demonstrates how to implement a Logic-Based Benders Decomposition method for two-stage stochastic problems,
with custom subproblem solver using BendersLib.
"""

# %%
# Define the master problem:
from benderslib import CST, MasterProblem, Gurobi, LogicBasedBenders, CombinatorialFCGen
from gurobipy import Model, GRB
import random


def master_model(n_plants):
    model = Model("Master")

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
    model.setObjective(open.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [open[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Use a simple function as subproblem solver.
# The input is a dictionary of complicating variable values.
# The output is a tuple:
# (:attr:`LogicBasedSubProblem.status`, :attr:`LogicBasedSubProblem.obj`, :attr:`LogicBasedSubProblem.var_values`).
def sub_solver(complicating_var_values):
    n_plants = len(complicating_var_values)
    scenarios = [random.randint(0, n_plants) for _ in range(n_plants)]

    # Sub problem is feasible if it covers demand in all scenarios.
    for s in scenarios:
        if sum(complicating_var_values.values()) < s:
            return CST.INFEASIBLE, None, {}
    return CST.OPTIMAL, 0, {}


# %%
# Function as subproblem solver:
n_plants = 8
master_model, complicating_vars = master_model(n_plants)
master_model_copy = master_model.copy()

master_problem = MasterProblem(Gurobi(master_model))
LBBD = LogicBasedBenders(
    master_problem=master_problem,
    sub_problem=sub_solver,
    complicating_vars=complicating_vars,
    feasibility_cut=CombinatorialFCGen,
)
LBBD.solve()

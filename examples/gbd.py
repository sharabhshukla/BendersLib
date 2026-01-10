# coding:utf-8

"""
Generalized Benders Decomposition
============================================

.. currentmodule:: benderslib

This example demonstrates how to implement a simple Generalized Benders Decomposition
with subproblem being a convex Quadratic Programming (QP) problem

.. admonition:: Limitation
    :class: attention

    Gurobi is not dedicated to nonlinear programming, and its support for nonlinear models is limited.
    To get coefficients of Benders cuts from Gurobi, the subproblem must satisfy certain conditions.

    - **Optimality Cuts**:
      The subproblem must be a convex linearly constrained Quadratic Programming (QP) problem
      to obtain dual variables of constraints.
    - **Feasibility Cuts**:
      The subproblem's constraints must be a linear system to obtain Farkas duals.
"""

# %%
# Define master problem and subproblem:
import gurobipy as gp
from gurobipy import GRB

from benderslib import GeneralizedBenders, MasterProblem, SubProblem, ClassicalBenders, ClassicalFCGen
from benderslib.solvers import Gurobi
import random


def create_master_problem(warehouse_num, price, budget):
    model = gp.Model("master")
    x = model.addVars(range(warehouse_num), vtype=GRB.INTEGER, name="inventory")

    # Budget constraint
    model.addConstr(gp.quicksum(price[i] * x[i] for i in range(warehouse_num)) <= budget, "budget")

    # Objective: minimize inventory cost
    model.setObjective(gp.quicksum(price[i] * x[i] for i in range(warehouse_num)), GRB.MINIMIZE)

    model.update()
    complicating_vars = [var.VarName for var in x.values()]
    return model, complicating_vars


def create_sub_problem(warehouse_num, demand, max_shortage_ratio, linear_obj, linear_con):
    model = gp.Model("subproblem")
    shortage = model.addVars(range(warehouse_num), lb=0, vtype=GRB.CONTINUOUS, name="shortage")
    inventory = model.addVars(range(warehouse_num), vtype=GRB.CONTINUOUS, name="inventory")

    # Objective: minimize shortage cost
    if linear_obj:
        model.setObjective(gp.quicksum(shortage[i] for i in range(warehouse_num)), GRB.MINIMIZE)
    else:
        model.setObjective(gp.quicksum(shortage[i] * shortage[i] for i in range(warehouse_num)), GRB.MINIMIZE)

    # Constraints: define shortage based on demand
    model.addConstrs(shortage[i] >= demand[i] - inventory[i] for i in range(warehouse_num))

    # Constraints: limit maximum shortage ratio
    if linear_con:
        model.addConstrs(shortage[i] <= max_shortage_ratio * demand[i] for i in range(warehouse_num))
    else:
        model.addConstrs(shortage[i] * shortage[i] <= max_shortage_ratio * demand[i] for i in range(warehouse_num))

    model.update()
    return model


# %%
# Define complete model for validation:
def create_complete_model(warehouse_num, price, budget, demand, max_shortage_ratio, linear_obj, linear_cone):
    model = gp.Model("complete")

    # Variables from master and subproblem
    x = model.addVars(range(warehouse_num), vtype=GRB.INTEGER, name="inventory")
    shortage = model.addVars(range(warehouse_num), lb=0, vtype=GRB.CONTINUOUS, name="shortage")

    # Budget constraint from master
    model.addConstr(gp.quicksum(price[i] * x[i] for i in range(warehouse_num)) <= budget, "budget")

    # Constraints from subproblem: define shortage based on demand
    model.addConstrs(shortage[i] >= demand[i] - x[i] for i in range(warehouse_num))

    # Constraints from subproblem: limit maximum shortage ratio
    if linear_con:
        model.addConstrs(shortage[i] <= max_shortage_ratio * demand[i] for i in range(warehouse_num))
    else:
        model.addConstrs(shortage[i] * shortage[i] <= max_shortage_ratio * demand[i] for i in range(warehouse_num))

    # Combined objective
    master_obj = gp.quicksum(price[i] * x[i] for i in range(warehouse_num))
    if linear_obj:
        sub_obj = gp.quicksum(shortage[i] for i in range(warehouse_num))
    else:
        sub_obj = gp.quicksum(shortage[i] * shortage[i] for i in range(warehouse_num))
    model.setObjective(master_obj + sub_obj, GRB.MINIMIZE)

    model.update()
    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    return model


# %%
# Solve with Generalized Benders Decomposition:
if __name__ == "__main__":
    # Data
    warehouse_num = 8
    random.seed(1)
    price = [random.randrange(10, 50) for _ in range(warehouse_num)]
    demand = [random.randrange(20, 100) for _ in range(warehouse_num)]
    budget = 50000
    max_shortage_ratio = .8
    linear_obj = False
    linear_con = True

    # Create master problem
    master_problem_model, complicating_vars = create_master_problem(warehouse_num, price, budget)
    master_problem = MasterProblem(Gurobi(master_problem_model))

    # Create sub problem
    sub_problem_model = create_sub_problem(warehouse_num, demand, max_shortage_ratio, linear_obj, linear_con)
    sub_problem = SubProblem(Gurobi(sub_problem_model))

    # Create Benders decomposition instance
    benders = GeneralizedBenders(
        master_problem=master_problem,
        sub_problem=sub_problem,
        complicating_vars=complicating_vars
    )
    benders.solve()

    # Complete model for validation
    complete_model = create_complete_model(
        warehouse_num, price, budget, demand, max_shortage_ratio, linear_obj, linear_con)
    complete_model.optimize()
    if complete_model.Status == GRB.OPTIMAL:
        print(f"\nComplete model objective: {complete_model.ObjVal:.2f}")

# %%
#
# .. admonition:: References
#
#     * Tutorial of the Generalized Benders Decomposition: :doc:`../tutorials/gbd`
#     * This example uses the following class: :class:`GeneralizedBenders`

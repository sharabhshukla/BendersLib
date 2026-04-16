# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
OR-Tools
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Ortools` as a solver backend.

from benderslib import CombinatorialBenders, MasterProblem, SubProblem
from benderslib.solvers import Ortools, Gurobi
from benderslib.utils import draw_curve

import gurobipy as gp
from gurobipy import GRB

from ortools.sat.python import cp_model


def make_model(n_vars):
    model = cp_model.CpModel()
    x = [model.NewBoolVar(f"x[{i}]") for i in range(n_vars)]
    y = [model.NewBoolVar(f"y[{i}]") for i in range(n_vars)]

    for i in range(n_vars):
        model.Add(y[i] == 1)
        if i <= int(n_vars / 2):
            model.Add(y[i] <= x[i])

    model.Minimize(sum(x) + sum(y))
    return model


def make_master_problem(n_vars):
    model = gp.Model()
    x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
    model.setObjective(x.sum(), sense=GRB.MINIMIZE)
    model.update()
    return model, [x.VarName for x in x.values()]


def make_sub_problem(n_vars):
    model = cp_model.CpModel()
    y = [model.NewIntVar(name=f"y[{i}]", lb=0, ub=2) for i in range(n_vars)]
    x = [model.NewBoolVar(f"x[{i}]") for i in range(n_vars)]

    for i in range(n_vars):
        model.Add(y[i] == 1)
        # Ensure optimality cuts are generated
        if i <= int(n_vars / 2):
            model.Add(y[i] <= x[i])

    model.Minimize(sum(y))

    vars_map = {f"x[{i}]": x[i] for i in range(n_vars)}
    vars_map.update({f"y[{i}]": y[i] for i in range(n_vars)})
    return model, vars_map


if __name__ == '__main__':
    n_vars = 7

    # Complete model
    model = make_model(n_vars)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"Ortools Objective value: {solver.ObjectiveValue()}")
    print()

    # Benders Decomposition
    master_model, master_vars = make_master_problem(n_vars)
    sub_model, vars_map = make_sub_problem(n_vars)
    master_problem = MasterProblem(Gurobi(master_model))
    sub_problem = SubProblem(Ortools(sub_model, vars_map))
    BD = CombinatorialBenders(
        master_problem=master_problem,
        sub_problem=sub_problem,
        complicating_vars=master_vars,
    )
    BD.solve()

    draw_curve(BD.result)

# %%
#
# .. tags:: benders: classical, solver: ortools (cp), deterministic

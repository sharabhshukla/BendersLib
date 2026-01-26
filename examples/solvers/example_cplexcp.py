"""
Cplex CP
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.CplexCP` as a solver backend.

from benderslib import CombinatorialBenders, MasterProblem, SubProblem
from benderslib.solvers import CplexCP, Gurobi
from benderslib.utils import draw_curve

import gurobipy as gp
from gurobipy import GRB

from docplex.cp.model import CpoModel


def make_model(n_vars):
    model = CpoModel()
    x = [model.binary_var(name=f"x[{i}]") for i in range(n_vars)]
    y = [model.binary_var(name=f"y[{i}]") for i in range(n_vars)]

    for i in range(n_vars):
        model.add(y[i] == 1)
        if i <= int(n_vars / 2):
            model.add(y[i] <= x[i])

    model.minimize(model.sum(x) + model.sum(y))
    return model


def make_master_problem(n_vars):
    model = gp.Model()
    x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
    model.setObjective(x.sum(), sense=GRB.MINIMIZE)
    model.update()
    return model, [x.VarName for x in x.values()]


def make_sub_problem(n_vars):
    model = CpoModel()
    y = [model.binary_var(name=f"y[{i}]") for i in range(n_vars)]
    x = [model.binary_var(name=f"x[{i}]") for i in range(n_vars)]

    for i in range(n_vars):
        model.add(y[i] == 1)
        # Ensure optimality cuts are generated
        if i <= int(n_vars / 2):
            model.add(y[i] <= x[i])

    model.minimize(model.sum(y))

    vars_map = {f"x[{i}]": x[i] for i in range(n_vars)}
    vars_map.update({f"y[{i}]": y[i] for i in range(n_vars)})
    return model, vars_map


if __name__ == '__main__':
    n_vars = 7

    # Complete model
    model = make_model(n_vars)
    solution = model.solve()
    if solution:
        print(f"Cplex CP Objective value: {solution.get_objective_value()}")
    print()

    # Benders Decomposition
    master_model, master_vars = make_master_problem(n_vars)
    sub_model, vars_map = make_sub_problem(n_vars)
    master_problem = MasterProblem(Gurobi(master_model))
    sub_problem = SubProblem(CplexCP(sub_model, vars_map))
    BD = CombinatorialBenders(
        master_problem=master_problem,
        sub_problem=sub_problem,
        complicating_vars=master_vars,
    )
    BD.solve()

    draw_curve(BD.result)

# coding:utf-8

"""
CPLEX
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Cplex` as a solver backend.

from benderslib import AnnotationBenders, ClassicalBenders
from benderslib.solvers import Cplex
from benderslib.utils import draw_curve

import cplex


def make_original_problem():
    model = cplex.Cplex("m.lp")

    var_names = model.variables.get_names()
    var_types = model.variables.get_types()

    complicating_vars = [
        name for name, type in zip(var_names, var_types) if type != model.variables.type.continuous
    ]
    return model, complicating_vars


def make_model():
    model = cplex.Cplex()
    n_vars = 10

    # Add variables
    y_names = [f"y_{i}" for i in range(n_vars)]
    z_names = [f"z_{i}" for i in range(n_vars)]

    model.variables.add(
        names=y_names, types=[model.variables.type.integer] * n_vars, lb=[1] * n_vars, ub=[40] * n_vars)
    model.variables.add(
        names=z_names, types=[model.variables.type.continuous] * n_vars, lb=[1] * n_vars, ub=[40] * n_vars)

    # Set objective
    model.objective.set_sense(model.objective.sense.minimize)
    for i in range(n_vars):
        model.objective.set_linear(y_names[i], 2)
        model.objective.set_linear(z_names[i], 3)

    # Add constraints
    # sum(y) + sum(z) <= 50 * n_vars
    lin_expr = cplex.SparsePair(ind=y_names + z_names, val=[1] * (2 * n_vars))
    model.linear_constraints.add(lin_expr=[lin_expr], senses=["L"], rhs=[50 * n_vars], names=["main_constr_yz"])

    # 2 * y[i] <= 2 * (i + 1)
    for i in range(n_vars):
        lin_expr = cplex.SparsePair(ind=[y_names[i]], val=[2])
        model.linear_constraints.add(lin_expr=[lin_expr], senses=["L"], rhs=[2 * (i + 1)], names=[f"constr_y_{i}"])

    # 2 * y[i] + z[i] >= i
    for i in range(n_vars):
        lin_expr = cplex.SparsePair(ind=[y_names[i], z_names[i]], val=[2, 1])
        model.linear_constraints.add(lin_expr=[lin_expr], senses=["G"], rhs=[i], names=[f"constr_yz_{i}"])

    # 3 * z[i] <= 15
    for i in range(n_vars):
        lin_expr = cplex.SparsePair(ind=[z_names[i]], val=[3])
        model.linear_constraints.add(lin_expr=[lin_expr], senses=["L"], rhs=[15], names=[f"constr_z_{i}"])

    complicating_vars = y_names
    return model, complicating_vars


if __name__ == '__main__':
    model, complicating_vars = make_model()
    model.solve()
    print("\n CPLEX Objective value:", model.solution.get_objective_value())

    print()
    BD = AnnotationBenders(model, solver=Cplex, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.solve()

    draw_curve(BD.result)

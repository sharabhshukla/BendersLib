# coding:utf-8

"""
Gurobi IIS
=======================================

.. currentmodule:: benderslib.solvers

"""

# %%
# Using :meth:`Gurobi.compute_iis` to compute conflicting variables.


from benderslib.solvers import Gurobi

import gurobipy as gp
from gurobipy import GRB


def make_sub_problem():
    model = gp.Model(name='InfeasibleExample')

    x = model.addVar(lb=0, ub=5, vtype=GRB.INTEGER, name='x')
    y = model.addVar(lb=0, ub=5, vtype=GRB.INTEGER, name='y')

    model.addConstr(x >= 5, name='c1')
    model.addConstr(y >= 5, name='c2')
    model.addConstr(x + y <= 9, name='c3')

    model.update()

    return model


if __name__ == '__main__':
    sub = make_sub_problem()

    # For simplicity, we directly use the Gurobi solver interface from BendersLib.
    # Typically, this should be wrapped in the SubProblem class like SubProblem(Gurobi(...)).
    sub_problem_solver = Gurobi(sub)

    sub_problem_solver.solve()
    print("Optimization status :", sub_problem_solver.status)
    iis_vars = sub_problem_solver.compute_iis()
    print("Variables in the IIS:", iis_vars)

# %%
#
# .. tags:: solver: gurobi, iis

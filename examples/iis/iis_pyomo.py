# coding:utf-8

"""
Pyomo IIS
=======================================

"""

# %%
# Using `Minimal Intractable System (MIS) Finder <https://pyomo.readthedocs.io/en/stable/api/pyomo.contrib.iis.mis.html>`_
# to compute conflicting constraints.

from benderslib.solvers import Pyomo

import pyomo.environ as pyo
from pyomo.contrib.iis.mis import compute_infeasibility_explanation as mis


def make_sub_problem():
    model = pyo.ConcreteModel(name='InfeasibleExample')

    model.x = pyo.Var(bounds=(0, 2), within=pyo.Integers)
    model.y = pyo.Var(bounds=(0, 2), within=pyo.Integers)

    model.c1 = pyo.Constraint(expr=model.x >= 5)
    model.c2 = pyo.Constraint(expr=model.y >= 5)
    model.c3 = pyo.Constraint(expr=model.x + model.y <= 9)

    model.obj = pyo.Objective(expr=0, sense=pyo.minimize)

    return model


solvers = [
    'cbc',
    'cplex',
    'cplex_direct',
    'glpk',
    'gurobi',
    'gurobi_direct',
    # 'highs',
    'scip',

    # 'xpress',
    # 'xpress_direct',

    # 'mosek',        # License expires in one month
    # 'mosek_direct', # License expires in one month
]

for solver in solvers:
    model = make_sub_problem()
    model_copy = model.clone()
    pyomo_solver = Pyomo(model, solver=solver)

    # Pyomo Wrapper

    print("\nSolver     :", solver)
    iis_vars = pyomo_solver.compute_iis()
    print("Vars in IIS:", iis_vars)

    # Direct

    # mis(model_copy, solver=solver)

# %%
#
# .. tags:: solver: pyomo, iis

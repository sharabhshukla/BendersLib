# coding:utf-8

"""
SCIP
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Scip` as a solver backend.

from benderslib import ClassicalBenders, AnnotationBenders
from benderslib.solvers import Scip
from benderslib.utils import draw_curve

from pyscipopt import Model


def make_original_problem():
    model = Model("Original")

    n_vars = 10
    y = [model.addVar(vtype="I", name=f"y_{i}", ub=40) for i in range(n_vars)]
    z = [model.addVar(vtype="C", name=f"z_{i}", ub=40) for i in range(n_vars)]

    # Workaround for incorrect dual values of bound constraints in SCIP
    dummy = model.addVar(vtype="C", name="dummy", ub=0, lb=0, obj=0)

    model.setObjective(2 * sum(y) + 3 * sum(z), "minimize")

    model.addCons(sum(y) + sum(z) <= 50 * n_vars)

    model.addConss([2 * y[i] + dummy <= 2 * (i + 1) for i in range(n_vars)])
    model.addConss([2 * y[i] + z[i] >= i for i in range(n_vars)])
    model.addConss([3 * z[i] + dummy <= 15 for i in range(n_vars)])

    complicating_vars = [f"y_{i}" for i in range(n_vars)]
    return model, complicating_vars


if __name__ == '__main__':
    model, master_vars = make_original_problem()

    model.optimize()
    model.freeTransform()
    print()

    BD = AnnotationBenders(
        model,
        solver=Scip,
        complicating_vars=master_vars,
        benders=ClassicalBenders
    )
    BD.solve()

    draw_curve(BD.result)

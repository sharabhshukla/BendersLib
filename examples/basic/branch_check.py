# coding:utf-8

"""
Branch-and-check Method
=========================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotationBenders
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve
from gurobipy import Model, GRB


def make_original_problem():
    model = Model("Original")

    n_vars = 20
    y = model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

    model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr_yz")
    model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
    model.addConstrs((2 * y[i] + z[i] >= i for i in range(n_vars)), name="constr_yz")
    model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_z")

    model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Solve the problem using Branch-and-check method:

model, complicating_vars = make_original_problem()
BD = AnnotationBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)
BD.benders.params.tol_rel = 0.05
BD.benders.bnc_solve()
draw_curve(BD.result)

# %%
# .. seealso::
#
#    - A brief introduction to :ref:`enhance_branch_and_check`.
#    - Its classical implementation counterpart is :doc:`annotation_benders`.
#      The acceleration is remarkable!!
#
# .. tags:: benders: classical, solver: gurobi, deterministic, enhancement, branch-and-check

# coding:utf-8

"""
Combinatorial Benders using Branch-and-check Method
====================================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import AnnotationBenders, CombinatorialBenders
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB


def make_original_problem():
    # The problem is constructed such that the IIS involves only a few complicating variables.
    model = Model()

    n_vars = 9
    x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
    y = model.addVars(n_vars, name="y", vtype=GRB.BINARY)

    # Constraint 1: All subproblem variables must be one
    model.addConstrs((y[i] == 1 for i in range(n_vars)), name="sub")
    # Constraint 2: But, part of the subproblem variables must be smaller than its first-stage counterpart
    model.addConstrs((y[i] <= x[i] for i in range(int(n_vars))), name="link")

    # Objective: minimize the number of non-zero first-stage variables, second-stage has no objective
    model.setObjective(x.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    complicating_vars = [v.VarName for v in x.values()]
    return model, complicating_vars


# %%
# Solve the problem using Branch-and-check method.

model, complicating_vars = make_original_problem()

BD = AnnotationBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=CombinatorialBenders,
)
BD.params.use_iis_cut = True
BD.params.use_bnc = True
BD.solve()

# %%
# .. seealso::
#
#    - A brief introduction to :ref:`enhance_branch_and_check`.
#    - Its classical implementation counterpart is :doc:`../advanced/cbd_iis`.
#      The acceleration is remarkable!!
#
# .. tags:: benders: classical, solver: gurobi, deterministic, enhancement, branch-and-check

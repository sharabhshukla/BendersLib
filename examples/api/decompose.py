# coding:utf-8

"""
Retrieve master and sub problems
=======================================================

This example shows how to obtain the master and sub problems from a complete mathematical programming model.
This functionality is useful for users who have implemented a complete model (usually for comparison purposes)
and want to implement a Benders decomposition method based on that model
without manually defining the master and sub problems.
"""

# %%
# Import necessary modules:
from gurobipy import Model, GRB
from benderslib import AnnotationBenders
from benderslib.solvers import Gurobi


# %%
# Create the original problem:
def make_original_problem():
    model = Model("Original")

    n_vars = 20
    y = model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

    model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr")
    model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
    model.addConstrs((2 * y[i] + z[i] >= i for i in range(n_vars)), name="constr_yz")
    model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_zx")

    model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Obtain the master and sub problems:
model, complicating_vars = make_original_problem()
master, sub = AnnotationBenders._decompose(
    original_problem=model,
    solver=Gurobi,
    master_vars=complicating_vars,
    # True: return solver model instances;
    # False: return benderslib MasterProblem and SubProblem instances.
    solver_model=True
)
master.update()
print(master)

# %%
#
# .. admonition:: References
#
#     * This example uses the following class: :class:`~benderslib.AnnotationBenders`
#     * See :func:`~benderslib.solvers.Gurobi.make_master_problem` for details on how the master problem is constructed.
#     * See :func:`~benderslib.solvers.Gurobi.make_sub_problem` for details on how the subproblem is constructed.
#
# .. seealso::
#
#     * Automated decomposition based on master problem variables: :doc:`../../examples/annotation_benders`

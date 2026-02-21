# coding:utf-8

"""
Callback in Branch-and-Check Method
=========================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotationBenders, CallbackBase, BendersContext, CST
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
# Define the callback.

class BncCallback(CallbackBase):

    def __init__(self):
        self.feasible_solutions = []

    def on_opti_cut_generated(self, context: BendersContext):
        if context.where == CST.INCUMBENT:
            sol = context.sub_problem.get_var_values()
            self.feasible_solutions.append(sol)

        if context.where == CST.NODE:
            pass


# %%
# Solve the problem using Branch-and-Check method:

model, complicating_vars = make_original_problem()
BD = AnnotationBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)
# BD.benders.params.tol_rel = 0.05
# BD.params.bnc_frac_sol = True
callback = BncCallback()
BD.benders.register_callback(callback)
BD.benders.bnc_solve()
draw_curve(BD.result)

print(f"\nFound {len(callback.feasible_solutions)} feasible solutions.")

# %%
# .. seealso::
#
#    - A brief introduction to :ref:`enhance_branch_and_check`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, branch-and-check

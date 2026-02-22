# coding:utf-8

"""
Callback in Branch-and-Check Method
=========================================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import ClassicalBenders, AnnotationBenders, BendersContext, CST
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve, is_all_integer

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
# Define the callback, which generates optimality cuts only from integer solutions
# in the early iterations, and turns off cut generation from fractional solutions
# after a specified number of iterations.

def on_opti_cut_generated(context: BendersContext):
    if context.benders.result.n_iter <= 50:

        if context.where == CST.NODE:
            int_vars = context.master_problem.solver._int_vars
            int_vars += context.master_problem.solver._bin_vars
            master_sol = context.master_problem.get_var_values(int_vars)

            if not is_all_integer(master_sol.values()):
                # Add optimality cuts from only integer solutions
                context.current_opti_cuts = []

    else:
        # Turn off cut generation from fractional solutions
        # after a specified number of iterations
        context.benders.params.bnc_frac_sol = False


# %%
# Solve the problem using Branch-and-Check method with the defined callback.

model, complicating_vars = make_original_problem()
model_copy = model.copy()

BD = AnnotationBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

BD.benders.params.bnc_frac_sol = True

BD.benders.register_callback(on_opti_cut_generated)
BD.benders.bnc_solve()

draw_curve(BD.result)

# %%
# Solve the problem using trivial Branch-and-Check method.

BD = AnnotationBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)

BD.benders.bnc_solve()
draw_curve(BD.result)

# %%
# .. seealso::
#
#    - A brief introduction to :ref:`enhance_branch_and_check`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, branch-and-check, enhancement

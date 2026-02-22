# coding:utf-8

"""
Warm Start
=======================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import AnnotationBenders, ClassicalBenders, CallbackBase, CST
from benderslib.utils import draw_curve
from benderslib.solvers import Gurobi

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
# Define a custom callback to implement warm start.
# You can store the previous master and subproblem solutions
# as persistent data in the callback class, and use them to set
# the initial solution for the master and subproblem in the
# corresponding callback methods.

class WarmStartCallback(CallbackBase):

    def __init__(self):
        self.pre_master_sol = {}
        self.pre_sub_sol = {}

    def on_before_master_solve(self, context):
        model = context.master_problem.model
        for var in model.getVars():
            if var.VarName in self.pre_master_sol:
                var.Start = self.pre_master_sol[var.VarName]

    def on_after_master_solve(self, context):
        if context.master_problem.status == CST.OPTIMAL:
            self.pre_master_sol = context.master_problem.get_var_values()

    def on_before_sub_solve(self, context):
        model = context.sub_problem.model
        for var in model.getVars():
            if var.VarName in self.pre_sub_sol:
                var.Start = self.pre_sub_sol[var.VarName]

    def on_after_sub_solve(self, context):
        if context.sub_problem.status == CST.OPTIMAL:
            self.pre_sub_sol = context.sub_problem.get_var_values()


# %%
# Use the callback in the Benders decomposition process.

# Solve original problem for comparison
model, complicating_vars = make_original_problem()

# Create the Benders decomposition solver
AB = AnnotationBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)

# Register the warm start callback
warm_start_callback = WarmStartCallback()
AB.benders.register_callback(warm_start_callback)
AB.solve()

draw_curve(AB.result)

# %%
# .. seealso::
#
#    - A brief introduction to :ref:`enhance_warm_start`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement

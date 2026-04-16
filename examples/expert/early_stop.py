# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
Early Stop
=======================
"""

# %%
# Prepare the problem for Benders decomposition.

from benderslib import AnnotatedBenders, ClassicalBenders, CallbackBase, CST
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
# The callback will terminate the Benders process
# after a certain number of iterations,
# when there is no improvement in the upper bound.

class EarlyStop(CallbackBase):

    def __init__(self, n_iter_threshold):
        self.n_iter_threshold = n_iter_threshold
        self.best_ub = float('Inf')
        self.iter_counter = 0

    def on_iteration_end(self, context):
        current_ub = context.state.ub

        if current_ub < self.best_ub:
            # If new best solution is found
            self.iter_counter = 0
            self.best_ub = current_ub
            return CST.PROCEED

        else:
            self.iter_counter += 1

            if self.iter_counter >= self.n_iter_threshold:
                # If no improvement in upper bound for n_iter_threshold iterations

                if not context.state.status == CST.UNSOLVED:
                    # Ensure termination only happens with at least one solution found

                    print(f"No improvement in upper bound for {self.n_iter_threshold} iterations, terminating...")

                    # Return the termination signal to stop the Benders process
                    return CST.TERMINATE
            else:
                return CST.PROCEED


# %%
# Use the callback in the Benders decomposition process.

# Solve original problem for comparison
model, complicating_vars = make_original_problem()

# Create the Benders decomposition solver
BD = AnnotatedBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)

# Register the callback
BD.register(EarlyStop(10))

# This example works well with the Branch-and-check method, try it!
# BD.params.use_bnc = True

BD.solve()
draw_curve(BD.result)

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#    - A brief introduction to :ref:`enhance_early_stop`.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback, enhancement, branch-and-check

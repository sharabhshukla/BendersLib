# coding:utf-8

"""
Save All Feasible Solutions
===========================================
"""

# %%
# Prepare the master and subproblem for Benders decomposition.

from benderslib import ClassicalBenders, CallbackBase, CST
from benderslib.solvers import Gurobi

from gurobipy import Model, GRB


def make_master_problem():
    model = Model("Master")
    x = model.addVar(name="x", vtype=GRB.INTEGER, lb=0, ub=10)
    z = model.addVar(name="z")
    model.setObjective(x)
    model.update()
    return model, [x.VarName, z.VarName]


def make_sub_problem():
    model = Model("Sub")
    master_x = model.addVar(name="x")
    y = model.addVar(name="y")
    master_z = model.addVar(name="z")
    model.setObjective(2 * y)
    model.addConstr(master_x + y + master_z == 14)
    model.addConstr(master_x - y == 2)
    model.update()
    return model


# %%
# Define a custom callback to save all feasible solutions.

class SaveSolutionsCallback(CallbackBase):
    def __init__(self):
        self.feasible_solutions = []

    def on_after_master_solve(self, context):
        # Master problem is solved, we can get the solution
        solution = {
            var.VarName: var.X for var in context.master_problem.model.getVars()
        }
        self.feasible_solutions.append(solution)
        print(f"Master solution found: {solution}")

    def on_after_sub_solve(self, context):
        # Exclude the case where the subproblem is infeasible
        if context.sub_problem.status == CST.INFEASIBLE:
            self.feasible_solutions.pop()
            print("Subproblem infeasible, discarding the master solution.")


# %%
# Use the callback in the Benders decomposition process.

master_model, complicating_vars = make_master_problem()
sub_model = make_sub_problem()

BD = ClassicalBenders.from_models(
    master_model, Gurobi,
    sub_model, Gurobi,
    complicating_vars=complicating_vars
)

# Register the callback
save_cb = SaveSolutionsCallback()
BD.register(save_cb)

# Solve the problem
BD.solve()

# Print all saved feasible solutions
print("\nAll feasible solutions found during the Benders process:")
for i, sol in enumerate(save_cb.feasible_solutions):
    print(f"Solution {i + 1}: {sol}")

# %%
# .. seealso::
#
#    - This example uses the :doc:`../../manual/callbacks` functionality.
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback

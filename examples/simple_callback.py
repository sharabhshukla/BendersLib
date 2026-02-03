# coding:utf-8

"""
Simple Callback
=======================

"""

# %%
# Prepare the master and subproblem for Benders decomposition.

from benderslib import ClassicalBenders
from benderslib.callback import BendersCallback, BendersContext
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB


def make_master_problem():
    model = Model("Master")
    x = model.addVar(name="x", vtype=GRB.INTEGER)
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
# Define a custom callback by inheriting from BendersCallback.

class MyCallback(BendersCallback):
    some_persistent_data = 'Hi there!'

    def on_benders_start(self, context: BendersContext):
        print("Benders process started!")
        print(">>>>>>>>>>>>>>>>>>>>>>>>")
        print(self.some_persistent_data)
        print(">>>>>>>>>>>>>>>>>>>>>>>>")


# %%
# Define a lightweight function as a callback.

def on_benders_end(context: BendersContext):
    print("Benders process finished!")
    print(f"Final objective: {context.state.obj}")
    print(context)


# %%
# Using the callback in the Benders decomposition process.

if __name__ == '__main__':
    master_model, complicating_vars = make_master_problem()
    sub_model = make_sub_problem()

    benders = ClassicalBenders.from_models(
        master_model, Gurobi,
        sub_model, Gurobi,
        complicating_vars=complicating_vars
    )

    # Turn off console logging
    benders.params.log_to_console = False

    # Register the callback
    benders.register_callback(MyCallback())
    benders.register_callback(on_benders_end)

    # Solve the problem
    benders.solve()

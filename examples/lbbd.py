# coding:utf-8

"""
Logic-Based Benders Decomposition
============================================

.. currentmodule:: benderslib

This example demonstrates how to implement a simple Logic-Based Benders Decomposition
with custom subproblem solver using BendersLib.
The BendersLib accept a function or an instance class inherited from :class:`LogicBasedSubProblem`
as the input (``sub_problem``) of :class:`LogicBasedBenders`.

For custom cut generators, please refer to :doc:`../examples/cbd_iis` and :doc:`../examples/ilshape_iis`.
"""

# %%
# Define the master problem:
from benderslib import CST, MasterProblem, Gurobi, LogicBasedBenders, CombinatorialFCGen, LogicBasedSubProblem, NoGoodFC
from gurobipy import Model, GRB


def master_model(n_plants):
    model = Model("Master")

    open = model.addVars(n_plants, vtype=GRB.BINARY, name="open")
    model.setObjective(open.sum(), GRB.MINIMIZE)

    model.update()
    complicating_vars = [open[i].VarName for i in range(n_plants)]
    return model, complicating_vars


# %%
# Use a simple function as subproblem solver.
# The input is a dictionary of complicating variable values.
# The output is a tuple:
# (:attr:`LogicBasedSubProblem.status`, :attr:`LogicBasedSubProblem.obj`, :attr:`LogicBasedSubProblem.var_values`).
def sub_solver(complicating_var_values):
    # Sub problem is feasible if all plants are opened.
    if sum(complicating_var_values.values()) == len(complicating_var_values):
        return CST.OPTIMAL, 0, {}
    return CST.INFEASIBLE, None, {}


# %%
# Inherit from :class:`LogicBasedSubProblem` to define a custom subproblem.
# At least implement the :meth:`LogicBasedSubProblem.solve` method.
class SubProblem(LogicBasedSubProblem):

    def __init__(self, complicating_vars):
        super().__init__(complicating_vars)

    def solve(self):
        if sum(self.complicating_var_values.values()) == len(self.complicating_var_values):
            self.status = CST.OPTIMAL
            self.obj = 0
            self.var_values = {}
        else:
            self.status = CST.INFEASIBLE
            self.obj = None
            self.var_values = {}


# %%
# Custom feasibility cut generator:
def feasibility_cut_generator(master_problem, sub_problem):
    open_vars = sub_problem.complicating_var_values
    zeros = [i for i, val in open_vars.items() if val <= 0.01]

    cuts = []
    for z in zeros:
        # We know that all the plants that are closed (zero) must be opened (one).
        # Therefore, force zero variable to be one in the next iteration,
        # significantly reducing the number of Benders iterations.
        cut = NoGoodFC({z: 0})
        cuts.append(cut)

    return cuts


# %%
# Function as subproblem solver:
n_plants = 8
master_model, complicating_vars = master_model(n_plants)
master_model_copy = master_model.copy()

master_problem = MasterProblem(Gurobi(master_model))
LBBD = LogicBasedBenders(
    master_problem=master_problem,
    sub_problem=sub_solver,
    complicating_vars=complicating_vars,
    feasibility_cut=CombinatorialFCGen,
)
LBBD.solve()

# %%
# Class instance as subproblem solver:
master_problem = MasterProblem(Gurobi(master_model_copy))
LBBD = LogicBasedBenders(
    master_problem=master_problem,
    sub_problem=SubProblem(complicating_vars),
    complicating_vars=complicating_vars,
    feasibility_cut=feasibility_cut_generator
)
LBBD.solve()

# %%
#
# .. admonition:: References
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../tutorials/lbbd`
#     * This example uses the following class: :ref:`api-lbbd`

# coding:utf-8

"""
Template for Customizing Benders Decomposition
===============================================

"""

from gurobipy import Model
from benderslib import BendersSolver, Cut, CutGenerator, Gurobi, MasterProblem, SubProblem, BendersParams


# %%
# Define master problem and subproblem using your preferred solver interface:
def master_problem():
    return Model("Master")


def sub_problems():
    return Model("Sub")


# %%
# Use classes to define feasibility cut and optimality cut, if you want preserve some state during iterations,
# or the cut generation process is complex.
class OptiCut(CutGenerator):

    def __init__(self, master_problem: MasterProblem, sub_problem: SubProblem, params: BendersParams):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[Cut]:
        # Implement the logic to generate feasibility cut
        return []


class FeasCut(CutGenerator):

    def __init__(self, master_problem: MasterProblem, sub_problem: SubProblem, params: BendersParams):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[Cut]:
        # Implement the logic to generate feasibility cut
        return []


# %%
# BendersLib also supports defining cut generator functions directly.
# The signature of the cut generator functions should follow the example below.
def opti_cut_generator(master_problem, sub_problem) -> list[Cut]:
    ...


def feas_cut_generator(master_problem, sub_problem) -> list[Cut]:
    ...


if __name__ == '__main__':
    master_model = master_problem()
    sub_model = sub_problems()

    master_problem = MasterProblem(solver_backend=Gurobi(master_model))
    sub_problem = SubProblem(solver_backend=Gurobi(sub_model))

    BD = BendersSolver(
        master_problem=master_problem,
        sub_problem=sub_problem,
        complicating_vars=[],
        feasibility_cut=FeasCut,
        optimality_cut=OptiCut,
        # # Or using cut generator functions
        # feasibility_cut=feas_cut_generator,
        # optimality_cut=opti_cut_generator,
    )
    # BD.solve()

# coding:utf-8

"""
Gurobi
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Gurobi` as a solver backend.

from benderslib import AnnotationBenders, ClassicalBenders
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from pathlib import Path

from gurobipy import GRB
import gurobipy as gp


def make_original_problem():
    # env = gp.Env()
    # env.setParam("OutputFlag", 0)
    # model = gp.read("m.lp",env=env)

    model = gp.read(str(Path(__file__).parent / "m.lp"))

    complicating_vars = [v.VarName for v in model.getVars() if v.VType != GRB.CONTINUOUS]
    return model, complicating_vars


if __name__ == '__main__':
    model, complicating_vars = make_original_problem()
    model.optimize()

    print()
    BD = AnnotationBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.solve()

    draw_curve(BD.result)

# coding:utf-8

"""
Gurobi
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Gurobi` as a solver backend.

from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve

from pathlib import Path
import inspect

from gurobipy import GRB
import gurobipy as gp


def make_original_problem():
    # env = gp.Env()
    # env.setParam("OutputFlag", 0)
    # model = gp.read("m.lp",env=env)

    # Get the directory of the current file
    current_file_path = inspect.getfile(inspect.currentframe())
    lp_file_path = Path(current_file_path).parent / "m.lp"
    model = gp.read(str(lp_file_path))

    complicating_vars = [v.VarName for v in model.getVars() if v.VType != GRB.CONTINUOUS]
    return model, complicating_vars


if __name__ == '__main__':
    model, complicating_vars = make_original_problem()
    model_copy = model.copy()
    model.optimize()

    BD = AnnotatedBenders(model, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.solve()

    BD = AnnotatedBenders(model_copy, solver=Gurobi, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.params.use_bnc = True
    BD.solve()

    draw_curve(BD.result)

# %%
#
# .. tags:: benders: classical, solver: gurobi, deterministic, branch-and-check

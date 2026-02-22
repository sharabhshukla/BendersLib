# coding:utf-8

"""
COPT
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Copt` as a solver backend.

from benderslib import AnnotationBenders, ClassicalBenders
from benderslib.solvers import Copt
from benderslib.utils import draw_curve

import inspect
from pathlib import Path

from coptpy import COPT
import coptpy


def make_original_problem():
    env = coptpy.Envr()
    model = env.createModel()

    # Get the directory of the current file
    current_file_path = inspect.getfile(inspect.currentframe())
    lp_file_path = Path(current_file_path).parent / "m.lp"
    model.readLp(str(lp_file_path))

    complicating_vars = [v.name for v in model.getVars() if v.vtype != COPT.CONTINUOUS]
    return model, complicating_vars


if __name__ == '__main__':
    model, complicating_vars = make_original_problem()
    model_copy = model.clone()
    model.solve()

    BD = AnnotationBenders(model, solver=Copt, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.solve()

    BD = AnnotationBenders(model_copy, solver=Copt, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.params.use_bnc = True
    BD.solve()

    draw_curve(BD.result)

# %%
#
# .. tags:: benders: classical, solver: copt, deterministic, branch-and-check

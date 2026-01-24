# coding:utf-8

from benderslib import AnnotationBenders, ClassicalBenders
from benderslib.solvers import Copt
from benderslib.utils import draw_curve

from coptpy import COPT
import coptpy


def make_original_problem():
    env = coptpy.Envr()
    model = env.createModel()
    model.readLp("m.lp")

    complicating_vars = [v.name for v in model.getVars() if v.vtype != COPT.CONTINUOUS]
    return model, complicating_vars


if __name__ == '__main__':
    model, complicating_vars = make_original_problem()
    model.solve()

    print()
    BD = AnnotationBenders(model, solver=Copt, complicating_vars=complicating_vars, benders=ClassicalBenders)
    BD.solve()

    draw_curve(BD.result)

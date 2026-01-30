# coding:utf-8

import pytest
import os
from .test_solver_base import BaseTestSolver

try:
    import coptpy as cp
    from benderslib.solvers import Copt

    copt_available = True
except ImportError:
    copt_available = False

LP_FILE = os.path.join(os.path.dirname(__file__), "lp.lp")


@pytest.mark.skipif(not copt_available, reason="COPT is not installed")
class TestCopt(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        env = cp.Envr()
        model = env.createModel()
        model.readLp(LP_FILE)
        return Copt(model)

    @pytest.fixture
    def infeasible_solver_instance(self):
        env = cp.Envr()
        model = env.createModel()
        model.readLp(LP_FILE)
        x1 = model.getVarByName("x1")
        x2 = model.getVarByName("x2")
        model.addConstr(x1 + x2 <= 3)
        return Copt(model)

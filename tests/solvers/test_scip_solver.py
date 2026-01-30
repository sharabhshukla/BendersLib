# coding:utf-8

import pytest
import os
from .test_solver_base import BaseTestSolver

try:
    from pyscipopt import Model
    from benderslib.solvers import Scip

    scip_available = True
except ImportError:
    scip_available = False

LP_FILE = os.path.join(os.path.dirname(__file__), "lp.lp")


@pytest.mark.skipif(not scip_available, reason="SCIP is not installed")
class TestScip(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        model = Model()
        model.readProblem(LP_FILE)
        return Scip(model)

    @pytest.fixture
    def infeasible_solver_instance(self):
        model = Model()
        model.readProblem(LP_FILE)
        vars_map = {v.name: v for v in model.getVars(transformed=False)}
        x1 = vars_map["x1"]
        x2 = vars_map["x2"]
        model.addCons(x1 + x2 <= 3)
        return Scip(model)

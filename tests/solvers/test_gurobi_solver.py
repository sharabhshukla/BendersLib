# coding:utf-8

import pytest
import os
from .test_solver_base import BaseTestSolver

try:
    import gurobipy as gp
    from benderslib.solvers import Gurobi

    gurobi_available = True
except ImportError:
    gurobi_available = False

LP_FILE = os.path.join(os.path.dirname(__file__), "lp.lp")


@pytest.mark.skipif(not gurobi_available, reason="Gurobi is not installed")
class TestGurobi(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        model = gp.read(LP_FILE)
        return Gurobi(model)

    @pytest.fixture
    def infeasible_solver_instance(self):
        model = gp.read(LP_FILE)
        x1 = model.getVarByName("x1")
        x2 = model.getVarByName("x2")
        model.addConstr(x1 + x2 <= 3)
        return Gurobi(model)

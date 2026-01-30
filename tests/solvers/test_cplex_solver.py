# coding:utf-8

import pytest
import os
from .test_solver_base import BaseTestSolver

try:
    import cplex
    from benderslib.solvers import Cplex

    cplex_available = True
except ImportError:
    cplex_available = False

LP_FILE = os.path.join(os.path.dirname(__file__), "lp.lp")
print(LP_FILE)


@pytest.mark.skipif(not cplex_available, reason="CPLEX is not installed")
class TestCplexSolver(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        model = cplex.Cplex()
        model.read(LP_FILE)
        return Cplex(model)

    @pytest.fixture
    def infeasible_solver_instance(self):
        model = cplex.Cplex()
        model.read(LP_FILE)

        # c3: x1 + x2 <= 3
        model.linear_constraints.add(
            lin_expr=[[['x1', 'x2'], [1.0, 1.0]]],
            senses=['L'],
            rhs=[3],
            names=['c3']
        )

        return Cplex(model)

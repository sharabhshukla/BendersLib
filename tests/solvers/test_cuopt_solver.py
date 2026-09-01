# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import pytest
from .test_solver_base import BaseTestSolver

try:
    from cuopt.linear_programming.problem import Problem, CONTINUOUS, MINIMIZE
    from benderslib.solvers import Cuopt

    cuopt_available = True
except ImportError:
    cuopt_available = False


def _build_test_problem():
    # Minimizes 3*x1 + 3*x2 s.t. x1 + 2*x2 >= 6, 2*x1 + x2 >= 6, x1, x2 in [0, 100]
    p = Problem("TestLP")
    x1 = p.addVariable(lb=0.0, ub=100.0, vtype=CONTINUOUS, name="x1")
    x2 = p.addVariable(lb=0.0, ub=100.0, vtype=CONTINUOUS, name="x2")
    p.addConstraint(x1 + 2.0 * x2 >= 6.0, name="c1")
    p.addConstraint(2.0 * x1 + x2 >= 6.0, name="c2")
    p.setObjective(3.0 * x1 + 3.0 * x2, sense=MINIMIZE)
    return p


@pytest.mark.skipif(not cuopt_available, reason="cuOpt is not installed")
class TestCuopt(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        problem = _build_test_problem()
        return Cuopt(problem)

    @pytest.fixture
    def infeasible_solver_instance(self):
        problem = _build_test_problem()
        x1 = problem.getVariable("x1")
        x2 = problem.getVariable("x2")
        problem.addConstraint(x1 + x2 <= 3.0, name="c_inf")
        return Cuopt(problem)

    @pytest.fixture
    def unbounded_solver_instance(self):
        p = Problem("UnboundedLP")
        x1 = p.addVariable(lb=0.0, vtype=CONTINUOUS, name="x1")
        x2 = p.addVariable(lb=0.0, vtype=CONTINUOUS, name="x2")
        p.addConstraint(x1 + x2 >= 10.0, name="c1")
        p.setObjective(-1.0 * x1 - 1.0 * x2, sense=MINIMIZE)
        return Cuopt(p)

    def test_compute_iis_for_infeasible(self, infeasible_solver_instance):
        pass

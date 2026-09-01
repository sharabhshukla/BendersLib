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

    def test_batch_solve(self):
        """Test concurrent GPU batch LP solving with Cuopt.batch_solve."""
        from numpy.ma.testutils import approx
        from benderslib import BendersConsts as CST

        # Problem 1: min 3*x1 + 3*x2 s.t. x1 + 2*x2 >= 6, 2*x1 + x2 >= 6 -> obj = 12
        p1 = _build_test_problem()

        # Problem 2: min 2*x + y s.t. x + y >= 10, x, y >= 0 -> obj = 10 (at x=0, y=10)
        p2 = Problem("BatchP2")
        x2 = p2.addVariable(lb=0.0, vtype=CONTINUOUS, name="x")
        y2 = p2.addVariable(lb=0.0, vtype=CONTINUOUS, name="y")
        p2.addConstraint(x2 + y2 >= 10.0, name="c1")
        p2.setObjective(2.0 * x2 + y2, sense=MINIMIZE)

        # Problem 3: min 5*x + 2*y s.t. x >= 4, y >= 3 -> obj = 26
        p3 = Problem("BatchP3")
        x3 = p3.addVariable(lb=4.0, vtype=CONTINUOUS, name="x")
        y3 = p3.addVariable(lb=3.0, vtype=CONTINUOUS, name="y")
        p3.addConstraint(x3 >= 4.0, name="c1")
        p3.addConstraint(y3 >= 3.0, name="c2")
        p3.setObjective(5.0 * x3 + 2.0 * y3, sense=MINIMIZE)

        c1 = Cuopt(p1)
        c2 = Cuopt(p2)
        c3 = Cuopt(p3)

        Cuopt.batch_solve([c1, c2, c3])

        assert c1.status == CST.OPTIMAL
        assert c2.status == CST.OPTIMAL
        assert c3.status == CST.OPTIMAL

        assert approx(c1.get_obj(), 12.0, atol=1e-5)
        assert approx(c2.get_obj(), 10.0, atol=1e-5)
        assert approx(c3.get_obj(), 26.0, atol=1e-5)

    def test_lshaped_stochastic_batch_gpu(self):
        """Test Two-Stage Stochastic L-shaped method with GPU batch subproblems."""
        from benderslib import MasterProblem, SubProblem, SubProblems, LShaped, BendersConsts as CST
        from cuopt.linear_programming.problem import INTEGER

        # First stage (Master Problem): decide capacity x in [0, 50]
        # min 2 * x
        m_prob = Problem("MasterFirstStage")
        x = m_prob.addVariable(lb=0.0, ub=50.0, vtype=INTEGER, name="x")
        m_prob.setObjective(2.0 * x, sense=MINIMIZE)
        master = MasterProblem(Cuopt(m_prob))

        # Second stage (Subproblems for 3 scenarios with demands [10, 20, 30]):
        # Scenario s: min 5 * shortage s.t. shortage >= demand_s - x, shortage >= 0
        demands = [10.0, 20.0, 30.0]
        sub_list = []
        for s, d in enumerate(demands):
            sp = Problem(f"SubStage_{s}")
            x_sub = sp.addVariable(lb=0.0, ub=50.0, vtype=CONTINUOUS, name="x")
            shortage = sp.addVariable(lb=0.0, vtype=CONTINUOUS, name="shortage")
            sp.addConstraint(shortage + x_sub >= d, name=f"demand_c_{s}")
            sp.setObjective(5.0 * shortage, sense=MINIMIZE)
            sub_list.append(SubProblem(Cuopt(sp)))

        sub_problems = SubProblems(sub_list, prob=[1/3, 1/3, 1/3])

        L = LShaped(
            master_problem=master,
            sub_problem=sub_problems,
            complicating_vars=["x"],
        )
        L.params.batch_sub = True
        L.params.multi_optim_cut = True
        L.solve()

        assert L.result.status == CST.OPTIMAL
        assert 0 in L.result.solution
        assert "x" in L.result.solution[0]
        assert round(L.result.solution[0]["x"]) == 20
        assert round(L.result.obj, 2) == 56.67


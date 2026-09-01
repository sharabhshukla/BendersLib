# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import pytest
from .test_solver_base import BaseTestSolver

try:
    from benderslib.solvers import Jaxipm

    jaxipm_available = True
except ImportError:
    jaxipm_available = False


def _build_test_problem() -> dict:
    # Minimizes 3*x1 + 3*x2 s.t. x1 + 2*x2 >= 6, 2*x1 + x2 >= 6, x1, x2 in [0, 100]
    # (same canonical LP used by the other solver backends' tests)
    return {
        "sense": "min",
        "vars": [
            {"name": "x1", "lb": 0.0, "ub": 100.0, "vtype": "C", "obj": 3.0},
            {"name": "x2", "lb": 0.0, "ub": 100.0, "vtype": "C", "obj": 3.0},
        ],
        "constraints": [
            {"name": "c1", "sense": "G", "rhs": 6.0, "coefs": {"x1": 1.0, "x2": 2.0}},
            {"name": "c2", "sense": "G", "rhs": 6.0, "coefs": {"x1": 2.0, "x2": 1.0}},
        ],
    }


@pytest.mark.skipif(not jaxipm_available, reason="jaxipm is not installed")
class TestJaxipm(BaseTestSolver):

    @pytest.fixture
    def solver_instance(self):
        return Jaxipm(_build_test_problem())

    @pytest.fixture
    def infeasible_solver_instance(self):
        problem = _build_test_problem()
        problem["constraints"].append(
            {"name": "c_inf", "sense": "L", "rhs": 3.0, "coefs": {"x1": 1.0, "x2": 1.0}}
        )
        return Jaxipm(problem)

    @pytest.fixture
    def unbounded_solver_instance(self):
        problem = {
            "sense": "min",
            "vars": [
                {"name": "x1", "lb": 0.0, "ub": float("inf"), "vtype": "C", "obj": -1.0},
                {"name": "x2", "lb": 0.0, "ub": float("inf"), "vtype": "C", "obj": -1.0},
            ],
            "constraints": [
                {"name": "c1", "sense": "G", "rhs": 10.0, "coefs": {"x1": 1.0, "x2": 1.0}},
            ],
        }
        return Jaxipm(problem)

    def test_compute_iis_for_infeasible(self, infeasible_solver_instance):
        pass

    def test_make_master_problem(self, solver_instance):
        from benderslib.errors import BendersNotImplementedError
        with pytest.raises(BendersNotImplementedError):
            solver_instance.make_master_problem(solver_instance.model, ["x1"])

    def test_to_from_structured_roundtrip(self, solver_instance):
        structured = solver_instance.to_structured()
        rebuilt = Jaxipm.from_structured(structured)
        rebuilt_solver = Jaxipm(rebuilt)

        rebuilt_solver.solve()
        assert rebuilt_solver.status == "OPTIMAL"

    def test_batch_solve(self):
        """Batches two identical-structure instances differing only in the fixed x1 value."""
        from numpy.ma.testutils import approx

        inst1 = Jaxipm(_build_test_problem())
        inst2 = Jaxipm(_build_test_problem())

        inst1.fix_vars({"x1": 1.0})
        inst2.fix_vars({"x1": 4.0})

        Jaxipm.batch_solve([inst1, inst2])

        assert inst1.status == "OPTIMAL"
        assert inst2.status == "OPTIMAL"
        assert approx(inst1.get_var_values(["x1"])["x1"], 1.0, atol=1e-4)
        assert approx(inst2.get_var_values(["x1"])["x1"], 4.0, atol=1e-4)

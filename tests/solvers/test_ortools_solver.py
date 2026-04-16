# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import pytest
from .test_solver_base import BaseTestCPSolver

try:
    from ortools.linear_solver import pywraplp
    from benderslib.solvers import Ortools

    ortools_available = True
except ImportError:
    ortools_available = False


@pytest.mark.skipif(not ortools_available, reason="OrTools is not installed")
class TestOrtools(BaseTestCPSolver):

    @pytest.fixture
    def solver_instance(self):
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()

        # Below is an equivalent CP formulation of "lp.lp"
        x1 = model.NewIntVar(0, 100, 'x1')
        x2 = model.NewIntVar(0, 100, 'x2')
        c1_active = model.NewBoolVar("c1_active")
        c2_active = model.NewBoolVar("c2_active")

        model.Add(x1 + 2 * x2 >= 6).OnlyEnforceIf(c1_active)
        model.Add(2 * x1 + x2 >= 6).OnlyEnforceIf(c2_active)

        model.AddAssumptions([c1_active, c2_active])

        model.Minimize(3 * x1 + 3 * x2)

        vars_map = {
            'x1': x1,
            'x2': x2,
            'c1_active': c1_active,
            'c2_active': c2_active
        }

        cons_vars = {
            c1_active: ['x1', 'x2'],
            c2_active: ['x1', 'x2']
        }

        return Ortools(model, vars_map, cons_vars)

    @pytest.fixture
    def infeasible_solver_instance(self):
        from ortools.sat.python import cp_model
        model = cp_model.CpModel()

        # Below is an equivalent CP formulation of "lp.lp"
        x1 = model.NewIntVar(0, 100, 'x1')
        x2 = model.NewIntVar(0, 100, 'x2')
        c1_active = model.NewBoolVar("c1_active")
        c2_active = model.NewBoolVar("c2_active")
        c3_active = model.NewBoolVar("c3_active")

        model.Add(x1 + 2 * x2 >= 6).OnlyEnforceIf(c1_active)
        model.Add(2 * x1 + x2 >= 6).OnlyEnforceIf(c2_active)
        # Intentional infeasibility
        model.Add(x1 + x2 <= 3).OnlyEnforceIf(c3_active)

        model.AddAssumptions([c1_active, c2_active, c3_active])

        model.Minimize(3 * x1 + 3 * x2)

        vars_map = {
            'x1': x1,
            'x2': x2,
            'c1_active': c1_active,
            'c2_active': c2_active,
            'c3_active': c3_active
        }

        cons_vars = {
            c1_active: ['x1', 'x2'],
            c2_active: ['x1', 'x2'],
            c3_active: ['x1', 'x2']
        }

        return Ortools(model, vars_map, cons_vars)

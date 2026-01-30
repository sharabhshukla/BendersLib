# coding:utf-8

import pytest
from .test_solver_base import BaseTestCPSolver

try:
    from docplex.cp.model import CpoModel
    from benderslib.solvers import CplexCP

    cplexcp_available = True
except ImportError:
    cplexcp_available = False


@pytest.mark.skipif(not cplexcp_available, reason="CPLEX CP is not installed")
class TestCplexCP(BaseTestCPSolver):

    @pytest.fixture
    def solver_instance(self):
        model = CpoModel()

        # Below is an equivalent CP formulation of "lp.lp"
        x1 = model.integer_var(min=0, max=100, name='x1')
        x2 = model.integer_var(min=0, max=100, name='x2')

        model.add((x1 + 2 * x2 >= 6).set_name('c1'))
        model.add((2 * x1 + x2 >= 6).set_name('c2'))

        model.minimize(3 * x1 + 3 * x2)

        vars_map = {
            'x1': x1,
            'x2': x2
        }

        cons_vars = {
            'c1': ['x1', 'x2'],
            'c2': ['x1', 'x2']
        }

        return CplexCP(model, vars_map, cons_vars)

    @pytest.fixture
    def infeasible_solver_instance(self):
        model = CpoModel()

        # Below is an equivalent CP formulation of "lp.lp"
        x1 = model.integer_var(min=0, max=100, name='x1')
        x2 = model.integer_var(min=0, max=100, name='x2')

        model.add((x1 + 2 * x2 >= 6).set_name('c1'))
        model.add((2 * x1 + x2 >= 6).set_name('c2'))
        # Intentional infeasibility
        model.add((x1 + x2 <= 3).set_name('c3'))

        model.minimize(3 * x1 + 3 * x2)

        vars_map = {
            'x1': x1,
            'x2': x2
        }

        cons_vars = {
            'c1': ['x1', 'x2'],
            'c2': ['x1', 'x2'],
            'c3': ['x1', 'x2']
        }

        return CplexCP(model, vars_map, cons_vars)

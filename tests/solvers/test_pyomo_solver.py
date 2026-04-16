# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import pytest
from .test_solver_base import BaseTestSolver

try:
    import pyomo.environ as pyo
    from benderslib.solvers import Pyomo

    pyomo_available = True
except ImportError:
    pyomo_available = False

solvers = [
    'cbc',
    'cplex',
    'cplex_direct',
    'glpk',
    'gurobi',
    'gurobi_direct',
    'highs',
    'xpress',
    'xpress_direct',

    # 'mosek',        # License expires in one month
    # 'mosek_direct', # License expires in one month
    # 'scip',         # Unable to obtain correct dual values
]


def is_solver_available(solver):
    try:
        return pyo.SolverFactory(solver).available()
    except:
        return False


def create_pyomo_model():
    # Below is an equivalent formulation of "lp.lp"
    model = pyo.ConcreteModel()
    model.x1 = pyo.Var(bounds=(0, 100))
    model.x2 = pyo.Var(bounds=(0, 100))
    model.obj = pyo.Objective(expr=3 * model.x1 + 3 * model.x2, sense=pyo.minimize)
    model.c1 = pyo.Constraint(expr=model.x1 + 2 * model.x2 >= 6)
    model.c2 = pyo.Constraint(expr=2 * model.x1 + model.x2 >= 6)
    return model


def create_ubd_pyomo_model():
    # Below is an equivalent formulation of "lp_ubd.lp"
    model = pyo.ConcreteModel()
    model.x = pyo.Var(bounds=(0, None))
    model.y = pyo.Var(bounds=(0, None))
    model.obj = pyo.Objective(expr=-model.x - model.y, sense=pyo.minimize)
    model.c1 = pyo.Constraint(expr=model.x - model.y <= 1)
    model.c2 = pyo.Constraint(expr=-model.x + model.y <= 1)
    return model


@pytest.mark.parametrize("solver", solvers)
@pytest.mark.skipif(not pyomo_available, reason="Pyomo is not installed")
class TestPyomo(BaseTestSolver):

    @pytest.fixture(autouse=True)
    def skip_if_solver_not_available(self, solver):
        if not is_solver_available(solver):
            pytest.skip(f"Solver {solver} is not available")

    @pytest.fixture
    def solver_instance(self, solver):
        model = create_pyomo_model()
        return Pyomo(model, solver=solver)

    @pytest.fixture
    def infeasible_solver_instance(self, solver):
        model = create_pyomo_model()
        model.c3 = pyo.Constraint(expr=model.x1 + model.x2 <= 3)
        return Pyomo(model, solver=solver)

    @pytest.mark.skip(reason="The Pyomo interface cannot obtain extreme rays.")
    def test_get_extreme_ray(self, infeasible_solver_instance):
        pass

    @pytest.mark.skip(reason="The Pyomo interface cannot obtain IIS.")
    def test_compute_iis_for_infeasible(self, infeasible_solver_instance):
        pass

    def test_get_dual_values(self, solver_instance):
        if solver_instance._Pyomo__solver_name == 'scip':
            pytest.skip("Pyomo(m, solver='scip') is unable to obtain correct dual values as documented.")
        super().test_get_dual_values(solver_instance)

    @pytest.fixture
    def unbounded_solver_instance(self, solver):
        model = create_ubd_pyomo_model()
        return Pyomo(model, solver=solver)

    def test_unbounded_solution(self, unbounded_solver_instance):
        if unbounded_solver_instance._Pyomo__solver_name == 'glpk':
            pytest.skip("GLPK returns unexpected status 'other'.")

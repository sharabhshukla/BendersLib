# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""Tests for the cross-backend model exchange API (to_structured/from_structured),
SubProblems.from_models(), and AnnotatedBenders(master_solver=/sub_solver=).

All tests build the same small MILP:
    min 3*x + 4*y  s.t.  x + y >= 15,  2*x + 5*y >= 30,  x in {0, 1}, y >= 0
whose known optimum is x=1, y=14, obj=59 (x=0 forces y=15 -> obj=60).
"""

import pytest

from benderslib import BendersConsts as CST

try:
    from cuopt.linear_programming.problem import Problem as CuoptProblem
    from benderslib.solvers import Cuopt

    cuopt_available = True
except ImportError:
    cuopt_available = False

try:
    import gurobipy as gp
    from gurobipy import GRB
    from benderslib.solvers import Gurobi

    gurobi_available = True
except ImportError:
    gurobi_available = False

try:
    import coptpy as cp
    from coptpy import COPT
    from benderslib.solvers import Copt

    copt_available = True
except ImportError:
    copt_available = False

try:
    import pyomo.environ as pyo
    from benderslib.solvers import Pyomo

    pyomo_available = True
except Exception:
    # Some Pyomo releases ship a solver plugin that crashes with a NameError if cuopt is
    # already imported (a known Pyomo bug, unrelated to BendersLib); treat as unavailable.
    pyomo_available = False

try:
    from pyscipopt import Model as ScipModel
    from benderslib.solvers import Scip

    scip_available = True
except ImportError:
    scip_available = False


def _assert_expected_optimum(cuopt_model: 'CuoptProblem'):
    """Solve the converted cuOpt model and check it matches the known optimum (obj=59, x=1)."""
    c = Cuopt(cuopt_model)
    c.solve()
    assert c.status == CST.OPTIMAL
    assert round(c.get_obj(), 4) == 59.0
    vals = c.get_var_values(["x"])
    assert round(vals["x"], 5) == 1.0


@pytest.mark.skipif(not (cuopt_available and gurobi_available), reason="cuOpt or Gurobi is not installed")
def test_gurobi_to_cuopt_exchange():
    """to_structured/from_structured exchange: Gurobi (source) -> cuOpt (target)."""
    m = gp.Model()
    x = m.addVar(lb=0.0, ub=1.0, vtype=GRB.INTEGER, name="x")
    y = m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="y")
    m.addConstr(x + y >= 15.0, name="c1")
    m.addConstr(2.0 * x + 5.0 * y >= 30.0, name="c2")
    m.setObjective(3.0 * x + 4.0 * y, GRB.MINIMIZE)
    m.update()

    structured = Gurobi(m).to_structured()
    cuopt_model = Cuopt.from_structured(structured)
    _assert_expected_optimum(cuopt_model)


@pytest.mark.skipif(not (cuopt_available and copt_available), reason="cuOpt or COPT is not installed")
def test_copt_to_cuopt_exchange():
    """to_structured/from_structured exchange: COPT (source) -> cuOpt (target)."""
    env = cp.Envr()
    m = env.createModel("HybridExchange")
    x = m.addVar(lb=0.0, ub=1.0, vtype=COPT.INTEGER, name="x")
    y = m.addVar(lb=0.0, vtype=COPT.CONTINUOUS, name="y")
    m.addConstr(x + y >= 15.0, name="c1")
    m.addConstr(2.0 * x + 5.0 * y >= 30.0, name="c2")
    m.setObjective(3.0 * x + 4.0 * y, sense=COPT.MINIMIZE)

    structured = Copt(m).to_structured()
    cuopt_model = Cuopt.from_structured(structured)
    _assert_expected_optimum(cuopt_model)


@pytest.mark.skipif(not (cuopt_available and pyomo_available), reason="cuOpt or Pyomo is not installed")
def test_pyomo_to_cuopt_exchange():
    """to_structured/from_structured exchange: Pyomo (source) -> cuOpt (target)."""
    m = pyo.ConcreteModel()
    m.x = pyo.Var(bounds=(0, 1), within=pyo.Integers)
    m.y = pyo.Var(bounds=(0, None), within=pyo.Reals)
    m.c1 = pyo.Constraint(expr=m.x + m.y >= 15.0)
    m.c2 = pyo.Constraint(expr=2.0 * m.x + 5.0 * m.y >= 30.0)
    m.obj = pyo.Objective(expr=3.0 * m.x + 4.0 * m.y, sense=pyo.minimize)

    structured = Pyomo(m, solver='gurobi').to_structured()
    cuopt_model = Cuopt.from_structured(structured)
    _assert_expected_optimum(cuopt_model)


@pytest.mark.skipif(not (cuopt_available and scip_available), reason="cuOpt or SCIP is not installed")
def test_scip_to_cuopt_exchange():
    """to_structured/from_structured exchange: SCIP (source) -> cuOpt (target)."""
    m = ScipModel("HybridExchange")
    x = m.addVar(lb=0.0, ub=1.0, vtype="INTEGER", name="x")
    y = m.addVar(lb=0.0, vtype="CONTINUOUS", name="y")
    m.addCons(x + y >= 15.0, name="c1")
    m.addCons(2.0 * x + 5.0 * y >= 30.0, name="c2")
    m.setObjective(3.0 * x + 4.0 * y, "minimize")

    structured = Scip(m).to_structured()
    cuopt_model = Cuopt.from_structured(structured)
    _assert_expected_optimum(cuopt_model)


@pytest.mark.skipif(
    not (cuopt_available and gurobi_available and scip_available),
    reason="cuOpt, Gurobi, or SCIP is not installed",
)
def test_subproblems_from_models_batch():
    """SubProblems.from_models(): build scenario LPs in Gurobi, batch-solve via cuOpt."""
    from benderslib import MasterProblem, SubProblems, LShaped

    # Master problem (SCIP MILP): decide capacity x in [0, 50], min 2*x
    m_prob = ScipModel("MasterFirstStage")
    x = m_prob.addVar(lb=0.0, ub=50.0, vtype="INTEGER", name="x")
    m_prob.setObjective(2.0 * x, "minimize")
    master = MasterProblem(Scip(m_prob))

    # Scenario subproblems built with GUROBI: min 5*shortage s.t. shortage + x >= d, shortage >= 0
    demands = [10.0, 20.0, 30.0]
    sub_models = []
    for s, d in enumerate(demands):
        sp = gp.Model()
        x_sub = sp.addVar(lb=0.0, ub=50.0, vtype=GRB.CONTINUOUS, name="x")
        shortage = sp.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="shortage")
        sp.addConstr(shortage + x_sub >= d, name=f"demand_c_{s}")
        sp.setObjective(5.0 * shortage, GRB.MINIMIZE)
        sp.update()
        sub_models.append(sp)

    sub_problems = SubProblems.from_models(
        sub_models, solver=Gurobi, batch_solver=Cuopt, prob=[1 / 3, 1 / 3, 1 / 3],
    )

    # batch_sub should be auto-enabled since a conversion happened
    assert sub_problems.params.batch_sub is True
    # each subproblem should now be backed by Cuopt after conversion
    assert all(sp.solver.__class__.__name__ == "Cuopt" for sp in sub_problems.sub_problems)

    L = LShaped(
        master_problem=master,
        sub_problem=sub_problems,
        complicating_vars=["x"],
    )
    L.params.multi_optim_cut = True
    L.solve()

    assert L.result.status == CST.OPTIMAL
    assert 0 in L.result.solution
    assert "x" in L.result.solution[0]
    assert round(L.result.solution[0]["x"]) == 20
    assert round(L.result.obj, 2) == 56.67


@pytest.mark.skipif(
    not (cuopt_available and scip_available),
    reason="cuOpt or SCIP is not installed",
)
def test_subproblems_from_models_batch_scip_models():
    """SubProblems.from_models(): pyscipopt-built scenario LPs batch-solved via cuOpt."""
    from benderslib import MasterProblem, SubProblems, LShaped

    # Master problem (SCIP MILP): decide capacity x in [0, 50], min 2*x
    m_prob = ScipModel("MasterFirstStage")
    x = m_prob.addVar(lb=0.0, ub=50.0, vtype="INTEGER", name="x")
    m_prob.setObjective(2.0 * x, "minimize")
    master = MasterProblem(Scip(m_prob))

    # Scenario subproblems built with PYSCIPOPT: min 5*shortage s.t. shortage + x >= d
    demands = [10.0, 20.0, 30.0]
    sub_models = []
    for s, d in enumerate(demands):
        sp = ScipModel(f"SubStage_{s}")
        x_sub = sp.addVar(lb=0.0, ub=50.0, vtype="CONTINUOUS", name="x")
        shortage = sp.addVar(lb=0.0, vtype="CONTINUOUS", name="shortage")
        sp.addCons(shortage + x_sub >= d, name=f"demand_c_{s}")
        sp.setObjective(5.0 * shortage, "minimize")
        sub_models.append(sp)

    sub_problems = SubProblems.from_models(
        sub_models, solver=Scip, batch_solver=Cuopt, prob=[1 / 3, 1 / 3, 1 / 3],
    )

    # batch_sub should be auto-enabled since a conversion happened
    assert sub_problems.params.batch_sub is True
    # each subproblem should now be backed by Cuopt after conversion
    assert all(sp.solver.__class__.__name__ == "Cuopt" for sp in sub_problems.sub_problems)

    L = LShaped(
        master_problem=master,
        sub_problem=sub_problems,
        complicating_vars=["x"],
    )
    L.params.multi_optim_cut = True
    L.solve()

    assert L.result.status == CST.OPTIMAL
    assert 0 in L.result.solution
    assert "x" in L.result.solution[0]
    assert round(L.result.solution[0]["x"]) == 20
    assert round(L.result.obj, 2) == 56.67


@pytest.mark.skipif(not (cuopt_available and gurobi_available), reason="cuOpt or Gurobi is not installed")
def test_annotated_benders_sub_solver():
    """AnnotatedBenders sub_solver API: Gurobi master + cuOpt subproblem."""
    from benderslib import AnnotatedBenders, ClassicalBenders

    m = gp.Model()
    x = m.addVar(lb=0.0, ub=1.0, vtype=GRB.INTEGER, name="x")
    y = m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="y")
    m.addConstr(x + y >= 15.0, name="c1")
    m.addConstr(2.0 * x + 5.0 * y >= 30.0, name="c2")
    m.setObjective(3.0 * x + 4.0 * y, GRB.MINIMIZE)
    m.update()

    BD = AnnotatedBenders(
        m,
        solver=Gurobi,
        sub_solver=Cuopt,
        complicating_vars=["x"],
        benders=ClassicalBenders,
    )

    assert BD.sub_problem.solver.__class__.__name__ == "Cuopt"

    BD.solve()

    assert BD.result.status == CST.OPTIMAL
    assert round(BD.result.obj, 2) == 59.0
    assert round(BD.result.solution["x"], 5) == 1.0

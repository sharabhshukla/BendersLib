# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
SCIP Models, Batched GPU Subproblems: L-shaped Method via cuOpt
===================================================

This example solves a Two-Stage Stochastic Program with 50 scenarios using the
L-shaped method, with **all models built using the pyscipopt API**:

- **Master problem (MILP)**: a native pyscipopt model, solved by SCIP on the CPU.
- **Scenario subproblems (LPs)**: native pyscipopt models, converted to cuOpt via the
  cross-backend model exchange and **solved together in a single GPU batch**
  (see :meth:`~benderslib.SubProblems.from_models`).

This demonstrates that GPU batch LP solving does not require modeling in cuOpt's
native API — any backend implementing
:meth:`~benderslib.solvers.SolverBase.to_structured` (Gurobi, COPT, Pyomo, SCIP)
can supply the subproblems.

.. note::
    cuOpt's ``BatchSolve`` is deprecated upstream by NVIDIA (see
    :attr:`~benderslib.BendersParams.batch_sub`); only the subproblem side relies on it.
"""

import random

from benderslib import MasterProblem, SubProblems, LShaped
from benderslib.solvers import Cuopt, Scip
from benderslib.utils import draw_curve

try:
    from pyscipopt import Model as ScipModel
    scip_available = True
except ImportError:
    scip_available = False

try:
    import cuopt.linear_programming  # noqa: F401 -- availability check only
    cuopt_available = True
except ImportError:
    cuopt_available = False


def first_stage_model(n_plants):
    """Build master problem (pyscipopt model): decide plant capacities (MIP)."""
    model = ScipModel("FirstStage")
    caps = [model.addVar(lb=0.0, ub=100.0, vtype="INTEGER", name=f"cap_{i}") for i in range(n_plants)]
    model.setObjective(sum(caps), "minimize")
    return model, [f"cap_{i}" for i in range(n_plants)]


def second_stage_models(n_plants, scenarios):
    """Build one pyscipopt LP subproblem per stochastic scenario."""
    sub_models = []
    for s, demand in enumerate(scenarios):
        model = ScipModel(f"Sub_{s}")
        caps = [model.addVar(lb=0.0, ub=100.0, vtype="CONTINUOUS", name=f"cap_{i}") for i in range(n_plants)]
        shortages = [model.addVar(lb=0.0, vtype="CONTINUOUS", name=f"shortage_{i}") for i in range(n_plants)]

        for i in range(n_plants):
            model.addCons(shortages[i] + caps[i] >= demand[i], name=f"demand_{s}_{i}")

        # Minimize shortage cost (penalty = 5.0)
        model.setObjective(5.0 * sum(shortages), "minimize")
        sub_models.append(model)

    return sub_models


if __name__ == '__main__':
    if scip_available and cuopt_available:
        random.seed(42)
        n_plants = 4
        n_scenarios = 50
        scenarios = [[random.randint(10, 80) for _ in range(n_plants)] for _ in range(n_scenarios)]
        probs = [1.0 / n_scenarios] * n_scenarios

        # Master problem: native pyscipopt model, solved by SCIP (CPU)
        master_model, complicating_vars = first_stage_model(n_plants)
        master_problem = MasterProblem(Scip(master_model))

        # Scenario subproblems: pyscipopt models converted to cuOpt and batched on the GPU
        sub_models = second_stage_models(n_plants, scenarios)
        sub_problems = SubProblems.from_models(
            sub_models,
            solver=Scip,          # the models are in pyscipopt format
            batch_solver=Cuopt,   # convert & solve all scenario LPs in one GPU batch
            prob=probs,
        )  # params.batch_sub = True is set automatically

        # L-shaped method: CPU master + batched GPU LP subproblems
        L = LShaped(
            master_problem=master_problem,
            sub_problem=sub_problems,
            complicating_vars=complicating_vars,
        )
        L.params.multi_optim_cut = True
        L.solve()

        print(f"Optimal Objective: {L.result.obj:.4f}")
        print(f"Optimal Capacities: {L.result.solution}")
        draw_curve(L.result)

# %%
#
# .. tags:: benders: l-shaped, solver: scip, solver: cuopt, gpu, batch-lp, stochastic

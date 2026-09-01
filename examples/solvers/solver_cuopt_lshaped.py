# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
NVIDIA cuOpt: Hybrid L-shaped Method (SCIP Master MILP + Batched GPU LP Subproblems)
===================================================

This example solves a Two-Stage Stochastic Program with 50 scenarios using the L-shaped
method, in BendersLib's **recommended way of using cuOpt** — a *hybrid* architecture:

- **Master problem (MILP)**: solved by `SCIP <https://www.scipopt.org>`_ on the CPU.
  The master is a small integer program that is re-solved every iteration; a CPU MIP
  solver handles this far better than cuOpt, which pays a large fixed cost per MIP
  solve (presolve, early heuristics, post-solve reconstruction).
- **Subproblems (LPs)**: all 50 scenario LPs are dispatched **together** to cuOpt via
  its ``BatchSolve`` API (see :attr:`~benderslib.BendersParams.batch_sub`), amortizing
  the GPU dispatch cost across the whole scenario set.

BendersLib natively supports mixing solver backends: the master and the subproblems
each take their own :class:`~benderslib.solvers.SolverBase` backend. For single-problem
workflows, :class:`~benderslib.AnnotatedBenders` exposes the same idea through its
``master_solver`` parameter.

If pyscipopt is not installed, the example falls back to a pure-cuOpt master, which is
correct but considerably slower.

.. note::
    ``BatchSolve`` is deprecated upstream by NVIDIA (see
    :attr:`~benderslib.BendersParams.batch_sub`); only the LP subproblem side relies on it.
"""

import random

from benderslib import MasterProblem, SubProblem, SubProblems, LShaped
from benderslib.solvers import Cuopt
from benderslib.utils import draw_curve

try:
    from pyscipopt import Model as ScipModel
    from benderslib.solvers import Scip
    scip_available = True
except ImportError:
    scip_available = False

try:
    from cuopt.linear_programming.problem import Problem, CONTINUOUS, MINIMIZE
    cuopt_available = True
except ImportError:
    cuopt_available = False


def first_stage_model(n_plants, backend='scip'):
    """Build master problem: decide plant capacities (MIP)."""
    if backend == 'scip':
        model = ScipModel("FirstStage")
        caps = [model.addVar(lb=0.0, ub=100.0, vtype="INTEGER", name=f"cap_{i}") for i in range(n_plants)]
        model.setObjective(sum(caps), "minimize")
    else:
        from cuopt.linear_programming.problem import INTEGER
        model = Problem("FirstStage")
        caps = [model.addVariable(lb=0.0, ub=100.0, vtype=INTEGER, name=f"cap_{i}") for i in range(n_plants)]
        model.setObjective(sum(caps), sense=MINIMIZE)
    return model, [f"cap_{i}" for i in range(n_plants)]


def second_stage_models(n_plants, scenarios):
    """Build cuOpt LP subproblem for each stochastic scenario."""
    sub_problems = []
    for s, demand in enumerate(scenarios):
        model = Problem(f"Sub_{s}")
        caps = [model.addVariable(lb=0.0, ub=100.0, vtype=CONTINUOUS, name=f"cap_{i}") for i in range(n_plants)]
        shortages = [model.addVariable(lb=0.0, vtype=CONTINUOUS, name=f"shortage_{i}") for i in range(n_plants)]

        for i in range(n_plants):
            model.addConstraint(shortages[i] + caps[i] >= demand[i], name=f"demand_{s}_{i}")

        # Minimize shortage cost (penalty = 5.0)
        model.setObjective(sum(5.0 * shortages[i] for i in range(n_plants)), sense=MINIMIZE)
        sub_problems.append(SubProblem(Cuopt(model)))

    return sub_problems


if __name__ == '__main__':
    if cuopt_available:
        random.seed(42)
        n_plants = 4
        n_scenarios = 50
        scenarios = [[random.randint(10, 80) for _ in range(n_plants)] for _ in range(n_scenarios)]
        probs = [1.0 / n_scenarios] * n_scenarios

        # Master problem: SCIP MILP backend (recommended), falling back to cuOpt
        master_backend = 'scip' if scip_available else 'cuopt'
        master_model, complicating_vars = first_stage_model(n_plants, backend=master_backend)
        master_solver_cls = Scip if scip_available else Cuopt
        master_problem = MasterProblem(master_solver_cls(master_model))

        # Scenario subproblems: cuOpt LP backend, solved in one batch
        sub_list = second_stage_models(n_plants, scenarios)
        sub_problems = SubProblems(sub_list, prob=probs)

        # L-shaped method: CPU master + batched GPU LP subproblems
        L = LShaped(
            master_problem=master_problem,
            sub_problem=sub_problems,
            complicating_vars=complicating_vars,
        )
        L.params.batch_sub = True  # All scenario LPs dispatched together via cuOpt BatchSolve
        L.params.multi_optim_cut = True
        L.solve()

        print(f"Optimal Objective: {L.result.obj:.4f}")
        print(f"Optimal Capacities: {L.result.solution}")
        draw_curve(L.result)

# %%
#
# .. tags:: benders: l-shaped, solver: cuopt, solver: scip, gpu, batch-lp, stochastic

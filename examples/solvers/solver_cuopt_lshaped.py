# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
NVIDIA cuOpt: GPU Batch LP L-shaped Method
===================================================

This example solves a Two-Stage Stochastic Program with 100 scenarios using
the L-shaped method. All 100 scenario LP subproblems are solved concurrently on
the GPU in a single batched CUDA kernel execution via cuOpt BatchSolve.
"""

import random

from benderslib import MasterProblem, SubProblem, SubProblems, LShaped
from benderslib.solvers import Cuopt
from benderslib.utils import draw_curve

try:
    from cuopt.linear_programming.problem import Problem, CONTINUOUS, INTEGER, MINIMIZE
    cuopt_available = True
except ImportError:
    cuopt_available = False


def first_stage_model(n_plants):
    """Build master problem: decide plant capacities (MIP)."""
    model = Problem("FirstStage")
    caps = []
    for i in range(n_plants):
        caps.append(model.addVariable(lb=0.0, ub=100.0, vtype=INTEGER, name=f"cap_{i}"))

    # Minimize sum of installation costs
    model.setObjective(sum(caps), sense=MINIMIZE)
    complicating_vars = [f"cap_{i}" for i in range(n_plants)]
    return model, complicating_vars


def second_stage_models(n_plants, scenarios):
    """Build LP subproblem for each stochastic scenario."""
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

        # Master problem
        master_model, complicating_vars = first_stage_model(n_plants)
        master_problem = MasterProblem(Cuopt(master_model))

        # Scenario subproblems
        sub_list = second_stage_models(n_plants, scenarios)
        sub_problems = SubProblems(sub_list, prob=probs)

        # L-shaped method with GPU BatchSolve enabled
        L = LShaped(
            master_problem=master_problem,
            sub_problem=sub_problems,
            complicating_vars=complicating_vars,
        )
        L.params.batch_sub = True  # Enable GPU batch LP solving for subproblems
        L.params.multi_optim_cut = True
        L.solve()

        print(f"Optimal Objective: {L.result.obj:.4f}")
        print(f"Optimal Capacities: {L.result.solution}")
        draw_curve(L.result)

# %%
#
# .. tags:: benders: l-shaped, solver: cuopt, gpu, batch-lp, stochastic

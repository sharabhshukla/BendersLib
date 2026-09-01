# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
NVIDIA cuOpt (Hybrid: CPU Master + GPU Subproblems)
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Cuopt` as a **subproblem** backend on GPU, paired
# with a CPU MIP backend (SCIP) for the master problem via the ``master_solver``
# parameter of :class:`~benderslib.AnnotatedBenders`.
#
# This is BendersLib's recommended way of using cuOpt: the master MILP is re-solved
# every Benders iteration and is best handled by a CPU MIP solver, while cuOpt's
# strength — fast LP solving on the GPU — is used for the subproblems.

from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Cuopt
from benderslib.utils import draw_curve

try:
    from cuopt.linear_programming.problem import Problem, CONTINUOUS, INTEGER, MINIMIZE
    cuopt_available = True
except ImportError:
    cuopt_available = False

try:
    from benderslib.solvers import Scip
    scip_available = True
except ImportError:
    scip_available = False


def make_original_problem():
    """Build a sample MILP model using native cuOpt Python API."""
    problem = Problem("BendersExample")

    # Master complicating variable (Binary)
    x1 = problem.addVariable(lb=0.0, ub=1.0, vtype=INTEGER, name="x1")

    # Subproblem continuous variables
    x2 = problem.addVariable(lb=2.0, vtype=CONTINUOUS, name="x2")
    x3 = problem.addVariable(lb=2.0, vtype=CONTINUOUS, name="x3")

    # Constraints
    problem.addConstraint(x1 + x2 + x3 >= 20.0, name="c1")
    problem.addConstraint(x1 - 3.0 * x2 + x3 <= 30.0, name="c2")
    problem.addConstraint(x2 - 3.5 * x3 == 0.0, name="c3")

    # Objective: Minimize x1 + x2 + x3
    problem.setObjective(x1 + x2 + x3, sense=MINIMIZE)

    complicating_vars = ["x1"]
    return problem, complicating_vars


if __name__ == '__main__':
    if cuopt_available:
        problem, complicating_vars = make_original_problem()

        BD = AnnotatedBenders(
            problem,
            solver=Cuopt,
            master_solver=Scip if scip_available else None,  # Recommended: CPU master (SCIP)
            complicating_vars=complicating_vars,
            benders=ClassicalBenders
        )
        BD.solve()

        draw_curve(BD.result)

# %%
#
# .. tags:: benders: classical, solver: cuopt, gpu, deterministic

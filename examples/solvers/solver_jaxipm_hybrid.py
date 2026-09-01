# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
jaxipm (Hybrid: Gurobi/COPT/SCIP/Pyomo Master + GPU Subproblem)
=======================================

"""

# %%
# This is the recommended way to use :class:`~benderslib.solvers.Jaxipm`: model the
# **overall problem** (and its master problem) in whichever general-purpose tool you already
# use -- :class:`~benderslib.solvers.Gurobi`, :class:`~benderslib.solvers.Copt`,
# :class:`~benderslib.solvers.Scip`, or :class:`~benderslib.solvers.Pyomo` -- and indicate,
# via the ``sub_solver`` parameter of :class:`~benderslib.AnnotatedBenders`, that the
# **subproblem** specifically should be solved by jaxipm on the GPU.
#
# jaxipm only supports continuous ("nice LP") problems, so it is never used for the master
# problem; the master's MIP is solved by ``solver`` as usual. Behind the scenes,
# :meth:`AnnotatedBenders.decompose` converts the subproblem from ``solver``'s native format
# to jaxipm's via the cross-backend model exchange
# (:meth:`~benderslib.solvers.SolverBase.to_structured` /
# :meth:`~benderslib.solvers.SolverBase.from_structured`), so no manual conversion is needed.

from pathlib import Path
import inspect

from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Gurobi, Jaxipm
from benderslib.utils import draw_curve

from gurobipy import GRB
import gurobipy as gp

try:
    import jaxipm as _jaxipm
    jaxipm_available = True
except ImportError:
    jaxipm_available = False


def make_original_problem():
    # Same model as examples/solvers/solver_gurobi.py: x1 is the only (binary) complicating
    # variable; x2, x3 are continuous and form the LP subproblem once x1 is fixed.
    current_file_path = inspect.getfile(inspect.currentframe())
    lp_file_path = Path(current_file_path).parent / "m.lp"
    model = gp.read(str(lp_file_path))

    complicating_vars = [v.VarName for v in model.getVars() if v.VType != GRB.CONTINUOUS]
    return model, complicating_vars


if __name__ == '__main__':
    if jaxipm_available:
        model, complicating_vars = make_original_problem()

        BD = AnnotatedBenders(
            model,
            solver=Gurobi,        # overall problem / master problem: Gurobi
            sub_solver=Jaxipm,    # subproblem: jaxipm (GPU interior-point)
            complicating_vars=complicating_vars,
            benders=ClassicalBenders,
        )
        BD.solve()

        draw_curve(BD.result)

# %%
#
# .. tags:: benders: classical, solver: jaxipm, gpu, deterministic

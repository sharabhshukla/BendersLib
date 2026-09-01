# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
jaxipm
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Jaxipm` directly, on a "nice LP" subproblem model.
#
# Unlike the other backends, jaxipm has no native model-building API (it is a functional
# GPU interior-point solver, not an algebraic modeling library), so its native model is a
# solver-agnostic **structured dict** -- see :class:`~benderslib.solvers.Jaxipm` for the format.
# jaxipm only supports continuous problems, so it can only be used as a **subproblem** backend.

from benderslib.solvers import Jaxipm

try:
    import jaxipm as _jaxipm
    jaxipm_available = True
except ImportError:
    jaxipm_available = False


def make_sub_problem() -> dict:
    # Minimize 3*x1 + 3*x2 s.t. x1 + 2*x2 >= 6, 2*x1 + x2 >= 6, x1, x2 in [0, 100]
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


if __name__ == '__main__':
    if jaxipm_available:
        sub = Jaxipm(make_sub_problem())
        sub.solve()

        print("Status:", sub.status)
        print("Objective:", sub.get_obj())
        print("Solution:", sub.get_var_values())
        print("Dual values:", sub.get_dual_values())

# %%
#
# .. tags:: solver: jaxipm, gpu

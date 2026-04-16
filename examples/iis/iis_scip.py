# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

"""
SCIP IIS
=======================================

.. currentmodule:: benderslib.solvers

"""

# %%
# Using :meth:`Scip.compute_iis` to compute conflicting variables.


from benderslib.solvers import Scip

import pyscipopt as scip


def make_sub_problem():
    model = scip.Model(problemName='InfeasibleExample')

    x = model.addVar(vtype='I', name='x')
    y = model.addVar(vtype='I', name='y')
    z = model.addVar(vtype='I', name='z')

    model.addCons(x + y >= 9)
    model.addCons(x + y <= 1)

    return model


if __name__ == '__main__':
    sub = make_sub_problem()

    # For simplicity, we directly use the Scip solver interface from BendersLib.
    # Typically, this should be wrapped in the SubProblem class like SubProblem(Scip(...)).
    sub_problem_solver = Scip(sub)

    # sub_problem_solver.solve()
    iis_vars = sub_problem_solver.compute_iis()
    print("Variables involved in the IIS:", iis_vars)

# %%
#
# .. tags:: solver: scip, iis

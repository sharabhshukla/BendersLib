# coding:utf-8

"""
OR-Tools IIS
=======================================

.. currentmodule:: benderslib.solvers

"""

# %%
# Using :meth:`Ortools.compute_iis` to compute conflicting variables.


from benderslib.solvers import Ortools

from ortools.sat.python import cp_model


def make_sub_problem():
    model = cp_model.CpModel()
    x = model.NewIntVar(0, 5, "x")
    y = model.NewIntVar(0, 5, "y")

    # We need to make the following auxiliary steps to track constraints causing infeasibility:
    # - Define a boolean variable for each constraint.
    # - Use OnlyEnforceIf to link constraints to these boolean variables.
    # - Map boolean variable objects to decision variable names in the corresponding constraints.

    # See also this OR-Tools official example:
    # https://github.com/google/or-tools/blob/stable/ortools/sat/samples/assumptions_sample_sat.py

    # Define boolean variable for each constraint
    c1_active = model.NewBoolVar("c1_active")
    c2_active = model.NewBoolVar("c2_active")
    c3_active = model.NewBoolVar("c3_active")

    # If a boolean variable is true, then the constraint is enforced
    model.Add(x >= 5).OnlyEnforceIf(c1_active)
    model.Add(y >= 5).OnlyEnforceIf(c2_active)
    model.Add(x + y <= 9).OnlyEnforceIf(c3_active)

    # This statement assumes all constraints should be active
    model.AddAssumptions([c1_active, c2_active, c3_active])

    vars_map = {
        "x": x,
        "y": y,
        "c1_active": c1_active,
        "c2_active": c2_active,
        "c3_active": c3_active
    }

    # You are required to provide a mapping from boolean variable objects associated with constraints
    # to the variable names involved in each constraint for IIS computation.
    cons_vars = {
        c1_active: ['x'],
        c2_active: ['y'],
        c3_active: ['x', 'y']
    }

    return model, vars_map, cons_vars


if __name__ == '__main__':
    sub, vars_map, cons_vars = make_sub_problem()

    # For simplicity, we directly use the Ortools solver interface from BendersLib.
    # Typically, this should be wrapped in the SubProblem class like SubProblem(Ortools(...)).
    sub_problem_solver = Ortools(sub, vars_map, cons_vars)

    sub_problem_solver.solve()
    iis_vars = sub_problem_solver.compute_iis()
    print("Variables involved in the IIS:", iis_vars)

# %%
#
# .. tags:: solver: ortools (cp), iis

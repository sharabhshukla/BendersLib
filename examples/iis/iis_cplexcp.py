# coding:utf-8

"""
CPLEX CP IIS
=======================================

"""

# %%
# Using :meth:`~benderslib.solvers.CplexCP.compute_iis` to compute conflicting variables.


from benderslib.solvers import CplexCP

from docplex.cp.model import CpoModel


def make_sub_problem():
    model = CpoModel(name='InfeasibleExample')

    x = model.integer_var(0, 5, name='x')
    y = model.integer_var(0, 5, name='y')

    model.add((x >= 5).set_name('c1'))
    model.add((y >= 5).set_name('c2'))
    model.add((x + y <= 9).set_name('c3'))

    vars_map = {
        'x': x,
        'y': y
    }

    # You are required to provide a mapping from constraint names
    # to the variable names involved in each constraint for IIS computation.
    cons_vars = {
        'c1': ['x'],
        'c2': ['y'],
        'c3': ['x', 'y']
    }

    return model, vars_map, cons_vars


if __name__ == '__main__':
    sub, vars_map, cons_vars = make_sub_problem()

    # For simplicity, we directly use the CplexCP solver interface from BendersLib.
    # Typically, this should be wrapped in the SubProblem class like SubProblem(CplexCP(...)).
    sub_problem_solver = CplexCP(sub, vars_map, cons_vars)

    sub_problem_solver.solve()
    iis_vars = sub_problem_solver.compute_iis()
    print("Variables involved in the IIS:", iis_vars)

# %%
#
# .. tags:: solver: cplex (cp), iis

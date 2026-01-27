# coding:utf-8

"""
Pyomo
=======================================

"""

# %%
# Using :class:`~benderslib.solvers.Pyomo` as a solver backend.


from benderslib import ClassicalBenders, MasterProblem, SubProblem
from benderslib.solvers import Pyomo
from benderslib.utils import draw_curve

import pyomo.environ as pyo


def make_original_problem():
    model = pyo.ConcreteModel("Original")

    n_vars = 7
    model.y = pyo.Var(range(n_vars), domain=pyo.Integers, bounds=(1, 40))
    model.z = pyo.Var(range(n_vars), domain=pyo.Reals, bounds=(1, 40))

    model.obj = pyo.Objective(
        expr=2 * sum(model.y[i] for i in range(n_vars)) + 3 * sum(model.z[i] for i in range(n_vars)),
        sense=pyo.minimize)

    model.main_constr_yz = pyo.Constraint(
        expr=sum(model.y[i] for i in range(n_vars)) + sum(model.z[i] for i in range(n_vars)) <= 50 * n_vars)

    model.constr_y = pyo.ConstraintList()
    for i in range(n_vars):
        model.constr_y.add(2 * model.y[i] <= 2 * (i + 1))

    model.constr_yz = pyo.ConstraintList()
    for i in range(n_vars):
        model.constr_yz.add(2 * model.y[i] + model.z[i] >= i)

    model.constr_z = pyo.ConstraintList()
    for i in range(n_vars):
        model.constr_z.add(3 * model.z[i] <= 15)

    complicating_vars = [f"y[{i}]" for i in range(n_vars)]
    return model, complicating_vars


if __name__ == '__main__':
    original_model, complicating_vars = make_original_problem()

    solvers = [
        'cbc',
        'cplex',
        'cplex_direct',
        'glpk',
        'gurobi',
        'gurobi_direct',
        'highs',
        'mosek',
        'mosek_direct',
        'xpress',
        'xpress_direct',

        # 'scip',  # Unable to obtain correct duals with bound constraints
    ]

    for solver in solvers:
        print(f"Solving with solver: {solver}")

        solver_factory = pyo.SolverFactory(solver)
        result = solver_factory.solve(original_model)
        print(result)

        master = Pyomo.make_master_problem(original_model, complicating_vars)
        sub = Pyomo.make_sub_problem(original_model, complicating_vars)

        master_problem = MasterProblem(Pyomo(master, solver=solver))
        sub_problem = SubProblem(Pyomo(sub, solver=solver))

        BD = ClassicalBenders(master_problem, sub_problem, complicating_vars)
        BD.solve()

        draw_curve(BD.result)

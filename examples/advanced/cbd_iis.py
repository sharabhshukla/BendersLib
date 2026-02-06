# coding:utf-8

"""
Combinatorial Benders Decomposition (IIS)
=========================================

This example demonstrates how to use the Combinatorial Benders decomposition method
with customized Benders cuts.
"""

# %%
# Define the original problem:
from benderslib import AnnotationBenders, CombinatorialBenders, NoGoodFC, MasterProblem, SubProblem
from benderslib.solvers import Gurobi
from gurobipy import Model, GRB
import matplotlib.pyplot as plt


def make_original_problem():
    # The problem is constructed such that the IIS involves only a few complicating variables.
    model = Model()

    n_vars = 9
    x = model.addVars(n_vars, name="x", vtype=GRB.BINARY)
    y = model.addVars(n_vars, name="y", vtype=GRB.BINARY)

    # Constraint 1: All subproblem variables must be one
    model.addConstrs((y[i] == 1 for i in range(n_vars)), name="sub")
    # Constraint 2: But, part of the subproblem variables must be smaller than its first-stage counterpart
    model.addConstrs((y[i] <= x[i] for i in range(int(n_vars))), name="link")

    # Objective: minimize the number of non-zero first-stage variables, second-stage has no objective
    model.setObjective(x.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0
    model.update()
    complicating_vars = [v.VarName for v in x.values()]
    return model, complicating_vars


# %%
# Define stronger customized Benders feasibility cut using IIS:
def cut_generator(master_problem: MasterProblem, sub_problem: SubProblem):
    """
    Generate a stronger feasibility cut using the Irreducible Infeasible Subsystem (IIS) of the subproblem.
    Though `master_problem` is not used, it is required as a placeholder for the callback function.
    """

    # Compute the IIS of the subproblem
    sp = sub_problem.model
    sp.computeIIS()
    # Save IIS to file
    # sp.write("subproblem.ilp")

    # Get the names of the variables in the IIS
    # v.IISLB and v.IISUB can be either 0 (False) or 1 (True), indicating whether the LB or UB is part of the IIS.
    iis_vars = [v.VarName for v in sp.getVars() if v.IISLB or v.IISUB]
    iis_var_values = master_problem.get_var_values(iis_vars)

    cut = NoGoodFC(iis_var_values)
    return [cut]


# %%
# Solve the problem using Gurobi and Combinatorial Benders Decomposition:
if __name__ == '__main__':
    # With subproblem objective
    model, complicating_vars = make_original_problem()

    # Solve with Gurobi
    model.optimize()
    if model.Status == GRB.OPTIMAL:
        print("Original Problem Solution:")
        # var_values = {v.VarName: v.X for v in model.getVars()}
        # print(var_values)
        print(f"Obj: {model.ObjVal}\n")
    else:
        print("Original Problem Solution: Infeasible or Unbounded\n")

    # Solve with Benders Decomposition + IIS-based cuts
    AB = AnnotationBenders(
        model,
        solver=Gurobi,
        complicating_vars=complicating_vars,
        # Customized feasibility cut generator
        feasibility_cut=cut_generator,
        benders=CombinatorialBenders,
    )
    # Modify the cut generator to use IIS-based feasibility cuts
    AB.solve()

    # Solve with Benders Decomposition + Naive cuts
    AB_copy = AnnotationBenders(
        model,
        solver=Gurobi,
        complicating_vars=complicating_vars,
        benders=CombinatorialBenders,
    )
    # Turn of IIS cuts
    AB_copy.params.use_iis_cut = False
    AB_copy.solve()

    print()
    print(f"Sol. Time (IIS vs Naive): {AB.result.time:.4f}, {AB_copy.result.time:.4f}")
    print(f"Num. Cuts (IIS vs Naive): {AB.result.n_cuts}, {AB_copy.result.n_cuts}")

    # Plot cut added
    plt.bar(
        ['IIS-based Cuts', 'Naive Cuts'],
        [AB.result.n_cuts, AB_copy.result.n_cuts],
        color=['blue', 'orange']
    )
    plt.ylabel('Number of Benders Cuts Added')
    plt.title('Comparison of Benders Cuts Added')
    plt.show()

# %%
#
# .. admonition:: References
#
#     * Tutorial of Combinatorial Benders Decomposition: :doc:`../../tutorials/cbd`
#     * This example uses the following classes: :class:`~benderslib.AnnotationBenders`, :class:`~benderslib.CombinatorialBenders`
#
# .. tags:: combinatorial, solver: gurobi, deterministic, custom cut, iis

# coding:utf-8

"""
Trust Region Method (Box Constraints)
=========================================
"""

# %%
# Prepare the problem for Benders decomposition.
from benderslib import ClassicalBenders, AnnotationBenders, CallbackBase
from benderslib.solvers import Gurobi
from benderslib.utils import draw_curve
from gurobipy import Model, GRB


def make_original_problem():
    model = Model("Original")

    n_vars = 20
    y = model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)

    model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr_yz")
    model.addConstrs((2 * y[i] <= 2 * (i + 1) for i in range(n_vars)), name="constr_y")
    model.addConstrs((2 * y[i] + z[i] >= i for i in range(n_vars)), name="constr_yz")
    model.addConstrs((3 * z[i] <= 15 for i in range(n_vars)), name="constr_z")

    model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)

    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    model.update()
    complicating_vars = [v.VarName for v in y.values()]
    return model, complicating_vars


# %%
# Define the trust region callback.
class TrustRegionCallback(CallbackBase):

    def __init__(self, radius):
        self.radius = radius
        self._pre_master_sol = None
        self._trust_region_added = False

        # Store trust region constraints, so that we can remove them later.
        self._pre_tr_cons = []

    def on_before_master_solve(self, context):

        if self._pre_master_sol and not self._trust_region_added:

            # Add a trust region constraint to restrict the master solution within
            # a certain radius from the trust region center (the best-known solution).

            for var_name in self._pre_master_sol:
                var = context.master_problem.model.getVarByName(var_name)

                # Add box constraint var \in [pre_master_sol[var_name] - radius, pre_master_sol[var_name] + radius]
                box_cons_l = context.master_problem.model.addConstr(var >= self._pre_master_sol[var_name] - self.radius)
                box_cons_u = context.master_problem.model.addConstr(var <= self._pre_master_sol[var_name] + self.radius)

                self._pre_tr_cons.append(box_cons_l)
                self._pre_tr_cons.append(box_cons_u)

            self._trust_region_added = True

    def on_new_upper_bound(self, context):
        # Save best-known solution as the trust region center
        self._pre_master_sol = context.master_problem.get_var_values()

        # Remove trust region constraints
        if self._pre_tr_cons:
            context.master_problem.model.remove(self._pre_tr_cons)

        # Trust region is updated only when a new upper bound is found, so we can reset the flag here.
        self._trust_region_added = False
        self._pre_tr_cons = []


# %%
# .. warning::
#
#     The lower bound of Benders decomposition is essentially the master problem objective value,
#     which is **monotonously non-decreasing** as more cuts are added.
#     Adding trust region constraints can break this monotonicity, leading to **early (incorrect) convergence**.
#     In some extreme cases (small radius), trust region constraints may even make the master problem infeasible,
#     causing the algorithm to fail.
#
# Run with the trust region callback.
model, complicating_vars = make_original_problem()
model_copy = model.copy()

BD = AnnotationBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)
trust_region_callback = TrustRegionCallback(1)
BD.benders.register_callback(trust_region_callback)
BD.solve()
draw_curve(BD.result)

# %%
# Run without the trust region callback.
BD_no_tr = AnnotationBenders(
    model_copy,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)
BD_no_tr.solve()
draw_curve(BD_no_tr.result)

# %%
#
# .. tags:: benders: classical, solver: gurobi, deterministic, callback

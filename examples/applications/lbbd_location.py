# coding:utf-8

"""
Facility Location
=======================================================

This example implements the Capacity- and Distance-Constrained
Plant Location Problem as described by Fazel-Zarandi and Beck.
The problem is solved with an integer programming model and Logic-based Benders Decomposition, respectively.
When using Logic-based Benders Decomposition,
we demonstrate how to define a custom subproblem solver and a custom cut generator.

.. admonition:: References

   * Fazel-Zarandi, M. M., & Beck, J. C. (2012). Using logic-based Benders decomposition to solve the capacity- and distance-constrained plant location problem. INFORMS Journal on Computing, 24(3), 387–398. https://doi.org/10.1287/ijoc.1110.0458
"""

# %%
# Integer Programming
# ---------------------------

# %%
# Import necessary packages:
import random
from gurobipy import Model, GRB, quicksum
from itertools import product
from benderslib import LogicBasedBenders, MasterProblem, CST, Cut
from benderslib.solvers import Gurobi


# %%
# Define the function to generate problem instance data:
def generate_problem_data(num_clients, num_facilities, max_vehicles_per_facility, random_seed=None):
    if random_seed is not None:
        random.seed(random_seed)

    # Sets
    client_indices = range(num_clients)
    facility_indices = range(num_facilities)
    vehicle_indices = range(1, max_vehicles_per_facility + 1)

    # Parameters: objective
    facility_opening_costs = {j: random.randint(1000, 2000) for j in facility_indices}
    vehicle_use_cost = 150
    assignment_costs = {(i, j): random.randint(10, 50) for i, j in product(client_indices, facility_indices)}
    # Parameters: constraints
    max_vehicle_distance = 100
    _min_dis = max_vehicle_distance // 4
    _max_dis = max_vehicle_distance // 2
    travel_distances = {(i, j): random.randint(_min_dis, _max_dis) for i, j in
                        product(client_indices, facility_indices)}
    facility_capacities = {j: random.randint(30, 60) for j in facility_indices}
    client_demands = {i: random.randint(5, 15) for i in client_indices}

    problem_data = {
        # Sets
        "client_indices": client_indices,
        "facility_indices": facility_indices,
        "vehicle_indices": vehicle_indices,
        # Parameters: objective
        "facility_opening_costs": facility_opening_costs,
        "vehicle_use_cost": vehicle_use_cost,
        "assignment_costs": assignment_costs,
        # parameters: constraints
        "max_vehicles_per_facility": max_vehicles_per_facility,
        "max_vehicle_distance": max_vehicle_distance,
        "travel_distances": travel_distances,
        "facility_capacities": facility_capacities,
        "client_demands": client_demands,
    }
    return problem_data


# %%
# Define the function to solve the **integer programming** formulation:
def solve_ip(problem_data, enable_reinforcement=True):
    I = problem_data["client_indices"]
    J = problem_data["facility_indices"]
    K = problem_data["vehicle_indices"]
    facility_opening_costs = problem_data["facility_opening_costs"]
    vehicle_use_cost = problem_data["vehicle_use_cost"]
    assignment_costs = problem_data["assignment_costs"]
    max_vehicle_distance = problem_data["max_vehicle_distance"]
    travel_distances = problem_data["travel_distances"]
    facility_capacities = problem_data["facility_capacities"]
    client_demands = problem_data["client_demands"]

    # Create a Gurobi model
    model = Model("IP")

    # Variables
    p = model.addVars(J, vtype=GRB.BINARY, name="p")
    z = model.addVars(J, K, vtype=GRB.BINARY, name="z")
    x = model.addVars(I, J, K, vtype=GRB.BINARY, name="x")

    # Constraints
    # (1) Each client must be served by exactly one facility and one vehicle.
    model.addConstrs((quicksum(x[i, j, k] for j in J for k in K) == 1 for i in I))

    # (2) The total distance traveled by a vehicle cannot exceed its limit.
    model.addConstrs(
        (quicksum(travel_distances[i, j] * x[i, j, k] for i in I) <= max_vehicle_distance * z[j, k]
         for j in J for k in K))

    # (3) The total demand served by a facility cannot exceed its capacity.
    model.addConstrs(
        (quicksum(client_demands[i] * x[i, j, k] for i in I for k in K) <= facility_capacities[j] * p[j]
         for j in J))

    # (4) A vehicle can only be assigned to an open facility.
    model.addConstrs((z[j, k] <= p[j] for j in J for k in K))

    # (5) A client can only be served by an activated vehicle.
    model.addConstrs((x[i, j, k] <= z[j, k] for i in I for j in J for k in K))

    # (6) Symmetry-breaking: vehicles at a site are used in sequential order.
    model.addConstrs((z[j, k] <= z[j, k - 1] for j in J for k in K if k > 1))

    if enable_reinforcement:
        # (8) A plant cannot be open if no client is assigned to it.
        model.addConstrs((p[j] <= quicksum(x[i, j, k] for i in I for k in K) for j in J))

        # (9) A plant cannot be open if no vehicle is assigned to it.
        model.addConstrs((p[j] <= quicksum(z[j, k] for k in K) for j in J))

    # Objective
    objective = (
            quicksum(facility_opening_costs[j] * p[j] for j in J) +
            vehicle_use_cost * quicksum(z[j, k] for j in J for k in K) +
            quicksum(assignment_costs[i, j] * x[i, j, k] for i in I for j in J for k in K)
    )
    model.setObjective(objective, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        print(f"\nOptimal solution found with objective value: {model.ObjVal:.2f}\n")
    else:
        print(f"Optimization finished with status: {model.Status}\n")


# %%
# Generate problem data and solve the integer programming formulation:
instance_data = generate_problem_data(
    num_clients=10,
    num_facilities=4,
    max_vehicles_per_facility=4,
    random_seed=1
)
solve_ip(instance_data)


# %%
# Logic-based Benders Decomposition
# -------------------------------------------

# %%
# Master Problem
# ^^^^^^^^^^^^^^^^^^

# %%
# Define the **master problem** for Logic-based Benders decomposition:
def make_master_problem(problem_data, sub_relaxation=True):
    I = problem_data["client_indices"]
    J = problem_data["facility_indices"]
    facility_opening_costs = problem_data["facility_opening_costs"]
    vehicle_use_cost = problem_data["vehicle_use_cost"]
    assignment_costs = problem_data["assignment_costs"]
    max_vehicle_distance = problem_data["max_vehicle_distance"]
    travel_distances = problem_data["travel_distances"]
    facility_capacities = problem_data["facility_capacities"]
    client_demands = problem_data["client_demands"]
    k_bar = problem_data["max_vehicles_per_facility"]

    # Create a Gurobi model
    master_model = Model("MP")

    # Variables
    p = master_model.addVars(J, vtype=GRB.BINARY, name="p")
    x = master_model.addVars(I, J, vtype=GRB.BINARY, name="x")
    V = master_model.addVars(J, vtype=GRB.INTEGER, lb=0, ub=k_bar, name="V")

    # Constraints
    # (10) Each client is served by exactly one facility.
    master_model.addConstrs((quicksum(x[i, j] for j in J) == 1 for i in I))

    # (11) Facility capacity limit.
    master_model.addConstrs(
        (quicksum(client_demands[i] * x[i, j] for i in I) <= facility_capacities[j] * p[j] for j in J))

    # (12) Upper bound on a single client's travel distance.
    master_model.addConstrs((travel_distances[i, j] * x[i, j] <= max_vehicle_distance for i, j in product(I, J)))

    if sub_relaxation:
        # (13) Relaxation of the subproblem (lower bound on number of vehicles).
        master_model.addConstrs(
            (V[j] * max_vehicle_distance >= quicksum(travel_distances[i, j] * x[i, j] for i in I) for j in J))

    # (15) Customers can only be allocated to open facilities.
    master_model.addConstrs((x[i, j] <= p[j] for i, j in product(I, J)))

    # Objective
    objective = (
            quicksum(facility_opening_costs[j] * p[j] for j in J) +
            quicksum(assignment_costs[i, j] * x[i, j] for i, j in product(I, J)) +
            vehicle_use_cost * quicksum(V[j] for j in J)
    )
    master_model.setObjective(objective, GRB.MINIMIZE)

    master_model.update()
    complicating_vars = [xx.VarName for xx in x.values()]
    complicating_vars += [vv.VarName for vv in V.values()]
    return master_model, complicating_vars


# %%
#
# .. hint::
#
#    In the above master problem, constraint (13) is a relaxation of the subproblem.
#    **Adding subproblem relaxations expressed as master problem variables can significantly improve the convergence of
#    Logic-based Benders decomposition,** as discussed in:
#
#    * Hooker, J. N. (2019). Logic-based Benders decomposition for large-scale optimization. In J. M. Velásquez-Bermúdez, M. Khakifirooz, & M. Fathi (Eds.), Large Scale Optimization in Supply Chains and Smart Manufacturing: Theory and Applications (pp. 1–26). Springer International Publishing. https://doi.org/10.1007/978-3-030-22788-3_1


# %%
# Subproblem
# ^^^^^^^^^^^^^^^^^^

# %%
# Define the **subproblem** solver for Logic-based Benders decomposition:
#
# .. note::
#
#    In this example, the subproblem checks for feasibility. Benders feasibility cuts will be generated
#    when the subproblem is infeasible (any facility is infeasible). When all the facilities are feasible,
#    the optimum is reached.
def subproblem_solver(complicating_var_values):
    I = instance_data["client_indices"]
    J = instance_data["facility_indices"]
    vehicle_max_distance = instance_data["max_vehicle_distance"]
    travel_distances = instance_data["travel_distances"]
    k_bar = instance_data["max_vehicles_per_facility"]

    # Retrieve master problem solution
    facility_vehicle_num = {j: int(complicating_var_values[f"V[{j}]"]) for j in J}
    facility_clients = {j: [] for j in J}
    for i, j in product(I, J):
        if complicating_var_values[f"x[{i},{j}]"] > 0.5:
            facility_clients[j].append(i)

    # Determine the number of vehicles required for each facility
    facility_vehicle_num_req = {j: k_bar for j in J}
    for j in J:
        capacity = vehicle_max_distance
        items = [travel_distances[i, j] for i in facility_clients[j]]
        bin_num_ffd = _bin_packing_ffd(capacity, items)
        if bin_num_ffd > facility_vehicle_num[j]:
            bin_num_exact = _bin_packing_exact(capacity, items)
            if bin_num_exact > facility_vehicle_num[j]:
                facility_vehicle_num_req[j] = bin_num_exact
            else:
                facility_vehicle_num_req[j] = facility_vehicle_num[j]
        else:
            facility_vehicle_num_req[j] = facility_vehicle_num[j]

    # Check feasibility
    for j in J:
        if facility_vehicle_num_req[j] > facility_vehicle_num[j]:
            # ``facility_vehicle_num_req`` can be retrieved in the cut generator via ``sub_problem.var_values``
            return CST.INFEASIBLE, None, facility_vehicle_num_req
    return CST.OPTIMAL, 0, facility_vehicle_num_req


# %%
# The ``subproblem_solver`` relies on solving bin packing problems to check feasibility.
#
# .. note::
#
#    **Bin Packing Problem**: Given a set of items with sizes and a set of bins with fixed capacity,
#    the bin packing problem aims to pack all items into the minimum number of bins without exceeding
#    the capacity of any bin.
def _bin_packing_ffd(capacity: float | int, items: list[float | int]):
    """A simple bin packing solver using first-fit decreasing (FFD) algorithm."""
    bins = []

    for item in sorted(items, reverse=True):
        placed = False
        for b in bins:
            if sum(b) + item <= capacity:
                b.append(item)
                placed = True
                break
        if not placed:
            bins.append([item])

    return len(bins)


def _bin_packing_exact(capacity: float | int, items: list[float | int]):
    """An exact bin packing solver using Gurobi."""
    model = Model("BinPacking")
    model.Params.OutputFlag = 0
    model.Params.LogToConsole = 0

    n_items = len(items)
    max_bins = n_items

    # Variables
    y = model.addVars(max_bins, vtype=GRB.BINARY, name="y")
    x = model.addVars(n_items, max_bins, vtype=GRB.BINARY, name="x")

    # Constraints
    model.addConstrs((quicksum(x[i, j] for j in range(max_bins)) == 1 for i in range(n_items)))
    model.addConstrs(
        (quicksum(items[i] * x[i, j] for i in range(n_items)) <= capacity * y[j] for j in range(max_bins))
    )
    # Symmetry-breaking
    model.addConstrs((y[j] >= y[j + 1] for j in range(max_bins - 1)))

    # Objective
    model.setObjective(quicksum(y[j] for j in range(max_bins)), GRB.MINIMIZE)

    model.optimize()
    used_bins = sum(1 for j in range(max_bins) if y[j].X > 0.5)
    return used_bins


# %%
# Cut Generator
# ^^^^^^^^^^^^^^^^^^^^^^^

# %%
# Define the **feasibility cut generator** for Logic-based Benders decomposition:
def feasibility_cut_generator(master_problem, sub_problem):
    I = instance_data["client_indices"]
    J = instance_data["facility_indices"]

    # Retrieve decision variable values
    # The following lines have been used in ``subproblem_solver``, to avoid redundancy, use a class-based subproblem.
    facility_vehicle_num = {j: int(sub_problem.complicating_var_values[f"V[{j}]"]) for j in J}
    facility_clients = {j: [] for j in J}
    for i, j in product(I, J):
        if sub_problem.complicating_var_values[f"x[{i},{j}]"] > 0.5:
            facility_clients[j].append(i)

    facility_vehicle_num_req = sub_problem.var_values

    cuts = []
    for j in J:
        if facility_vehicle_num_req[j] > facility_vehicle_num[j]:
            vars = [f"x[{i},{j}]" for i in facility_clients[j]] + [f"V[{j}]"]
            coefs = [1] * len(facility_clients[j]) + [-1]
            rhs = len(facility_clients[j]) - facility_vehicle_num_req[j]
            sense = CST.LE
            cut = Cut(
                vars=vars,
                coefs=coefs,
                rhs=rhs,
                sense=sense,
                ctype=CST.FEASIBILITY,
                name=f"FC",
            )
            cuts.append(cut)

    return cuts


# %%
# Solving
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

# %%
# Initialize a Logic-based Benders decomposition instance and solve it:
master_model, complicating_vars = make_master_problem(instance_data)
LBBD = LogicBasedBenders(
    master_problem=MasterProblem(Gurobi(master_model)),
    sub_problem=subproblem_solver,
    complicating_vars=complicating_vars,
    feasibility_cut=feasibility_cut_generator
)
LBBD.solve()

# %%
# Now, remove the subproblem relaxation from the master problem and solve again:
master_model_no_relax, complicating_vars = make_master_problem(instance_data, sub_relaxation=False)
LBBD_no_relax = LogicBasedBenders(
    master_problem=MasterProblem(Gurobi(master_model_no_relax)),
    sub_problem=subproblem_solver,
    complicating_vars=complicating_vars,
    feasibility_cut=feasibility_cut_generator
)
LBBD_no_relax.solve()

# %%
#
# .. admonition:: References
#
#     * Tutorial of the Logic-based Benders Decomposition: :doc:`../../tutorials/lbbd`
#     * This example uses the following class: :class:`~benderslib.LogicBasedBenders`

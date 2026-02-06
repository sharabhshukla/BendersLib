Solver Interfaces
=============================================

.. currentmodule:: benderslib

Abstract Base Classes
---------------------------------------------

.. autoclass:: SolverBase
   :inherited-members:
   :show-inheritance:
   :exclude-members:

.. autoclass:: SolverCPBase
   :inherited-members:
   :show-inheritance:
   :exclude-members: get_var_coefs, get_rhs, get_dual_values, get_extreme_ray, make_master_problem, make_sub_problem,
                     add_estimators, add_cut, remove_cut

Mathematical Programming Solver Interfaces
---------------------------------------------

.. autoclass:: benderslib.solvers.Gurobi
   :inherited-members:
   :show-inheritance:
   :exclude-members:

.. autoclass:: benderslib.solvers.Copt
   :inherited-members:
   :show-inheritance:
   :exclude-members:

.. autoclass:: benderslib.solvers.Pyomo
   :inherited-members:
   :show-inheritance:
   :exclude-members: compute_iis

.. autoclass:: benderslib.solvers.Scip
   :inherited-members:
   :show-inheritance:
   :exclude-members:

.. autoclass:: benderslib.solvers.Cplex
   :inherited-members:
   :show-inheritance:
   :exclude-members:

Constraint Programming Solver Interfaces
---------------------------------------------

.. autoclass:: benderslib.solvers.Ortools
   :inherited-members:
   :show-inheritance:
   :exclude-members: get_var_coefs, get_rhs, get_dual_values, get_extreme_ray, make_master_problem, make_sub_problem,
                     add_estimators, add_cut, remove_cut

.. autoclass:: benderslib.solvers.CplexCP
   :inherited-members:
   :show-inheritance:
   :exclude-members: get_var_coefs, get_rhs, get_dual_values, get_extreme_ray, make_master_problem, make_sub_problem,
                     add_estimators, add_cut, remove_cut

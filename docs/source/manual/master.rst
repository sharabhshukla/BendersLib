Master Problem
============================================

.. currentmodule:: benderslib

Create a Master Problem
-------------------------------------------

Master Problem from Annotated Model
-------------------------------------------

Add Benders Cut to Master Problem
-------------------------------------------

====

Attributes & Methods
--------------------------------------------

Below are the attributes and methods of the master problem class :class:`MasterProblem`.
It is inherited from the base class :class:`ProblemBase`, but tailored for master problems in Benders Decomposition.
:class:`ProblemBase` takes an instance that inherits from
:class:`SolverBase` as an argument to handle the underlying optimization solver.

.. mermaid::
    :caption: Master Problem Inheritance Diagram
    :align: center

    flowchart LR
        MasterProblem --inherits--> ProblemBase
        ProblemBase --uses--> SolverBase
    style SolverBase fill:#f2f2f2,stroke:#333,stroke-width:1px

.. rubric:: Attributes

.. autosummary::
   :nosignatures:

   ~MasterProblem.model
   ~MasterProblem.status
   ~MasterProblem.params
   ~MasterProblem.complicating_vars
   ~MasterProblem.optimality_cuts
   ~MasterProblem.feasibility_cuts
   ~MasterProblem.estimators

.. rubric:: Methods

.. autosummary::
   :nosignatures:

   ~MasterProblem.add_cut
   ~MasterProblem.remove_cut
   ~MasterProblem.get_estimator_values
   ~MasterProblem.add_vars
   ~MasterProblem.get_obj_expr
   ~MasterProblem.set_obj
   ~MasterProblem.fix_vars
   ~MasterProblem.unfix_vars
   ~MasterProblem.get_var_values
   ~MasterProblem.get_var_coefs
   ~MasterProblem.get_rhs
   ~MasterProblem.get_dual_values
   ~MasterProblem.get_extreme_ray
   ~MasterProblem.get_obj
   ~MasterProblem.solve

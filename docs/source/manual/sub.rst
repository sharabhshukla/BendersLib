Subproblem
============================================

.. currentmodule:: benderslib

Create a Subproblem
-------------------------------------------

Subproblem from Annotated Model
-------------------------------------------

Create Multiple Subproblems
-------------------------------------------

====

.. _manual_custom_sub:

Customization
-------------------------------------------

Custom Subproblem Solver (class-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom Subproblem Solver (function-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom Subproblems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====

Attributes & Methods
-------------------------------------------

The class :class:`SubProblem` is inherited from the base class :class:`ProblemBase`,
but tailored for subproblems in Benders Decomposition.
:class:`ProblemBase` takes an instance that inherits from
:class:`SolverBase` as an argument to handle the underlying optimization solver.
For stochastic programming with multiple scenarios, the class :class:`SubProblems` manages multiple subproblem instances.

.. mermaid::
    :caption: Subproblem Inheritance Diagram
    :align: center

    flowchart LR
        SubProblem -- inherits --> ProblemBase
        ProblemBase -- uses --> SolverBase
        SubProblems -. contains .-> SubProblem
        SubProblems -. contains .-> LogicBasedSubProblem

    style SolverBase fill:#f2f2f2,stroke:#333,stroke-width:1px

*\*Note: Dashed arrows indicate optional relationships, from which exactly one must be selected for each usage.*

We also provide a :class:`LogicBasedSubProblem` template for custom subproblem,
especially for logic-based Benders Decomposition that do not rely on traditional optimization solvers.
Users can inherit from :class:`LogicBasedSubProblem` and implement the required abstract methods for custom subproblem logic.

Below are the attributes and methods :class:`SubProblem`, :class:`SubProblems`, and :class:`LogicBasedSubProblem`.

SubProblem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Attributes

.. autosummary::
   :nosignatures:

   ~SubProblem.model
   ~SubProblem.status
   ~SubProblem.params
   ~SubProblem.complicating_vars

.. rubric:: Methods

.. autosummary::
   :nosignatures:

   ~SubProblem.add_vars
   ~SubProblem.get_obj_expr
   ~SubProblem.set_obj
   ~SubProblem.fix_vars
   ~SubProblem.unfix_vars
   ~SubProblem.get_var_values
   ~SubProblem.get_var_coefs
   ~SubProblem.get_rhs
   ~SubProblem.get_dual_values
   ~SubProblem.get_extreme_ray
   ~SubProblem.get_obj
   ~SubProblem.solve

SubProblems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Attributes

.. autosummary::
   :nosignatures:

   ~SubProblems.sub_problems
   ~SubProblems.prob
   ~SubProblems.params
   ~SubProblems.status

.. rubric:: Methods

.. autosummary::
   :nosignatures:

   ~SubProblems.get_obj
   ~SubProblems.fix_vars
   ~SubProblems.get_var_values
   ~SubProblems.solve

LogicBasedSubProblem
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. rubric:: Attributes

.. autosummary::
   :nosignatures:

   ~LogicBasedSubProblem.complicating_vars
   ~LogicBasedSubProblem.complicating_var_values
   ~LogicBasedSubProblem.obj
   ~LogicBasedSubProblem.var_values
   ~LogicBasedSubProblem.status
   ~LogicBasedSubProblem.params

.. rubric:: Methods

.. autosummary::
   :nosignatures:

   ~LogicBasedSubProblem.solve
   ~LogicBasedSubProblem.fix_vars
   ~LogicBasedSubProblem.get_var_values
   ~LogicBasedSubProblem.get_obj


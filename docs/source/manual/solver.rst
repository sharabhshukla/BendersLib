Solver Interfaces
===========================================

.. currentmodule:: benderslib

Supported Solvers
-------------------------------------------

.. attention::

   BendersLib will **NOT** install any solver to your environment automatically.
   You need to install the solvers separately based on your needs.

BendersLib supports the following solvers.
Installation instructions can be found in the manual under :ref:`Installing Solvers <manual_installing_solver>`.

.. list-table:: Built-in Solvers Interfaces
    :widths: 15 15 15 50 50
    :header-rows: 1

    * - Solver
      - Class
      - Type
      - Website
      - Note
    * - Gurobi
      - :class:`Gurobi`
      - MP
      - https://docs.gurobi.com
      - Commercial solver with free academic license.

*MP: Mathematical Programming, CP: Constraint Programming.*

If you want to use a solver not listed here,
you can implement your own solver interface by inheriting from :class:`SolverBase` and implement
the abstract methods defined.

.. note::

   *Contributing solver interfaces to BendersLib is welcome!*
   See :ref:`manual_custom_solver_interface` and :doc:`contribution` for guidelines.

Mathematical Programming vs. Constraint Programming
----------------------------------------------------

====

Customization
-------------------------------------------

Lightweight Custom Solver Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. _manual_custom_solver_interface:

Fully Featured Custom Solver Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====

Attributes & Methods
-------------------------------------------

Below are the attributes and methods of the base solver interface :class:`SolverBase`.
Any built-in solver interface (e.g., :class:`Gurobi`) is inherited from this base class,
meaning they have these attributes and methods.
Adding a new solver interface requires implementing these attributes and methods,
especially the `abstract methods <https://docs.python.org/3/library/abc.html#abc.abstractmethod>`_.
See :class:`SolverBase` for the comprehensive API reference, and :doc:`built-in solver interfaces <../api/solver>` for examples.

.. mermaid::
    :caption: Solver Interface Inheritance Diagram
    :align: center

    flowchart TD
        Gurobi -->|inherits| SolverBase
        COPT -->|inherits| SolverBase
        HiGHS -->|inherits| SolverBase
        Pyomo -->|inherits| SolverBase

.. seealso::

    * Base Class: :class:`SolverBase`
    * Solver Interfaces: :class:`Gurobi`

.. rubric:: Attributes

.. autosummary::
   :nosignatures:

   ~SolverBase.status
   ~SolverBase._solver_model
   ~SolverBase._sense
   ~SolverBase._all_vars
   ~SolverBase._int_vars
   ~SolverBase._bin_vars
   ~SolverBase._var_bounds
   ~SolverBase._rhs

.. rubric:: Methods

.. autosummary::
   :nosignatures:

   ~SolverBase.add_vars
   ~SolverBase.get_obj_expr
   ~SolverBase.set_obj
   ~SolverBase.fix_vars
   ~SolverBase.unfix_vars
   ~SolverBase.get_var_values
   ~SolverBase.get_var_coefs
   ~SolverBase.get_rhs
   ~SolverBase.get_dual_values
   ~SolverBase.get_extreme_ray
   ~SolverBase.get_obj
   ~SolverBase.add_cut
   ~SolverBase.remove_cut
   ~SolverBase.solve
   ~SolverBase.make_master_problem
   ~SolverBase.make_sub_problem

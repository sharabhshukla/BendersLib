Solver Interfaces
=======================================

.. currentmodule:: benderslib

BendersLib currently supports the following solvers.
You can implement your own solver interface by inheriting from :class:`SolverBase` and implement
the abstract methods defined, if you want to use a solver not listed here.

.. list-table:: Built-in Solvers Interfaces
    :widths: 15 15 50 50 50
    :header-rows: 1

    * - Solver
      - Class
      - Installation
      - Website
      - Note
    * - Gurobi
      - :class:`Gurobi`
      - ``pip install gurobipy``
      - https://docs.gurobi.com
      - Commercial solver with free academic license.

When you need :class:`AnnotationBenders`, :func:`make_master_problem` and :func:`make_sub_problem` are
required to be implemented. An example can be found in
:func:`Gurobi.make_master_problem` and :func:`Gurobi.make_sub_problem`.

Base Class
----------------------------

.. autoclass:: SolverBase
   :inherited-members:

.. _api-gurobi:

Built-in Gurobi Interface
----------------------------

.. autoclass:: Gurobi
   :inherited-members:
   :show-inheritance:

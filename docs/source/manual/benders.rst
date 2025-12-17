Benders Methods
===========================================

.. currentmodule:: benderslib

.. _manual_builtin_benders:

Built-in Benders Methods
-------------------------------------------

.. autosummary::
   :nosignatures:

   ~ClassicalBenders
   ~CombinatorialBenders
   ~LShaped
   ~IntegerLShaped
   ~LogicBasedBenders

Create a Benders Decomposition Instance
-------------------------------------------

Classical Benders Decomposition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Combinatorial Benders Decomposition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Options for Benders Decomposition
-------------------------------------------

Solve the Benders Decomposition Instance
-------------------------------------------

Access Additional Statistics
-------------------------------------------

Stochastic Benders Decomposition
-------------------------------------------

Nested Benders Decomposition
-------------------------------------------

Automated Decomposition
-------------------------------------------

====

Customization
-------------------------------------------

Custom Benders Decomposition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom Stochastic Benders Decomposition
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====

Attributes & Methods
-------------------------------------------

The class :class:`BendersSolver` is the base class for all Benders Decomposition implementations.
Specific implementations, e.g., :class:`ClassicalBenders`, inherit from this class.
The diagram below illustrates the main inheritance and composition relationships among the relevant classes.
A :class:`BendersSolver` instance is composed of :class:`MasterProblem`,
:class:`SubProblem` (or :class:`SubProblems`, :class:`LogicBasedSubProblem`),
and :class:`CutGenerator` instances to handle their respective functionalities.

.. mermaid::
    :caption: Benders Solver Inheritance Diagram
    :align: center

    flowchart LR
        BendersSolver -- has --> CutGenerator
        BendersSolver -- has --> MasterProblem
        BendersSolver -- has --> SubProblem

        CutGenerator -- generates --> Cut
        Cut -- is added to --> MasterProblem

        CutGenerator -- uses --> SubProblem
        CutGenerator -- uses --> MasterProblem

        style MasterProblem fill:#f2f2f2,stroke:#333,stroke-width:1px
        style SubProblem fill:#f2f2f2,stroke:#333,stroke-width:1px
        style CutGenerator fill:#f2f2f2,stroke:#333,stroke-width:1px
        style Cut fill:#f2f2f2,stroke:#333,stroke-width:1px

Below are the attributes and methods of the :class:`BendersSolver` class.
Please refer to :doc:`API Reference <../api/benders>` for the attributes and methods of specific implementations.

.. rubric:: Attributes

.. autosummary::
   :nosignatures:

   ~BendersSolver.master_problem
   ~BendersSolver.sub_problem
   ~BendersSolver.complicating_vars
   ~BendersSolver.optimality_cut
   ~BendersSolver.feasibility_cut
   ~BendersSolver.params
   ~BendersSolver.result

.. rubric:: Methods

.. autosummary::
   :nosignatures:

   ~BendersSolver.solve
   ~BendersSolver.from_models

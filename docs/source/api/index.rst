API Reference
======================

.. currentmodule:: benderslib

Overview
----------------------

The diagram below illustrates the :doc:`core` and :doc:`callbacks` and their relationships in BendersLib.
Other classes, including ones in :doc:`data`, :doc:`solvers`, :doc:`cuts`, and :doc:`benders`
are omitted for clarity.
The inheritance relationships are also shown in their respective sections.

.. mermaid::
    :caption: BendersLib Core Classes
    :align: center

    flowchart LR

    BendersSolver -- "has" --> MasterProblem
    BendersSolver -- "has" --> SubProblem
    BendersSolver -- "has" --> CutGenerator
    Cut -- "is added to" --> MasterProblem
    CutGenerator -- "generates" --> Cut
    CutGenerator -- "uses" --> SubProblem
    CutGenerator -- "uses" --> MasterProblem

    BendersSolver -- "triggers" --> CallbackBase
    CallbackBase -- "uses" --> BendersContext
    BendersContext -- "uses" --> MasterProblem
    BendersContext -- "uses" --> SubProblem

In the above diagram, the classes are categorized into five groups based on their roles in
the Benders decomposition process.

- **Master Problem**:
  This group includes the :class:`MasterProblem` class, which represents the master problem in
  the Benders decomposition framework. It is responsible for maintaining the current solution
  and incorporating cuts generated from the subproblem.
- **Sub Problem**:
  This group includes the :class:`SubProblem` (:class:`SubProblems`, :class:`LogicBasedSubProblem`)
  class, which represents the subproblem in the Benders decomposition framework. It is responsible
  for solving the subproblem based on the current solution from the master problem.
- **Cut Generation**:
  This group includes the :class:`Cut` (:class:`OptimalityCut`, :class:`FeasibilityCut`) and
  :class:`CutGenerator` classes, which are responsible for representing and generating cuts
  that are added to the master problem based on the solutions obtained from the subproblem.
- **Callback System**:
  This group includes the :class:`CallbackBase` and :class:`BendersContext` classes, which
  are responsible for providing a mechanism to customize the behavior of the Benders decomposition
  process through callbacks. The :class:`CallbackBase` class serves as the base class for creating
  custom callbacks, while the :class:`BendersContext` class provides access to the current state
  of the solver during callback execution.
- **Benders Solver**:
  This group includes the :class:`BendersSolver` class, which serves as the main interface for
  users to solve optimization problems using Benders decomposition. It orchestrates the interaction
  between the master problem, subproblem, cut generation, and callbacks to efficiently solve the problem.

Contents
----------------------

.. toctree::
   :maxdepth: 2

   data.rst
   solvers.rst
   core.rst
   cuts.rst
   benders.rst
   callbacks.rst
   functions.rst
   errors.rst

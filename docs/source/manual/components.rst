Components
=======================

.. currentmodule:: benderslib

Overview of the Design
-----------------------

The design of BendersLib follows the :doc:`Benders decomposition principle <../tutorials/index>`,
breaking down a complex optimization problem into a **master problem** and a **subproblem** (or subproblems).
At its core is an **iterative process** that progressively approaches the optimal solution by
passing information between the master problem and the subproblem, using trail solutions and **Benders cuts**.

The main workflow begins with solving the master problem,
which initially contains little or no information from the subproblem,
to obtain a set of values for the complicating variables.
These values are then fixed in the subproblem,
which is solved to assess the future cost or feasibility under the current master decision.
Based on the subproblem's solution, one or more Benders optimality and/or feasibility cuts are generated.
These cuts feed information back to the master problem,
either to exclude the current solution or to refine the objective function in subsequent iterations.
This iterative cycle repeats until the objective values of the master problem and the subproblem converge,
indicating that the optimal solution to the original problem has been found.

.. note::

    All Benders Decomposition variants (:doc:`../tutorials/index`) share the same key components:
    **master problem**, **subproblem**, **Benders cuts**, and the **iterative solving process**.

The BendersLib is structured around these fundamental components,
allowing users to define and customize most parts according to their specific problem requirements.
The following diagram illustrates the relationships between the main components of BendersLib.

.. mermaid::
    :caption: BendersLib Components

    graph TD
        subgraph "Benders Decomposition"
            BM["Benders Method"]
            MP["Master Problem"]
            SP["Subproblem"]
            CG["Cut Generator"]
            BC["Benders Cut"]
        end

        SI["Solver Interface"]
        ES["External Solver"]

        style ES fill:#f2f2f2,stroke:#333,stroke-width:1px

        BM -- "has" --> MP
        BM -- "has" --> SP
        BM -- "has" --> CG
        MP -- "uses" --> SI
        SP -- "uses" --> SI
        CG -- "generates" --> BC
        BC -- "is added to" --> MP
        SI -- "interfaces with" --> ES

Within this framework, the **Benders Method** acts as the main controller,
coordinating the solving process between the **Master Problem** and the **Subproblem**.
The **Cut Generator** is responsible for extracting information from
the master problems's and subproblem's results to create **Benders Cut**.
A unified **Solver Interface** allows BendersLib to interact with
:doc:`various external optimization solvers <solver>` to solve both the master and subproblems.
This design enables users to flexibly define and combine different Benders decomposition strategies
to meet the demands of various complex optimization problems.

Main Components
-----------------------

Below is a brief overview of the main components in BendersLib.
Users may visit the respective :doc:`index` for how to use and customize each component.
Detailed API for each component can be found in the :doc:`API reference <../api/index>`.

* :doc:`solver`:
  The solver component provides a unified interface to :doc:`various external optimization solvers <solver>`.
  It defines a common set of methods for interacting with any solver, such as building models, adding variables,
  adding constraints, and triggering the solution process.
  This abstraction allows the main Benders algorithm to remain independent of the specific solver used.

.. admonition:: Related classes
    :class: seealso

    * Abstraction: :class:`SolverBase`
    * Solvers: :class:`~.solvers.Gurobi`, :class:`~.solvers.Copt`

* :doc:`master`:
  The master problem component represents the high-level problem in the Benders decomposition.
  It is responsible for managing the master model, which includes the complicating variables and the Benders cuts added
  during the iterative process.
  At each iteration, it solves the relaxed master problem to propose a new solution for the complicating variables
  and establish a lower bound on the optimal objective.

.. admonition:: Related classes
    :class: seealso

    * :class:`ProblemBase`, :class:`MasterProblem`

* :doc:`sub`:
  The subproblem component evaluates the consequences of the decisions made in the master problem.
  It takes the solution for the complicating variables, fixes them within its own model,
  and solves the resulting problem. The outcome (objective value, dual information, or proof of infeasibility)
  is used to generate Benders cuts and provide an upper bound on the optimal objective.
  For stochastic problems, this component can manage multiple subproblems representing different scenarios.

.. admonition:: Related classes
    :class: seealso

    * :class:`ProblemBase`, :class:`SubProblem`, :class:`LogicBasedSubProblem`, :class:`SubProblems`

* :doc:`cut` (and cut generator):
  This component is responsible for defining and generating the Benders cuts that link the subproblem's results
  back to the master problem. It includes logic for creating different types of cuts,
  such as optimality and feasibility cuts, based on the subproblem's solution.
  This abstracts the logic of cut generation, allowing maintaining global attributes for cut management.

.. admonition:: Related classes
    :class: seealso

    * Abstraction:
      :class:`CutGenerator`, :class:`Cut`, :class:`OptimalityCut`, :class:`FeasibilityCut`
    * Benders cut:
      :class:`ClassicalOC`, :class:`ClassicalFC`, :class:`CombinatorialOC`, :class:`NoGoodFC`, :class:`LShapedOC`,
      :class:`GeneralizedOC`, :class:`GeneralizedFC`, :class:`GeneLShapedOC`
    * Cut generator:
      :class:`ClassicalOCGen`, :class:`ClassicalFCGen`,
      :class:`CombinatorialOCGen`, :class:`CombinatorialFCGen`,
      :class:`LShapedOCGen`, :class:`LShapedFCGen`,
      :class:`IntegerLShapedOCGen`, :class:`IntegerLShapedFCGen`,
      :class:`GeneralizedOCGen`, :class:`GeneralizedFCGen`,
      :class:`GeneLShapedOCGen`

    *\* Note: "OC" stands for Optimality Cut, and "FC" stands for Feasibility Cut.*

* :doc:`benders`: This is the core controller that executes the Benders decomposition algorithm.
  It orchestrates the entire process: iteratively solving the master problem and subproblem(s),
  managing the addition of cuts, and checking for convergence.
  It brings all the other components together to implement various built-in Benders decomposition methods,
  and other custom variants by users.

.. admonition:: Related classes
    :class: seealso

    * Abstraction: :class:`BendersSolver`,
    * Benders methods: :class:`ClassicalBenders`, :class:`CombinatorialBenders`,
      :class:`LShaped`, :class:`IntegerLShaped`, :class:`LogicBasedBenders`, :class:`GeneralizedBenders`,
      :class:`GeneLShaped`

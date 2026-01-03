API Reference
======================

Overview
----------------------

The diagram below illustrates the :doc:`core` and their relationships in BendersLib.
Other classes, including ones in :doc:`data`, :doc:`solver`, :doc:`cut`, and :doc:`benders`
are omitted for clarity.
The inheritance relationships are also shown in their respective sections.

.. mermaid::
    :caption: BendersLib Core Classes
    :align: center

    flowchart LR

    style Cut fill:#D6EAF8,stroke:#333,stroke-width:1px
    style OptimalityCut fill:#D6EAF8,stroke:#333,stroke-width:1px
    style FeasibilityCut fill:#D6EAF8,stroke:#333,stroke-width:1px
    style CutGenerator fill:#D6EAF8,stroke:#333,stroke-width:1px

    style SubProblem fill:#D5F5E3,stroke:#333,stroke-width:1px
    style SubProblems fill:#D5F5E3,stroke:#333,stroke-width:1px
    style LogicBasedSubProblem fill:#D5F5E3,stroke:#333,stroke-width:1px

    style MasterProblem fill:#FEF9E7,stroke:#333,stroke-width:1px
    style BendersSolver stroke:#333,stroke-width:1px

    BendersSolver -- "has" --> MasterProblem
    BendersSolver -. "has" .-> SubProblem
    BendersSolver -- "has" --> CutGenerator
    Cut -. "is added to" .-> MasterProblem
    FeasibilityCut -. "is added to" .-> MasterProblem
    OptimalityCut -. "is added to" .-> MasterProblem
    CutGenerator -. "generates" .-> Cut
    CutGenerator -. "generates" .-> OptimalityCut
    CutGenerator -. "generates" .-> FeasibilityCut
    CutGenerator -. "uses" .-> SubProblem
    CutGenerator -. "uses" .-> SubProblems
    CutGenerator -. "uses" .-> LogicBasedSubProblem
    CutGenerator -- "uses" --> MasterProblem
    OptimalityCut -- "inherits" --> Cut
    FeasibilityCut -- "inherits" --> Cut

    BendersSolver -. "has" .-> SubProblems
    BendersSolver -. "has" .-> LogicBasedSubProblem
    SubProblems -. "contains" .-> SubProblem
    SubProblems -. "contains" .-> LogicBasedSubProblem



*\*Note: Dashed arrows indicate optional relationships, from which exactly one must be selected for each usage.*

Contents
----------------------

.. toctree::
   :maxdepth: -1

   data.rst
   solver.rst
   core.rst
   cut.rst
   benders.rst
   exceptions.rst

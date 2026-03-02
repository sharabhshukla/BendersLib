Manual
=================================================

.. currentmodule:: benderslib

Motivation
------------------------------------------------

Benders Decomposition is a powerful mathematical programming technique for optimization problems
with block structure, developed by Jacques Benders (1941-2017) in 1962 [1]_.
The method decomposes a complex problem into smaller, more manageable master problem and subproblem,
which can be solved iteratively to find the optimal solution to the original problem.

.. mermaid::
   :align: center

   xychart-beta
     title "Benders Decomposition Publications"
     x-axis "Year" [2001, 2003, 2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023, 2025]
     y-axis "Number of Papers"
     bar [100, 150, 200, 300, 400, 550, 700, 950, 1200, 1600, 2000, 2500, 3000]

From 1962 to 2025, there are over tens of thousands of research articles on Benders Decomposition,
covering a wide range of applications in various fields, including supply chain management,
energy systems, transportation, finance, and many others.
Despite its popularity (**1000 papers per year on average**, according to
`Google Scholar <https://scholar.google.com/scholar?q=Benders+Decomposition>`_),
there is no software library specializing in Benders Decomposition and its variants.
This project aims to fill this gap by providing a user-friendly and extensible library for Benders Decomposition
- **BendersLib**, which can be easily integrated with existing optimization solvers and frameworks.
Although this library is designed to be extended with user-defined Benders cuts, acceleration techniques,
and algorithms, it also implements several :doc:`representative Benders Decomposition variants <../tutorials/index>` for
rapid prototyping and benchmarking.

What can BendersLib provide?
------------------------------------------------

BendersLib offers a flexible and powerful framework for implementing Benders decomposition. Here's what you can do with it.

*   **Rapid Prototyping**:
    BendersLib implements :ref:`several common Benders decomposition algorithms <manual_builtin_benders>`.
    It also includes various :doc:`built-in Benders cuts <../api/cuts>`,
    enabling users to quickly prototype and validate their models.
    This allows researchers and practitioners to quickly test the feasibility of a Benders decomposition approach
    for their specific problem without implementing the entire algorithm from scratch.
    It significantly reduces development time and lowers the barrier to entry for using this technique.

*   **High Extensibility**:
    BendersLib is highly extensible.
    Users can easily customize core components like :ref:`solver interfaces <manual_custom_solver_interface>`,
    :class:`LogicBasedSubProblem`, and :class:`CutGenerator` to meet their specific needs.
    This flexibility is crucial for tackling complex, real-world problems that may require non-standard
    decomposition structures or specialized cut generation strategies.
    It empowers users to tailor the framework to their unique problem,
    facilitating research into new Benders variants and acceleration techniques.

What cannot BendersLib do?
------------------------------------------------

While BendersLib is a powerful tool, it's important to understand its scope.

*   **It cannot automatically identify complicating variables.**
    BendersLib requires the user to define which variables are part of the master problem
    and which belong to the subproblem.
    This decision is problem-specific and is a critical step in the modeling process that relies on
    the user's domain knowledge and understanding of the problem structure.
    The library (*currently*) does not have the capability to analyze a model and suggest a decomposition.

*   **It does not guarantee performance improvements.**
    The effectiveness of Benders decomposition is highly dependent on the structure of the problem.
    While it can lead to performance gains for :ref:`certain classes of problems <suitable-problem>`,
    it is not a silver bullet. For some problems, the computational overhead of managing
    the master problems, subproblems, and Benders cuts can exceed the benefits of decomposition,
    leading to longer solution times compared to solving the monolithic problem.

*   **It is not a standalone solver.**
    You still need to formulate your optimization problem using a dedicated modeling library.
    BendersLib orchestrates the decomposition and solution process,
    but it does not solve master problems or subproblems on its own.
    You must integrate it with an appropriate solver interface that can handle your specific problem type.

Alternatives
------------------------------------------------

Several optimization solvers overlap with BendersLib's functionality.
Consider one of these alternatives if BendersLib does not meet your requirements.

.. list-table:: Optimization Solvers with Benders Decomposition Features
    :widths: 15 70 10 15
    :header-rows: 1

    * - Name
      - Feature
      - Language
      - License
    * - `AIMMS <https://documentation.aimms.com/language-reference/optimization-modeling-components/automatic-benders-decomposition/index.html>`__
      - An optimization modeling system that supports automatic Benders decomposition.
      - AIMMS Language
      - Commercial
    * - `Coluna.jl <https://atoptima.github.io/Coluna.jl>`_
      - A branch-and-price-and-cut framework that supports Benders Decomposition.
      - Julia
      - `MPL 2.0 <https://github.com/atoptima/Coluna.jl?tab=License-1-ov-file#readme>`__
    * - `CPLEX <https://www.ibm.com/docs/en/icos/22.1.1?topic=optimizers-users-manual-cplex>`_
      - An optimization solver that supports annotated Benders decomposition [2]_.
      - C/C++, Java, .NET
      - Commercial
    * - `FortSP <http://dev.optirisk-systems.com/products/solver-systems/fortsp/>`_
      - A solver for stochastic programming that supports L-shaped method and nested Benders decomposition.
      - C
      - Commercial
    * - `GCG <https://gcg.or.rwth-aachen.de/>`_
      - A generic decomposition solver for mixed-integer programs that has the capability of automatically Benders decomposition (part of the SCIP Optimization Suit).
      - C/C++ *
      - LGPL
    * - `mpi-sppy <https://mpi-sppy.readthedocs.io/>`_
      - A package for solving Stochastic Programming problems with L-shaped method and other decomposition algorithms.
      - Python
      - `BSD 3 Clause <https://github.com/Pyomo/mpi-sppy/blob/main/LICENSE.md>`_
    * - `SCIP <https://www.scipopt.org>`_
      - A framework for constraint integer programming and branch-cut-and-price that supports Benders Decomposition [3]_.
      - C/C++ *
      - `Apache 2.0 <https://www.scipopt.org/index.php#license>`_
    * - `SDDP.jl <https://sddp.dev/>`_ [4]_
      - A package for solving Multistage Stochastic Programming using Stochastic Dual Dynamic Programming (nested Benders methods).
      - Julia
      - `MPL 2.0 <https://github.com/odow/SDDP.jl?tab=License-1-ov-file#readme>`__
    * - `StochasticPrograms.jl <https://martinbiel.github.io/StochasticPrograms.jl>`_ [5]_
      - A package for modeling and solving Stochastic Programming problems that supports the L-shaped method.
      - Julia
      - `MIT License <https://github.com/martinbiel/StochasticPrograms.jl/blob/master/LICENSE.md>`_

*\* Note: SCIP has a Python interface namely* `PySCIPOpt <https://pyscipopt.readthedocs.io>`_;
*GCG has a Python interface namely* `PyGCGOpt <https://scipopt.github.io/PyGCGOpt/>`_.

Contents
------------------------------------------------

.. toctree::
   :maxdepth: -1

   installation.rst
   quickstart.rst
   components.rst
   workflow.rst
   solvers.rst
   master.rst
   sub.rst
   cuts.rst
   benders.rst
   callbacks.rst
   logging.rst
   numerical.rst
   howto.rst
   contribution.rst

References
------------------------------------------------

.. [1] Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
.. [2] Bonami, P., Salvagnin, D., & Tramontani, A. (2020). Implementing Automatic Benders Decomposition in a Modern MIP Solver. In D. Bienstock & G. Zambelli (Eds.), Integer Programming and Combinatorial Optimization (pp. 78–90). Springer International Publishing. https://doi.org/10.1007/978-3-030-45771-6_7
.. [3] Maher, S. J. (2021). Implementing the branch-and-cut approach for a general purpose Benders’ decomposition framework. European Journal of Operational Research, 290(2), 479–498. https://doi.org/10.1016/j.ejor.2020.08.037
.. [4] Dowson, O., & Kapelevich, L. (2021). SDDP.jl: A Julia Package for Stochastic Dual Dynamic Programming. INFORMS Journal on Computing, 33(1), 27–33. https://doi.org/10.1287/ijoc.2020.0987
.. [5] Biel, M., & Johansson, M. (2022). Efficient Stochastic Programming in Julia. INFORMS Journal on Computing, 34(4), 1885–1902. https://doi.org/10.1287/ijoc.2022.1158

Tutorials
=============

This tutorial section offers an overview of the Benders Decomposition theory,
covering its development over more than fifty years.
There are several important variants of Benders Decomposition listed below.
They are implemented (:doc:`../api/benders`, :doc:`../examples/index`) in BendersLib, and these representative variants
will help guide the design (:doc:`../manual/index`, :doc:`../api/index`) of the library.

.. list-table:: Benders Decomposition Variants
    :widths: 50 20 20 20
    :header-rows: 1
    :name: benders-variants

    * - Name
      - P\. Type
      - M.P. Type
      - S.P. Type
    * - (Classical) Benders Decomposition [1]_
      - MILP
      - MILP
      - LP
    * - Combinatorial Benders Decomposition [2]_
      - MILP
      - MILP
      - Feasibility
    * - Generalized Benders Decomposition [3]_
      - NLP
      - NLP
      - Convex NLP
    * - L-shaped Method [4]_
      - Stochastic LP
      - LP
      - LP
    * - Integer L-shaped Method [5]_
      - Stochastic MILP
      - MILP (binary)
      - MILP (binary)
    * - Nested Benders Decomposition [6]_
      - Stochastic LP
      - LP
      - LP
    * - Logic-based Benders Decomposition [7]_
      - Any
      - Any
      - Any

*P.: Original problem, M.P.: Master problem, S.P.: Sub problem,
MILP: Mixed-Integer Linear Programming, LP: Linear Programming, NLP: Non-Linear Programming.*

A Benders Decomposition method is composed of a **master problem**, one or more **subproblems**, **Benders cuts**,
and a **Benders algorithm** that orchestrates the solution process, to solve the original mathamatical programming problem.
These components make one Benders method different from another, e.g., ones in :ref:`benders-variants`.
A breif introduction of the components of these varaints is given below.


* :doc:`classical` is essentially a Kelley's
  :abbr:`cutting-plane method (methods iteratively refine a feasible set or objective function by linear inequalities)` [8]_
  for solving MILPs. It works by splitting a problem into two parts: a master problem that handles
  the difficult (integer) decisions and a subproblem that deals with the consequences of those decisions.
  The master problem, an MILP, proposes a set of integer variables, and the subproblem, a much simpler LP,
  checks the feasibility and optimality of that proposal. Information from the subproblem's dual solution is
  then used to generate linear *Benders optimality cuts* and *Benders feasibility cuts* that are added to the master problem,
  systematically refining the solution until an optimum is found.

* :doc:`cbd`
  extends the cutting-plane approach to MILPs where the subproblem is itself a
  combinatorial problem, typically a MILP. Like the classical method, it divides the problem into a master problem
  (**complicating variables are pure binary**) and a subproblem that assesses the consequences.
  The fundamental difference is that the subproblem is not a simple LP, meaning its solution does not provide
  the dual information used in classical Benders. Instead, cuts are generated through combinatorial arguments:
  *no-good cuts* are derived from proofs of subproblem infeasibility,
  while *combinatorial optimality cuts* are logical constraints that connect a specific set of master decisions
  to the resulting subproblem cost.


.. seealso::

   * A review of Benders Decomposition by Rahmaniani et al. [9]_.
   * A review of Jacques Benders' life and work by Aardal et al. [10]_.
   * A review of Integer Linear Programming that covers Benders Decomposition by Clautiaux and Ljubić [11]_.
   * Useful practical guidelines for implementing (Logic-based) Benders Decomposition (Section 2.7) [12]_.


Contents
-------------

.. toctree::
   :maxdepth: -1

   classical.rst
   cbd.rst
   lshaped.rst
   ilshaped.rst
   lbbd.rst
   gbd.rst
   enhance.rst

References
-------------

.. [1] Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
.. [2] Codato, G., & Fischetti, M. (2006). Combinatorial Benders’ cuts for mixed-integer linear programming. Operations Research, 54(4), 756–766. https://doi.org/10.1287/opre.1060.0286
.. [3] Geoffrion, A. M. (1972). Generalized Benders Decomposition. Journal of Optimization Theory and Applications, 10(4), 237–260. https://doi.org/10.1007/BF00934810
.. [4] Van Slyke, R. M., & Wets, R. (1969). L-shaped linear programs with applications to optimal control and stochastic programming. SIAM Journal on Applied Mathematics, 17(4), 638–663. https://doi.org/10.1137/0117061
.. [5] Laporte, G., & Louveaux, F. V. (1993). The integer L-shaped method for stochastic integer programs with complete recourse. Operations Research Letters, 13(3), 133–142. https://doi.org/10.1016/0167-6377(93)90002-X
.. [6] Birge, J. R. (1985). Decomposition and partitioning methods for multistage stochastic linear programs. Operations Research, 33(5), 989–1007. https://doi.org/10.1287/opre.33.5.989
.. [7] Hooker, J. N., & Ottosson, G. (2003). Logic-based Benders Decomposition. Mathematical Programming, 96(1), 33–60. https://doi.org/10.1007/s10107-003-0375-9
.. [8] Kelley, Jr., J. E. (1960). The cutting-plane method for solving convex programs. Journal of the Society for Industrial and Applied Mathematics, 8(4), 703–712. https://doi.org/10.1137/0108053
.. [9] Rahmaniani, R., Crainic, T. G., Gendreau, M., & Rei, W. (2017). The Benders Decomposition algorithm: A literature review. European Journal of Operational Research, 259(3), 801–817. https://doi.org/10.1016/j.ejor.2016.12.005
.. [10] Aardal, K., Hurkens, C., & Lenstra, J. K. (2025). Jacques Benders and his decomposition algorithm. Operations Research Letters, 63, 107361. https://doi.org/10.1016/j.orl.2025.107361
.. [11] Clautiaux, F., & Ljubić, I. (2025). Last fifty years of integer linear programming: A focus on recent practical advances. European Journal of Operational Research, 324(3), 707–731. https://doi.org/10.1016/j.ejor.2024.11.018
.. [12] Hooker, J. (2024). Logic-Based Benders Decomposition: Theory and Applications. Springer International Publishing. https://doi.org/10.1007/978-3-031-45039-6

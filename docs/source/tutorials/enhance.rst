Enhancements
====================================

Benders decomposition is a powerful technique for solving large-scale optimization problems,
but its convergence can be slow. To address this, various acceleration strategies have
been developed, which can be broadly categorized into two groups: those that
**speed up the solution of each iteration** and those that **reduce the total number of iterations**
required to find a solution.

.. seealso::

    We also recommend these papers [#]_ [#]_ [#]_ [#]_ [#]_ for taxonomies of acceleration strategies.

.. mermaid::
   :align: center
   :caption: Benders Decomposition Acceleration Strategies

   graph LR

       A(Benders Decomposition Acceleration Strategies);

       B(Speed Up Each Iteration);
       C(Reduce Number of Iterations);

       A --> B;
       A --> C;

       B1(Accelerate Master Problem Solving);
       B2(Accelerate Subproblem Solving);

       B --> B1;
       B --> B2;

       B1 --> B1a(Cut Management);
       B1 --> B1b(Warm Starting);
       B1 --> B1c(Branch and Check);

       B2 --> B2a(Parallelization);
       B2 --> B2d(Warm Starting);
       B2 --> B2b(CP and Algorithmic Solver);

       C1(Generate Stronger Cuts and Bounds);
       C2(Improve Convergence Quality and Stability);
       C3(Optimize Algorithm Control Flow);

       C --> C1;
       C --> C2;
       C --> C3;

       C1 --> C1a(Pareto-Optimal Cuts);
       C1 --> C1b(Global Valid Inequalities);
       C1 --> C1c(Cut Lifting);
       C2 --> C2a(Trust Region);
       C2 --> C2b(Cut Normalization);
       C3 --> C3a(Local Branching);
       C3 --> C3b(Early Stopping);

       classDef root fill:#0066CC,stroke:#333,color:#fff;
       classDef mainBranch fill:#5c9ce6,stroke:#333,color:#fff;
       classDef midLevel fill:#a9c9f7,stroke:#333,color:#000;
       classDef leaf fill:#fff,stroke:#333,color:#000;

       class A root;
       class B,C mainBranch;
       class B1,B2,C1,C2,C3 midLevel;
       class B1a,B1b,B1c,B2a,B2b,B2d,C1a,C1b,C1c,C2a,C2b,C3a,C3b leaf;

.. level-set method, in-out method

BendersLib is designed with a flexible and extensible architecture that facilitates the
implementation of these acceleration strategies. The library's :doc:`callback system <../manual/callbacks>` allows
for the integration of custom logic at various stages of the decomposition process.
This enables users to implement techniques such as warm starting, cut management,
and custom termination criteria. Additionally, the modular design of BendersLib
allows for the extension and customization of core components, such as :ref:`custom cut generators <manual_custom_cut>`
and :ref:`custom solvers <manual_custom_sub>`, making it possible to incorporate advanced methods like Pareto-optimal
cuts and local branching.

Introductions to some of these strategies are provided below.
Though they are not exhaustive, they serve as :doc:`examples <../manual/enhance>` of
how BendersLib can be used to implement various acceleration techniques.

Cut Management
------------------------------

Warm Starting
------------------------------

Warm starting [#]_ is a technique used to improve the performance of iterative optimization
algorithms by providing a good initial solution or starting point. In the context of
Benders decomposition, warm starting can be applied to both the master problem and
the subproblems. By providing a high-quality initial solution (e.g., from the previous iteration),
the effort required to solve the master problem and subproblems can be reduced.

.. admonition:: Example
    :class: seealso

    The example (:doc:`../examples/expert/warm_start`) demonstrates how to implement
    warm starting in BendersLib using :doc:`../manual/callbacks`.

Branch-and-Check Method
------------------------------

[#]_ [#]_ [#]_

Parallelization
------------------------------

CP and Algorithmic Solvers
------------------------------

When subproblems exhibit special combinatorial structures, using specialized algorithms
instead of general-purpose Mathematical Programming solvers can be significantly more efficient.
This is the core idea behind :doc:`lbbd` and :doc:`cbd`.
Constraint Programming (CP) is a powerful paradigm for solving combinatorial problems.
It can serve as a general purpose subproblem solver.
BendersLib facilitates this by providing :ref:`backends for CP solvers <solver-table>`,
allowing users to seamlessly integrate them for solving subproblems within the Benders decomposition framework.

.. admonition:: Example
    :class: seealso

    The example (:doc:`../examples/applications/lbbd_location`) demonstrates how to
    implement :ref:`customized subproblem solvers <manual_custom_sub>`
    within the :doc:`lbbd` framework using BendersLib.

Pareto-optimal Cut
------------------------------

[#]_  [#]_

Global Valid Inequalities
------------------------------

Global valid inequalities are constraints added to the master problem to strengthen
the formulation and accelerate convergence. Unlike traditional Benders cuts,
which are derived from specific subproblem solutions, these inequalities
are valid for the overall problem.
They often encapsulate a relaxation of the subproblem, expressed
in terms of master problem variables [#]_.
In stochastic programming, a global bound for the estimator variables of the
recourse function can tighten the master problem by providing stronger lower bound [#]_.
Symmetry breaking constraints also fall into this category.

.. admonition:: Note
    :class: seealso

    Global valid inequalities can be added at the beginning
    of the algorithm when building the master problem, using solver-specific APIs.
    They can also be added dynamically during the algorithm, using :doc:`../manual/callbacks`.

Cut Lifting
------------------------------

Trust Region Method
------------------------------

Cut Normalization
------------------------------

Cut normalization enhances numerical stability in Benders decomposition by scaling
cuts that have large coefficients and right-hand side (RHS) values. Multiplying
the cut by a factor produces an equivalent but more manageable cut, which can
improve convergence speed and reliability. A common normalization method is to
divide the cut by the norm of its coefficients.

.. admonition:: Example
    :class: seealso

    The example (:doc:`../examples/expert/normalize_cut`) demonstrates how to
    implement cut normalization in BendersLib using :doc:`../manual/callbacks`.

Local Branching
------------------------------

[#]_ [#]_

Early Stopping
------------------------------

Early stopping is a practical strategy to terminate the Benders decomposition process
before the theoretical optimality gap is closed. This is often done when the
improvement in the objective function becomes negligible over several iterations.
This can save significant computation time, especially when finding the
true optimal solution is not critical, and a good-enough solution is acceptable.

.. admonition:: Example
    :class: seealso

    The example :doc:`../examples/expert/early_stop` demonstrates how to implement
    early stopping in BendersLib using :doc:`../manual/callbacks`.

References
------------------------------

.. Review
.. [#] Rahmaniani, R., Crainic, T. G., Gendreau, M., & Rei, W. (2017). The Benders decomposition algorithm: A literature review. European Journal of Operational Research, 259(3), 801–817. https://doi.org/10.1016/j.ejor.2016.12.005
.. [#] Rahmaniani, R., Crainic, T. G., Gendreau, M., & Rei, W. (2018). Accelerating the Benders Decomposition Method: Application to Stochastic Network Design Problems. SIAM Journal on Optimization, 28(1), 875–903. https://doi.org/10.1137/17M1128204
.. [#] Hooker, J. (2024). Logic-Based Benders Decomposition: Theory and Applications. Springer International Publishing. https://doi.org/10.1007/978-3-031-45039-6
.. [#] Naderi, B., & Roshanaei, V. (2020). Branch-Relax-and-Check: A tractable decomposition method for order acceptance and identical parallel machine scheduling. European Journal of Operational Research, 286(3), 811–827. https://doi.org/10.1016/j.ejor.2019.10.014
.. [#] Nasirian, A., Zhang, L., Costa, A. M., & Abbasi, B. (2024). Multiskilled workforce staffing and scheduling: A logic-based benders’ decomposition approach. European Journal of Operational Research. https://doi.org/10.1016/j.ejor.2024.11.033

.. Warm Starting
.. [#] Bolusani, S., Besançon, M., Gleixner, A., Berthold, T., D’Ambrosio, C., Muñoz, G., Paat, J., & Thomopulos, D. (2024). The MIP Workshop 2023 Computational Competition on reoptimization. Mathematical Programming Computation. https://doi.org/10.1007/s12532-024-00256-w

.. Branch-and-Benders Method
.. [#] Thorsteinsson, E. S. (2001). Branch-and-check: A hybrid framework integrating mixed integer programming and constraint logic programming. In T. Walsh (Ed.), Principles and Practice of Constraint Programming—CP 2001 (pp. 16–30). Springer. https://doi.org/10.1007/3-540-45578-7_2
.. [#] Gendron, B., Scutellà, M. G., Garroppo, R. G., Nencioni, G., & Tavanti, L. (2016). A branch-and-Benders-cut method for nonlinear power design in green wireless local area networks. European Journal of Operational Research, 255(1), 151–162. https://doi.org/10.1016/j.ejor.2016.04.058
.. [#] Rubin, P. A. (2011, October 9). Benders Decomposition Then and Now. OR in an OB World. https://orinanobworld.blogspot.com/2011/10/benders-decomposition-then-and-now.html

.. Pareto-optimal cuts
.. [#] Magnanti, T. L., & Wong, R. T. (1981). Accelerating Benders Decomposition: Algorithmic Enhancement and Model Selection Criteria. Operations Research, 29(3), 464–484. https://doi.org/10.1287/opre.29.3.464
.. [#] Kaltis, T., & Saharidis, G. K. D. (2025). Literature review on Benders cut selection and a multiple cut generation scheme. INFOR: Information Systems and Operational Research. https://www.tandfonline.com/doi/abs/10.1080/03155986.2025.2540205

.. Global Valid Inequalities
.. [#] Hooker, J. N. (2019). Logic-based Benders decomposition for large-scale optimization. In J. M. Velásquez-Bermúdez, M. Khakifirooz, & M. Fathi (Eds.), Large Scale Optimization in Supply Chains and Smart Manufacturing: Theory and Applications (pp. 1–26). Springer International Publishing. https://doi.org/10.1007/978-3-030-22788-3_1
.. [#] Guo, P., & Zhu, J. (2023). Capacity reservation for humanitarian relief: A logic-based Benders decomposition method with subgradient cut. European Journal of Operational Research, 311(3), 942–970. https://doi.org/10.1016/j.ejor.2023.06.006

.. Local Branching
.. [#] Fischetti, M., & Lodi, A. (2003). Local branching. Mathematical Programming, 98(1), 23–47. https://doi.org/10.1007/s10107-003-0395-5
.. [#] Rei, W., Cordeau, J.-F., Gendreau, M., & Soriano, P. (2009). Accelerating Benders Decomposition by Local Branching. INFORMS Journal on Computing, 21(2), 333–345. https://doi.org/10.1287/ijoc.1080.0296

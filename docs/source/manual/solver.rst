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
Guide on building solver models can be found in the official documentation of each solver.

.. list-table:: Built-in Solver and Modeling Language Interfaces
    :widths: 20 15 15 50 50
    :header-rows: 1
    :name: solver-table

    * - Solver
      - Class
      - Type
      - Documentation
      - Note
    * - **Gurobi**
      - :class:`~.solvers.Gurobi`
      - MP
      - https://docs.gurobi.com
      - Commercial (free academic license)
    * - **COPT**
      - :class:`~.solvers.Copt`
      - MP
      - https://guide.coap.online/copt/en-doc/
      - Commercial (free academic license)
    * - **Pyomo** *
      - :class:`~.solvers.Pyomo`
      - ML
      - https://pyomo.readthedocs.io/en/stable/
      - Open-source modeling language supporting
        `multiple solvers <https://pyomo.readthedocs.io/en/stable/getting_started/solvers.html>`_.
    * - SCIP
      -
      - MP
      -
      - Open-source
    * - IPOPT
      -
      - MP (NLP)
      -
      - Open-source
    * - MOSEK
      -
      - MP (NLP)
      -
      - Commercial (free academic license)
    * - KNITRO
      -
      - MP (NLP)
      -
      - Commercial
    * - Baron
      -
      - MP (NLP)
      -
      - Commercial
    * - OR-Tools
      -
      - CP
      -
      - Open-source CP/SAT solver.
    * - CVXPY
      -
      - ML
      -
      - Open-source modeling language.
    * - AMPL
      -
      - ML
      -
      - Commercial modeling language supporting
        `multiple solvers <https://dev.ampl.com/solvers/index.html>`__.

*\* Note: Pyomo supported solvers need to be installed separately, see*
`installation instruction <https://pyomo.readthedocs.io/en/stable/getting_started/solvers.html>`_
*and* `supported solvers <https://github.com/Pyomo/pyomo/tree/main/pyomo/solvers/plugins/solvers>`_.
*MP: Mathematical Programming, CP: Constraint Programming, ML: Modeling Language.*

.. admonition:: Mathematical Programming vs. Constraint Programming
    :class: tip

    Mathematical Programming and Constraint Programming are two different paradigms for solving optimization problems.
    They have distinct approaches and are suited for different types of problems.
    A wise choice between the two can lead to more efficient problem-solving.

    .. list-table::
       :widths: 25 37 38
       :header-rows: 1

       * - Feature
         - Mathematical Programming
         - Constraint Programming
       * - **Origin**
         - Operations Research (OR)
         - Artificial Intelligence (AI)
       * - **Core Idea**
         - Optimize a specific objective function subject to a set of constraints.
         - Find a feasible solution that satisfies all constraints, without necessarily having an objective function.
       * - **Typical Techniques**
         - Simplex method, interior-point methods.
         - Backtracking, constraint propagation, and local search.
       * - **Best Suited For**
         - Problems with quantitative variables and linear/nonlinear relationships.
         - Problems with combinatorial structures and discrete variables.

    There are many successful attempts that **combing both paradigms**.
    Specifically in the :doc:`../tutorials/lbbd` famework,
    master problems are often modeled using Mathematical Programming,
    while subproblems can be modeled using Constraint Programming to leverage its strengths in handling combinatorial constraints.

**Using a solver not listed here? No worries!**

See the next section on how to create a custom solver interface,
and see :ref:`Custom Subproblem <manual_custom_sub>` for even simpler ways to use custom solvers for subproblems.

====

.. _manual_custom_solver_interface:

Customization
-------------------------------------------

BendersLib is designed to be extensible, allowing you to integrate solvers that are not natively supported.
This is achieved by creating a custom solver interface.

To add a new solver, you need to create a class that inherits from :class:`SolverBase`.
This base class serves as a template for all solver interfaces in BendersLib.
The :class:`SolverBase` is an `Abstract Base Class (ABC) <https://docs.python.org/3/library/abc.html>`_,
a feature from Python.
ABCs are used to define interfaces,
meaning a concrete class that inherits from an ABC must implement all of its
`abstract methods <https://docs.python.org/3/library/abc.html#abc.abstractmethod>`_.
This ensures that every solver interface in BendersLib provides a consistent set of functionalities.
When you create your custom solver class,
you must inherit from :class:`SolverBase` and provide implementations for all methods decorated with ``@abstractmethod``,
and define all attributes defined in :class:`SolverBase`.

While :class:`SolverBase` defines several abstract methods that you must implement,
two methods, :meth:`~SolverBase.make_master_problem` and :meth:`~SolverBase.make_sub_problem`,
have special considerations.
These methods are essential for the :class:`AnnotationBenders` class,
which automates the decomposition process.
If you do not intend to use :class:`AnnotationBenders`,
you might not need to implement the full logic for these methods.
However, for a solver interface to be considered for contribution to the official BendersLib repository,
a complete and functional implementation of these methods is required to ensure full compatibility with all library features.

To see a practical implementation, you can refer to the source code of the built-in solver interfaces,
such as :class:`~.solvers.Gurobi`.
Examining how it inherits from :class:`SolverBase` and implements the required methods will provide a clear
and effective template for creating your own custom solver.

.. note::

   *Contributing solver interfaces to BendersLib is welcome!*
   See :doc:`contribution` for guidelines.

====

Attributes & Methods
-------------------------------------------

Below are the attributes and methods of the base solver interface :class:`SolverBase`.
Any built-in solver interface (e.g., :class:`~.solvers.Gurobi`) is inherited from this base class,
meaning they have these attributes and methods.
Adding a new solver interface requires implementing these attributes and methods,
especially the `abstract methods <https://docs.python.org/3/library/abc.html#abc.abstractmethod>`_.
See :class:`SolverBase` for the comprehensive API reference, and :doc:`built-in solver interfaces <../api/solver>` for examples.

.. mermaid::
    :caption: Solver Interface Inheritance Diagram
    :align: center

    flowchart TB
        Gurobi -- inherits --> SolverBase
        COPT -- inherits --> SolverBase
        Pyomo -- inherits --> SolverBase

.. attention::

    The solver interfaces are not designed to be used directly by end-users.
    Use :class:`MasterProblem` and :class:`SubProblem` instead,
    which internally utilize the solver interfaces to interact with the optimization solvers.

.. rubric:: :class:`SolverBase` - Attributes

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
   ~SolverBase._constr_num

.. tip::

    Use :attr:`SolverBase._solver_model` to access to more attributes.

.. rubric:: :class:`SolverBase` - Methods

.. autosummary::
   :nosignatures:

   ~SolverBase.add_estimators
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

.. seealso::

    * Base Class: :class:`SolverBase`
    * Solver Interfaces: :class:`~.solvers.Gurobi`, :class:`~.solvers.Copt`

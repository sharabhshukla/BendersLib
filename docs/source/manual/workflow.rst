Workflow
====================================

.. currentmodule:: benderslib

Basic Usage
------------------------------------

In the basic scenario, you can use the built-in Benders decomposition methods provided by BendersLib.
This approach is suitable for standard problems that align with one of the
:doc:`predefined Benders decomposition frameworks <../tutorials/index>`.
BendersLib offers several :doc:`implementation of the Benders variants <../api/benders>`
and the necessary :doc:`Benders cuts <../api/cut>` and :doc:`cut generators <../api/benders>`.

.. mermaid::
  :caption: Basic Usage Workflow
  :align: center

   sequenceDiagram
       actor User
       participant BendersLib
       participant External Solver

       User->>BendersLib: 1. Define master and subproblems
       User->>BendersLib: 2. Create Benders object
       BendersLib->>BendersLib: Initialize Benders object
       User->>BendersLib: 3. Set parameters (optional)
       User->>BendersLib: 4. solve()
       loop Benders Iteration
           BendersLib->>External Solver: Solve master problem
           External Solver-->>BendersLib: Master problem solution
           BendersLib->>External Solver: Solve subproblems
           External Solver-->>BendersLib: Subproblem solutions
           BendersLib->>BendersLib: Generate and add cuts
           BendersLib->>BendersLib: Check convergence criteria
       end
       BendersLib-->>User: 5. Return solution

The workflow involves modeling the master and subproblems using a
:doc:`supported solver interface <solver>`,
and then passing these models to the Benders class specified for your chosen decomposition method.
You can then configure :class:`BendersParams` such as convergence tolerance and maximum iterations
before invoking the :class:`BendersSolver.solve()` method.
The BendersLib handles the iterative process of solving the master problem, passing the solution to the subproblems,
and generating the necessary optimality and feasibility cuts automatically.

.. seealso::

    * See :ref:`Built-in Benders Methods <manual_builtin_benders>` for more details on using built-in Benders methods.
    * See :doc:`../tutorials/index` for the theory of the above Benders methods.

Advanced Usage
------------------------------------

For more complex problems that do not fit the standard Benders decomposition patterns,
BendersLib offers an advanced usage mode.
This mode provides the flexibility to customize subproblem solver and cut generator, which are the
key components of the Benders algorithm.
This feature is especially useful for implementing :doc:`../tutorials/lbbd`,
as it allows the subproblem to be any type of optimization problem without a standard method for formulating Benders cuts.

.. mermaid::
   :caption: Advanced Usage Workflow
   :align: center

   sequenceDiagram
       actor User
       participant BendersLib
       participant Custom Solver
       participant Custom Cut Generator
       participant External Solver

       User->>BendersLib: 1. Define master problems
       User->>Custom Solver: 2. Define custom subproblem solver
       User->>Custom Cut Generator: 3. Define custom cut generator
       User->>BendersLib: 4. Create Benders object
       BendersLib->>BendersLib: Initialize Benders object
       Custom Solver-->>BendersLib: Register custom solver
       Custom Cut Generator-->>BendersLib: Register custom cut generator
       User->>BendersLib: 5. Set parameters (optional)
       User->>BendersLib: 6. solve()
       loop Benders Iteration
           BendersLib->>External Solver: Solve master problem
           External Solver-->>BendersLib: Master problem solution
           BendersLib->>Custom Solver: Solve subproblems
           Custom Solver-->>BendersLib: Subproblem solutions
           BendersLib->>Custom Cut Generator: Generate cuts
           Custom Cut Generator-->>BendersLib: Custom cuts
           BendersLib->>BendersLib: Add cuts to master problem
           BendersLib->>BendersLib: Check convergence criteria
       end
       BendersLib-->>User: 7. Return solution

Key customization options include:

- **Custom Subproblem Solver**:
  You are not limited to built-in solvers for the subproblems.
  You can implement a custom solver, which can be any algorithm or method that can solve the subproblem
  given a solution from the master problem.
  This is achieved by creating a class that inherits from :class:`LogicBasedSubProblem`.
  It is particularly useful for subproblems that have special structure that can be exploited by a specialized algorithm.

- **Custom Cut Generator**:
  You can define your own logic for generating optimality and feasibility cuts.
  This is done by creating a class that inherits from :class:`CutGenerator`,
  or by simply providing a function that returns a list of :class:`Cut` objects.
  When using a class-based approach, you can maintain state between iterations, which is important for
  cuts management and advanced acceleration techniques.
  This allows for the implementation of specialized cuts that can improve the convergence of the algorithm.

.. seealso::

    * See :ref:`Subproblem Customization <manual_custom_sub>` for more details on creating custom subproblem solvers.
    * See :ref:`Benders Cut Customization <manual_custom_cut>` for more details on creating custom cuts and cut generators.

Expert Usage
------------

This section covers expert-level features for fine-tuning the Benders decomposition algorithm,
including the use of :doc:`callbacks <callbacks>` for implementing custom acceleration strategies,
such as warm starts, cut management, and dynamic algorithm configuration.

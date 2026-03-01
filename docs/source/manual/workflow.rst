Workflow
====================================

.. currentmodule:: benderslib

Basic Usage
------------------------------------

In the basic scenario, you can use the built-in Benders decomposition methods provided by BendersLib.
This approach is suitable for standard problems that align with one of the
:doc:`predefined Benders decomposition frameworks <../tutorials/index>`.
BendersLib offers several :doc:`implementation of the Benders variants <../api/benders>`
and the necessary :doc:`Benders cuts <../api/cuts>` and :ref:`cut generators <cut_generators>`.

.. mermaid::
  :caption: Basic Usage Workflow
  :align: center

   sequenceDiagram
       actor User
       participant BendersLib
       participant Built-in Cut Generator
       participant Solver Interface

       User->>Solver Interface: 1. Define master & subproblems
       User->>BendersLib: 2. Create BendersSolver instance
       User->>BendersLib: 3. Set parameters (optional)
       User->>BendersLib: 4. solve()
       loop Benders Iteration
           Solver Interface-->>BendersLib: Return master/sub solution
           Built-in Cut Generator-->>BendersLib: Generate cuts
           BendersLib->>BendersLib: Check convergence & add cuts
       end
       BendersLib-->>User: 5. Return solution

The workflow involves modeling the master and subproblems using a
:doc:`supported solver interface <solvers>`,
and then passing these models to the Benders class specified for your chosen decomposition method.
You can then configure :class:`BendersParams` such as convergence tolerance and maximum iterations
before invoking the :class:`BendersSolver.solve()` method.
The BendersLib handles the iterative process of solving the master problem, passing the solution to the subproblems,
and generating the necessary optimality and feasibility cuts automatically.

.. seealso::

    * See :ref:`Built-in Benders Methods <manual_builtin_benders>` for more details on using built-in Benders methods.
    * See :doc:`../tutorials/index` for the theory of the above Benders methods.
    * Examples: :doc:`../examples/basic/index`.

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
       participant Custom Cut Generator
       participant Custom Solver
       participant Solver Interface

       User->>Solver Interface: 1. Define master problem
       User->>Custom Solver: 2. Define custom subproblem solver
       User->>Custom Cut Generator: 3. Define custom cut generator
       User->>BendersLib: 4. Create BendersSolver instance
       User->>BendersLib: 5. Set parameters (optional)
       User->>BendersLib: 6. solve()
       loop Benders Iteration
           Solver Interface-->>BendersLib: Return master solution
           Custom Solver-->>BendersLib: Return sub solution
           Custom Cut Generator-->>BendersLib: Generate cuts
           BendersLib->>BendersLib: Check convergence & add cuts
       end
       BendersLib-->>User: 7. Return solution

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
    * Examples: :doc:`tag: custom-cut <../_tags/custom-cut>` and :doc:`tag: custom-subproblem <../_tags/custom-subproblem>`.

Expert Usage
------------

This section covers expert-level features for fine-tuning the Benders decomposition algorithm,
including the use of :doc:`callbacks <callbacks>` for implementing custom
:doc:`acceleration strategies <../tutorials/enhance>`,
such as warm start, cut management, and cut selection.

.. mermaid::
   :caption: Expert Usage Workflow
   :align: center

   sequenceDiagram
       actor User
       participant BendersLib
       participant Custom Callbacks
       participant Solver Interface

       User->>Solver Interface: 1. Define master & subproblems
       User->>Custom Callbacks: 2. Define custom callbacks
       User->>BendersLib: 3. Create BendersSolver instance
       User->>BendersLib: 4. Set parameters (optional)
       User->>BendersLib: 5. solve()
       loop Benders Iteration
           Solver Interface-->>BendersLib: Return master/sub solution
           BendersLib-->>Custom Callbacks: Trigger callbacks during various events
           BendersLib->>BendersLib: Check convergence & add cuts
       end
       BendersLib-->>User: 6. Return solution

- **Custom Callbacks**:
  Callbacks allow for the injection of custom logic at various stages of the Benders decomposition algorithm.
  This is achieved by creating a class that inherits from :class:`CallbackBase` and implementing the desired methods.
  Callbacks can be used to implement acceleration strategies such as warm-starting the subproblems,
  managing the cut pool, or implementing custom termination criteria.

.. seealso::

    * See :doc:`callbacks` for more details on creating custom callbacks.
    * See :doc:`../tutorials/enhance` for more details on acceleration strategies.
    * Examples: :doc:`tag: callback <../_tags/callback>`.

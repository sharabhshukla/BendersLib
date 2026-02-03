Callbacks
====================================

.. currentmodule:: benderslib

What are Callbacks?
------------------------------------

This section provides an overview of the `callback <https://en.wikipedia.org/wiki/Callback_(computer_programming)>`_
system in BendersLib.
Callbacks are functions executed at specific events during the Benders decomposition,
allowing for monitoring and intervention.

The primary motivation for callbacks in BendersLib is to allow users to "hook into" the algorithm,
making it a flexible and extensible framework.
By providing hooks into the solver's lifecycle, callbacks enable monitoring progress,
extracting intermediate data, or customizing behavior without altering the core library.
They are the primary mechanism for extending the Benders decomposition with advanced strategies
like custom cut generation, problem-specific heuristics, and other acceleration techniques,
which can significantly improve performance, stability, and convergence.
See :doc:`enhance` for advanced acceleration techniques implemented via callbacks.

.. rubric:: Supported Callbacks

.. autosummary::
   :nosignatures:

   ~BendersCallback.on_benders_start
   ~BendersCallback.on_benders_end
   ~BendersCallback.on_iteration_start
   ~BendersCallback.on_iteration_end
   ~BendersCallback.on_master_build
   ~BendersCallback.on_before_master_solve
   ~BendersCallback.on_after_master_solve
   ~BendersCallback.on_new_lower_bound
   ~BendersCallback.on_sub_build
   ~BendersCallback.on_before_sub_solve
   ~BendersCallback.on_after_sub_solve
   ~BendersCallback.on_feas_cut_generated
   ~BendersCallback.on_opti_cut_generated
   ~BendersCallback.on_cut_generated
   ~BendersCallback.on_new_incumbent
   ~BendersCallback.on_new_upper_bound

.. mermaid

The callback system in BendersLib operates on an event-driven basis.
The :class:`BendersSolver` emits events at various stages of the decomposition process.
When an event is emitted, the solver checks for any registered callbacks corresponding
to that event and executes them sequentially.

How to Use Callbacks?
------------------------------------

There are two ways to create callbacks: as a class inheriting from :class:`BendersCallback` or as a standalone function.
Both approaches receive a :class:`BendersContext` object, which provides access to the master problem, subproblem,
and the current state of the decomposition.
The **class-based** callbacks are ideal for complex logic that requires maintaining state between events.
By defining a class, you can use instance attributes to store information across different callback calls.
The **function-based** callbacks is a simpler, more direct way to respond to events when you don not  need to
maintain state. Each callback function is independent.
A callback can also terminate the Benders process prematurely by returning the constant :attr:`~BendersConsts.TERMINATE`.

The following example demonstrates how to define and register both types of callbacks,
and how to use a callback to terminate the process.

.. code-block:: python

    from benderslib import ClassicalBenders, BendersCallback, BendersContext, BendersConsts
    from benderslib.solvers import Gurobi

    # --- 1. Define callbacks ---

    # Class-based callback
    class MyCallback(BendersCallback):
        def on_benders_start(self, context: BendersContext):
            print("Benders process has started.")

        def on_iteration_end(self, context: BendersContext):
            print(f"Iteration {context.state.n_iter} has ended.")
            # Terminate if the lower bound exceeds a certain value
            if context.state.lb > 500:
                print("Termination condition met. Stopping Benders process.")
                return BendersConsts.TERMINATE

    # Function-based callback
    def on_benders_end(context: BendersContext):
        print("Benders process has finished.")
        print(f"Final result: {context.state}")


    # --- 2. Initialize BendersSolver ---

    # (Assuming you have your master and subproblem models defined)
    # master_model = ...
    # sub_model = ...
    benders_solver = ClassicalBenders.from_models(
        master_model, Gurobi,
        sub_model, Gurobi,
        complicating_vars=complicating_vars
    )


    # --- 3. Register callbacks ---

    benders_solver.register_callback(MyCallback())
    benders_solver.register_callback(on_benders_end)

    # --- 4. Run the solver ---

    benders_solver.solve()

.. admonition:: Example
    :class: note

    :doc:`../examples/simple_callback`
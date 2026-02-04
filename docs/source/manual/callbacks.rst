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
   ~BendersCallback.on_new_upper_bound

The callback system in BendersLib operates on an event-driven basis.
The :class:`BendersSolver` emits events at various stages of the decomposition process.
When an event is emitted, the solver checks for any registered callbacks corresponding
to that event and executes them sequentially.
The following pseudocode illustrates the main stages of the Benders decomposition algorithm and the specific points at which each callback event is triggered.

.. parsed-literal::
   :class: benders-pseudocode
   :name: Timeline of Callback Triggers in Benders Decomposition

    // solve() method of BendersSolver is called
    trigger :meth:`~BendersCallback.on_master_build`
    trigger :meth:`~BendersCallback.on_sub_build`
    trigger :meth:`~BendersCallback.on_benders_start`

    while not converged:
        increment iteration counter
        trigger :meth:`~BendersCallback.on_iteration_start`

        trigger :meth:`~BendersCallback.on_before_master_solve`
        solve master problem
        trigger :meth:`~BendersCallback.on_after_master_solve`

        if master problem is optimal:
            trigger :meth:`~BendersCallback.on_before_sub_solve`
            solve subproblem
            trigger :meth:`~BendersCallback.on_after_sub_solve`

            if subproblem is optimal:
                if new lower bound is found:
                    trigger :meth:`~BendersCallback.on_new_lower_bound`
                if new upper bound is found:
                    trigger :meth:`~BendersCallback.on_new_upper_bound`

                if converged:
                    break

                generate optimality cut
                trigger :meth:`~BendersCallback.on_opti_cut_generated`
                add optimality cut to master problem

            else if subproblem is infeasible:
                if converged:
                    break

                generate feasibility cut
                trigger :meth:`~BendersCallback.on_feas_cut_generated`
                add feasibility cut to master problem

        else:
            // master problem is infeasible or unbounded
            break

        trigger :meth:`~BendersCallback.on_iteration_end`

    trigger :meth:`~BendersCallback.on_benders_end`


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

The following :doc:`example <../examples/simple_callback>` demonstrates how to define and register both types of callbacks.

.. literalinclude:: ../examples/simple_callback.py
    :lines: 39-
    :caption: Defining and registering callbacks in BendersLib

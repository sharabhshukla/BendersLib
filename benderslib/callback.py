# coding:utf-8

from abc import ABC
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

from .consts import BendersConsts as CST

# Avoid circular imports
if TYPE_CHECKING:
    from .core import BendersResult, MasterProblem, SubProblem, BendersSolver, Cut


@dataclass
class BendersContext:
    """Context information passed to Benders decomposition callbacks.

    This dataclass bundles the objects that callbacks commonly need while
    observing or interacting with a running Benders decomposition. It is
    passed as the sole argument to all callback methods in :class:`BendersCallback`.
    """

    benders: "BendersSolver"
    """The Benders decomposition solver instance."""
    master_problem: "MasterProblem"
    """The current master problem instance."""
    sub_problem: "SubProblem"
    """The current subproblem instance."""
    state: "BendersResult"
    """The current state of the Benders decomposition process."""
    cuts_generated: list["Cut"] = None
    """List of cuts generated but not yet added to the master problem."""

    def __str__(self):
        master_str = str(self.master_problem).replace('\n', '\n' + ' ' * 4)
        sub_str = str(self.sub_problem).replace('\n', '\n' + ' ' * 4)
        state_str = str(self.state).replace('\n', '\n' + ' ' * 4)
        return (f"{self.__class__.__name__}(\n"
                f"    master_problem={master_str},\n"
                f"    sub_problem={sub_str},\n"
                f"    state={state_str}\n"
                f")")


class BendersCallback(ABC):
    """Abstract base class for Benders decomposition callbacks.

    Users can define custom callbacks by inheriting from :class:`BendersCallback` and
    overriding the desired event methods. Each method receives a
    :class:`BendersContext` object containing information about the current
    state of the Benders decomposition process.
    Alternatively, users can define standalone functions with names matching
    the methods in :class:`BendersCallback` to serve as lightweight callbacks.

    If a callback returns the constant :attr:`~BendersConsts.TERMINATE` the Benders
    process will be terminated immediately.  Otherwise,
    returning ``None`` (or not returning) signals normal continuation.

    The callbacks are passed to Benders decomposition instances via :meth:`~BendersSolver.register_callback`.

    Example
    ---------------

    .. code-block:: python

        from benderslib import BendersCallback, BendersContext

        # Class-based callback
        class MyCallback(BendersCallback):

            def on_benders_start(self, context: BendersContext):
                print("Benders process started!")

        # Function-based callback
        def on_benders_end(self, context: BendersContext):
            print("Benders process finished!")

        BD = BendersSolver(...)
        BD.register_callback(MyCallback())
        BD.register_callback(on_benders_end)
    """

    def on_benders_start(self, context: BendersContext):
        """Called at the start of the Benders decomposition process."""
        ...

    def on_benders_end(self, context: BendersContext):
        """Called at the end of the Benders decomposition process."""
        ...

    def on_iteration_start(self, context: BendersContext):
        """Called at the start of each Benders decomposition iteration."""
        ...

    def on_iteration_end(self, context: BendersContext):
        """Called at the end of each Benders decomposition iteration."""
        ...

    def on_master_build(self, context: BendersContext):
        """Called after the master problem is built."""
        ...

    def on_sub_build(self, context: BendersContext):
        """Called after the subproblem is built."""
        ...

    def on_before_master_solve(self, context: BendersContext):
        """Called before solving the master problem."""
        ...

    def on_after_master_solve(self, context: BendersContext):
        """Called after solving the master problem."""
        ...

    def on_before_sub_solve(self, context: BendersContext):
        """Called before solving the subproblem."""
        ...

    def on_after_sub_solve(self, context: BendersContext):
        """Called after solving the subproblem."""
        ...

    def on_opti_cut_generated(self, context: BendersContext):
        """Called when an optimality cut is generated."""
        ...

    def on_feas_cut_generated(self, context: BendersContext):
        """Called when a feasibility cut is generated."""
        ...

    def on_new_lower_bound(self, context: BendersContext):
        """Called when a higher lower bound is found."""
        ...

    def on_new_upper_bound(self, context: BendersContext):
        """Called when a lower upper bound is found."""
        ...


class _CallbackEvents:
    """Enumeration of callback event names.

    The event names correspond to the method names in :class:`BendersCallback`,
    but are represented as uppercase strings.
    When define a function-based callback, the function takes the name of the event
    to be triggered.

    Example
    ---------------

    .. code-block:: python

        from benderslib import _CallbackEvents as EVENTS, BendersContext

        def example_callback_function(EVENTS.ON_BENDERS_START, context: BendersContext):
            print("Benders process started!")
    """

    ON_BENDERS_START = "ON_BENDERS_START"
    """See :meth:`BendersCallback.on_benders_start`."""
    ON_BENDERS_END = "ON_BENDERS_END"
    """See :meth:`BendersCallback.on_benders_end`."""
    ON_ITERATION_START = "ON_ITERATION_START"
    """See :meth:`BendersCallback.on_iteration_start`."""
    ON_ITERATION_END = "ON_ITERATION_END"
    """See :meth:`BendersCallback.on_iteration_end`."""
    ON_MASTER_BUILD = "ON_MASTER_BUILD"
    """See :meth:`BendersCallback.on_master_build`."""
    ON_SUB_BUILD = "ON_SUB_BUILD"
    """See :meth:`BendersCallback.on_sub_build`."""
    ON_BEFORE_MASTER_SOLVE = "ON_BEFORE_MASTER_SOLVE"
    """See :meth:`BendersCallback.on_before_master_solve`."""
    ON_AFTER_MASTER_SOLVE = "ON_AFTER_MASTER_SOLVE"
    """See :meth:`BendersCallback.on_after_master_solve`."""
    ON_BEFORE_SUB_SOLVE = "ON_BEFORE_SUB_SOLVE"
    """See :meth:`BendersCallback.on_before_sub_solve`."""
    ON_AFTER_SUB_SOLVE = "ON_AFTER_SUB_SOLVE"
    """See :meth:`BendersCallback.on_after_sub_solve`."""
    ON_OPTI_CUT_GENERATED = "ON_OPTI_CUT_GENERATED"
    """See :meth:`BendersCallback.on_opti_cut_generated`."""
    ON_FEAS_CUT_GENERATED = "ON_FEAS_CUT_GENERATED"
    """See :meth:`BendersCallback.on_feas_cut_generated`."""
    ON_NEW_LOWER_BOUND = "ON_NEW_LOWER_BOUND"
    """See :meth:`BendersCallback.on_new_lower_bound`."""
    ON_NEW_UPPER_BOUND = "ON_NEW_UPPER_BOUND"
    """See :meth:`BendersCallback.on_new_upper_bound`."""


class _CallbackManager:
    """Manager for handling multiple Benders decomposition callbacks.

    This class is initialized within :class:`BendersSolver` and is responsible for
    registering and triggering callbacks at appropriate events during the Benders
    decomposition process.
    """

    def __init__(self):
        self.callbacks: list[BendersCallback] = []

    def register(self, callback: BendersCallback | Callable):
        # Handle functions as callbacks
        if not isinstance(callback, BendersCallback):
            callback = _FuncWrapperCallback(callback)
        self.callbacks.append(callback)

    def trigger(self, event: str, context: BendersContext):
        for callback in self.callbacks:
            event = event.lower()
            method = getattr(callback, event, None)

            if callable(method):
                action = method(context)

                if action == CST.TERMINATE:
                    return CST.TERMINATE
        return CST.PROCEED


class _FuncWrapperCallback(BendersCallback):
    """A wrapper class to allow using functions as callbacks."""

    valid_events = [
        func for func in dir(BendersCallback)
        if callable(getattr(BendersCallback, func))
           and not func.startswith("__")
    ]

    def __init__(self, func):
        self._func = func

        if self._func.__name__ not in self.valid_events:
            raise ValueError(f"Function name '{self._func.__name__}' should be one of: {self.valid_events}")

        if hasattr(self._func, '__name__'):
            setattr(self, self._func.__name__, self._func)

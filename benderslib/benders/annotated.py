# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from typing import Type

from ..solvers import SolverBase
from ..core import BendersParams, MasterProblem, SubProblem, BendersSolver


class AnnotatedBenders(BendersSolver):
    """The class to perform Benders decomposition using annotation-based approach.

    This class decomposes the original problem into a master problem and a subproblem
    based on the specified complicating/master variables, and then applies the chosen Benders
    decomposition method to solve the problem.

    .. admonition:: Master problem variables vs. complicating variables
        :class: note

        The **master problem variables** are variables that appears only in the master problem.
        It has a subset, **complicating variables**, which are variables that are passed to the subproblem
        as known parameters.
        Though they are *sometimes identical*, the decomposition is based on the former.

    Parameters
    ----------
    original_problem:
        The original optimization problem in a solver-specific format.
    solver: Type[SolverBase]
        The solver class to be used for solving the master and subproblems, e.g., :class:`~.solvers.Gurobi`.
        It should be compatible with the :attr:`original_problem`.
    complicating_vars: list[str]
        A list of variable names that are considered complicating variables for the decomposition.
        The complicating variables are those that are passed to the subproblem as known parameters.
    master_vars: list[str], optional
        A list of variable names to be included in the master problem.
        The master variables are used to define the master problem and subproblem from the original problem.
        It is usually a superset of ``complicating_vars``.
        If not provided, it defaults to ``complicating_vars``.
    sub_solver: Type[SolverBase], optional
        A *different* solver class to be used for the **subproblem** only, e.g.,
        :class:`~.solvers.Jaxipm` when ``solver`` is :class:`~.solvers.Gurobi`.

        This lets you model the *overall* problem (and its master problem) in whichever
        general-purpose tool you already use -- :class:`~.solvers.Gurobi`, :class:`~.solvers.Copt`,
        :class:`~.solvers.Scip`, or :class:`~.solvers.Pyomo` -- while indicating that the
        subproblem specifically should be solved by a different backend. The subproblem model
        is converted from ``solver``'s format via the cross-backend model exchange
        (:meth:`~benderslib.solvers.SolverBase.to_structured` /
        :meth:`~benderslib.solvers.SolverBase.from_structured`). If not provided (default),
        the subproblem uses ``solver`` as well.

        .. note::
            ``solver`` must implement :meth:`~benderslib.solvers.SolverBase.to_structured`,
            and ``sub_solver`` must implement :meth:`~benderslib.solvers.SolverBase.from_structured`.
    master_solver: Type[SolverBase], optional
        The symmetric counterpart of ``sub_solver``: a *different* solver class to be used for
        the **master problem** only. Rarely needed, but available for completeness (e.g. to pair
        a MIP master modeled in one backend with a master solved by another).
    benders: Type[BendersSolver], optional
        The Benders decomposition method to be applied, e.g., :class:`ClassicalBenders`.
        If not provided, the class :class:`BendersSolver` will be used with the optimality
        and feasibility cut generators provided.
        If provided, parameters ``optimality_cut`` and ``feasibility_cut`` will be ignored,
        and the default cut generators of the chosen Benders method will be used.
    optimality_cut: Type[CutGenerator], optional
        The optimality cut generator to be used in the Benders decomposition.
        If not provided, the default optimality cut generator of the chosen Benders method ``benders`` will be used.
    feasibility_cut: Type[CutGenerator], optional
        The feasibility cut generator to be used in the Benders decomposition.
        If not provided, the default feasibility cut generator of the chosen Benders method ``benders`` will be used.
    params: BendersParams, optional
        An instance of :class:`BendersParams` containing parameters for the Benders decomposition process.
        If not provided, default parameters will be used.

    Caution
    -------
    - The ``solver`` should be a **class** (not an instance) that inherits from :class:`SolverBase`.
    - The ``benders`` should be a **class** (not an instance) that inherits from :class:`BendersSolver`.
    - The ``optimality_cut`` and ``feasibility_cut``, if provided, should be **classes** (not instances)
      that inherit from :class:`CutGenerator`.

    Example
    -------
    .. code-block:: python

        from benderslib import AnnotatedBenders, ClassicalBenders
        from benderslib.solvers import Gurobi

        original_problem = ...  # Define or load your original problem here
        complicating_vars = [...]  # List of complicating variable names
        master_vars = [...]  # List of master variable names (usually a superset of complicating_vars)

        BD = AnnotatedBenders(
            original_problem=original_problem,
            solver=Gurobi,
            benders=ClassicalBenders,
            complicating_vars=complicating_vars,
            master_vars=master_vars
        )

    Example: hybrid solving (Gurobi master + Jaxipm GPU subproblem)
    -------
    .. code-block:: python

        from benderslib import AnnotatedBenders, ClassicalBenders
        from benderslib.solvers import Gurobi, Jaxipm

        # Model the overall problem (and its master) in Gurobi as usual; indicate that the
        # subproblem specifically should be solved by Jaxipm on the GPU.
        BD = AnnotatedBenders(
            original_problem,
            solver=Gurobi,          # overall problem / master problem: Gurobi
            sub_solver=Jaxipm,      # subproblem: jaxipm (GPU interior-point)
            benders=ClassicalBenders,
            complicating_vars=["x"],
        )
    """

    def __new__(
            cls,
            original_problem,
            solver: Type[SolverBase],
            complicating_vars: list[str],
            master_vars: list[str] = None,
            sub_solver: Type[SolverBase] = None,
            master_solver: Type[SolverBase] = None,
            benders: Type[BendersSolver] = None,
            optimality_cut=None,
            feasibility_cut=None,
            params: BendersParams | None = None,
    ):
        master_vars = master_vars if master_vars is not None else complicating_vars
        master_problem, sub_problem = cls.decompose(
            original_problem, solver, master_vars, sub_solver=sub_solver, master_solver=master_solver
        )

        benders_kwargs = {
            "master_problem": master_problem,
            "sub_problem": sub_problem,
            "complicating_vars": complicating_vars,
            "params": params
        }

        if benders is None:
            benders = BendersSolver

        if optimality_cut is not None:
            benders_kwargs["optimality_cut"] = optimality_cut

        if feasibility_cut is not None:
            benders_kwargs["feasibility_cut"] = feasibility_cut

        return benders(**benders_kwargs)

    def __init__(self, *args, **kwargs):
        # This is intentionally left empty. The actual initialization is handled by the __new__ method,
        # which returns an instance of a different class (the one specified by the `benders` parameter).
        # By having AnnotatedBenders inherit from BendersSolver, documentation tools can correctly
        # identify and list the available methods.
        pass

    @staticmethod
    def decompose(
            original_problem,
            solver: Type[SolverBase],
            master_vars: list[str],
            solver_model=False,
            sub_solver: Type[SolverBase] = None,
            master_solver: Type[SolverBase] = None,
    ) -> tuple:
        """Decomposes the original problem into a master problem and a subproblem.

        It conducts automatic decomposition based on the given master variable names,
        using the methods :meth:`~benderslib.SolverBase.make_master_problem` and
        :meth:`~benderslib.SolverBase.make_sub_problem` provided by the solver interfaces.

        .. admonition:: Master problem variables vs. complicating variables
            :class: note

            The **master problem variables** are variables that appears only in the master problem.
            It has a subset, **complicating variables**, which are variables that are passed to the subproblem
            as known parameters.
            Though they are *sometimes identical*, the decomposition is based on the former.

        Parameters
        ----------
        original_problem:
            The original optimization problem in a solver-specific format.
        solver: Type[SolverBase]
            The solver class to be used for solving the master and subproblems.
        master_vars: list[str]
            A list of variable names to be included in the master problem.
        solver_model: bool, optional
            If ``True``, return the master and subproblem in the solver-specific format;
            If ``False``, return instances of :class:`MasterProblem` and :class:`SubProblem`.
        sub_solver: Type[SolverBase], optional
            A different solver class to be used for the subproblem only (see :class:`AnnotatedBenders`).
            The subproblem model is converted from ``solver``'s format via the cross-backend
            model exchange.
        master_solver: Type[SolverBase], optional
            A different solver class to be used for the master problem only (see :class:`AnnotatedBenders`).

        Returns
        -------
        tuple[MasterProblem, SubProblem] | tuple[object, object]
            A tuple containing the master problem and subproblem instances.

        Example
        --------
        .. code-block:: python

            from benderslib import AnnotatedBenders
            from benderslib.solvers import Gurobi

            original_problem = ...  # Define or load your original problem here
            master_vars = [...]  # List of master variable names (usually a superset of complicating_vars)

            master, sub = AnnotatedBenders.decompose(
                original_problem=original_problem,
                solver=Gurobi,
                master_vars=master_vars,
                solver_model=False  # (Default) Returns MasterProblem and SubProblem instances
            )
        """
        master = solver.make_master_problem(original_problem, master_vars)
        sub = solver.make_sub_problem(original_problem, master_vars)

        master_wrapper_cls = solver
        if master_solver is not None and master_solver is not solver:
            # Cross-backend model exchange: rebuild the master in master_solver's format.
            master = master_solver.from_structured(solver(master).to_structured())
            master_wrapper_cls = master_solver

        sub_wrapper_cls = solver
        if sub_solver is not None and sub_solver is not solver:
            # Cross-backend model exchange: rebuild the subproblem in sub_solver's format.
            sub = sub_solver.from_structured(solver(sub).to_structured())
            sub_wrapper_cls = sub_solver

        if solver_model:
            return master, sub
        else:
            return MasterProblem(master_wrapper_cls(master)), SubProblem(sub_wrapper_cls(sub))

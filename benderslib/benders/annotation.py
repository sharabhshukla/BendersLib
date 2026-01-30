# coding:utf-8

from typing import Type

from ..solvers import SolverBase
from ..core import BendersParams, MasterProblem, SubProblem, BendersSolver


class AnnotationBenders:
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
    benders: Type[BendersSolver]
        The Benders decomposition method to be applied, e.g., :class:`ClassicalBenders`.
    complicating_vars: list[str]
        A list of variable names that are considered complicating variables for the decomposition.
    master_vars: list[str], optional
        A list of variable names to be included in the master problem.
        It is usually a superset of ``complicating_vars``.
        If not provided, it defaults to ``complicating_vars``.
    optimality_cut: Type[CutGenerator], optional
        The optimality cut generator to be used in the Benders decomposition.
        If not provided, the default optimality cut generator of the chosen Benders method will be used.
    feasibility_cut: Type[CutGenerator], optional
        The feasibility cut generator to be used in the Benders decomposition.
        If not provided, the default feasibility cut generator of the chosen Benders method will be used.
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

        from benderslib import AnnotationBenders, ClassicalBenders
        from benderslib.solvers import Gurobi

        original_problem = ...  # Define or load your original problem here
        complicating_vars = [...]  # List of complicating variable names
        master_vars = [...]  # List of master variable names (usually a superset of complicating_vars)

        benders_solver = AnnotationBenders(
            original_problem=original_problem,
            solver=Gurobi,
            benders=ClassicalBenders,
            complicating_vars=complicating_vars,
            master_vars=master_vars
        )
    """

    def __init__(
            self,
            original_problem,
            solver: Type[SolverBase],
            benders: Type[BendersSolver],
            complicating_vars: list[str],
            master_vars: list[str] = None,
            optimality_cut=None,
            feasibility_cut=None,
            params: BendersParams = BendersParams(),
    ):
        master_vars = master_vars if master_vars is not None else complicating_vars
        master_problem, sub_problem = self.decompose(original_problem, solver, master_vars)

        # Attributes
        self.params = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""

        benders_kwargs = {
            "master_problem": master_problem,
            "sub_problem": sub_problem,
            "complicating_vars": complicating_vars,
            "params": self.params
        }
        if optimality_cut is not None:
            benders_kwargs["optimality_cut"] = optimality_cut
        if feasibility_cut is not None:
            benders_kwargs["feasibility_cut"] = feasibility_cut

        self.benders_instance = benders(**benders_kwargs)
        """The Benders decomposition instance initialized from the ``benders`` parameter."""
        self.result = self.benders_instance.result
        """An instance of :class:`BendersResult` that stores the results and statistics."""

    @staticmethod
    def decompose(
            original_problem,
            solver: Type[SolverBase],
            master_vars: list[str],
            solver_model=False
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

        Returns
        -------
        tuple[MasterProblem, SubProblem] | tuple[object, object]
            A tuple containing the master problem and subproblem instances.

        Example
        --------
        .. code-block:: python

            from benderslib import AnnotationBenders
            from benderslib.solvers import Gurobi

            original_problem = ...  # Define or load your original problem here
            master_vars = [...]  # List of master variable names (usually a superset of complicating_vars)

            master, sub = AnnotationBenders.decompose(
                original_problem=original_problem,
                solver=Gurobi,
                master_vars=master_vars,
                solver_model=False  # (Default) Returns MasterProblem and SubProblem instances
            )
        """
        master = solver.make_master_problem(original_problem, master_vars)
        sub = solver.make_sub_problem(original_problem, master_vars)

        if solver_model:
            return master, sub
        else:
            return MasterProblem(solver(master)), SubProblem(solver(sub))

    def solve(self, callback=None):
        """A wrapper method to solve the Benders decomposition instance.

        See :meth:`~benderslib.BendersSolver.solve` for details.
        """
        self.benders_instance.solve(callback)

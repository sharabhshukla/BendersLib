# coding:utf-8

from typing import Type

from .solver import SolverBase
from .core import BendersParams, MasterProblem, SubProblem, BendersSolver


class AnnotationBenders:
    """
    Class to perform Benders decomposition using annotation-based approach.
    This class decomposes the original problem into a master problem and a subproblem
    based on the specified complicating variables, and then applies the chosen Benders
    decomposition method to solve the problem.

    Parameters
    ----------
    original_problem:
        The original optimization problem in a solver-specific format.
    solver: Type[SolverBase]
        The solver class to be used for solving the master and subproblems, e.g., :class:`Gurobi`.
        It should be compatible with the :attr:`original_problem`.
    complicating_vars: list[str]
        A list of variable names that are considered complicating variables for the decomposition.
    benders: Type[BendersSolver]
        The Benders decomposition method to be applied, e.g., :class:`ClassicalBenders`.

    Caution
    -------
    - The parameter ``solver`` should be a **class** (not an instance) that inherits from :class:`SolverBase`.
    - The parameter ``benders`` should be a **class** (not an instance) that inherits from :class:`BendersSolver`.

    .. code-block:: python
        :emphasize-lines: 5, 7

        from benderslib import AnnotationBenders, ClassicalBenders, Gurobi, BendersParams

        benders_solver = AnnotationBenders(
            original_problem=original_problem,
            solver=Gurobi,  # Note: pass the class (without parentheses), not an instance
            complicating_vars=complicating_vars,
            benders=ClassicalBenders,  # Note: pass the class (without parentheses), not an instance
        )
    """

    def __init__(
            self,
            original_problem,
            solver: Type[SolverBase],
            complicating_vars: list[str],
            benders: Type[BendersSolver],
            optimality_cut=None,
            feasibility_cut=None,
            params: BendersParams = BendersParams(),
    ):
        self.complicating_vars = complicating_vars
        self.master_problem, self.sub_problem = self._decompose(original_problem, solver, complicating_vars)
        self.params = params

        benders_kwargs = {
            "master_problem": self.master_problem,
            "sub_problem": self.sub_problem,
            "complicating_vars": self.complicating_vars,
            "params": self.params
        }
        if optimality_cut is not None:
            benders_kwargs["optimality_cut"] = optimality_cut
        if feasibility_cut is not None:
            benders_kwargs["feasibility_cut"] = feasibility_cut

        self.benders_instance = benders(**benders_kwargs)
        """The Benders decomposition instance initialized from the ``benders`` parameter."""

        # Attributes
        self.result = self.benders_instance.result
        """An instance of :class:`BendersResult` that stores the results and statistics."""

    @staticmethod
    def _decompose(
            original_problem,
            solver: Type[SolverBase],
            complicating_vars: list[str],
            solver_model=False
    ) -> tuple:
        """
        Decomposes the original problem into a master problem and a subproblem
        based on the specified complicating variables.

        Parameters
        ----------
        original_problem:
            The original optimization problem in a solver-specific format.
        solver: Type[SolverBase]
            The solver class to be used for solving the master and subproblems.
        complicating_vars: list[str]
            A list of variable names that are considered complicating variables for the decomposition.
        solver_model: bool, optional
            If True, return the master and subproblem in the solver-specific format;
            If False, return instances of :class:`MasterProblem` and :class:`SubProblem`.

        Returns
        -------
        tuple[MasterProblem, SubProblem] | tuple[object, object]
            A tuple containing the master problem and subproblem instances.
        """
        solver_backend = solver(original_problem)
        master = solver_backend.make_master_problem(complicating_vars)
        sub = solver_backend.make_sub_problem(complicating_vars)
        if solver_model:
            return master, sub
        else:
            return MasterProblem(solver(master)), SubProblem(solver(sub))

    def solve(self, callback=None):
        """
        Call the ``solve`` method of the underlying Benders decomposition instance initialized from the ``benders``
        parameter, and store the result to the attribute :attr:`AnnotationBenders.result`.
        """
        self.benders_instance.solve(callback)
        self.result = self.benders_instance.result


if __name__ == '__main__':
    pass

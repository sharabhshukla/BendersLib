# coding:utf-8

from typing import Type

from .solver import SolverBase
from .core import BendersParams, MasterProblem, SubProblem, BendersBase


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
    benders: Type[BendersBase]
        The Benders decomposition method to be applied, e.g., :class:`ClassicalBenders`.

    Caution
    -------
    - The parameter ``solver`` should be a **class** (not an instance) that inherits from :class:`SolverBase`.
    - The parameter ``benders`` should be a **class** (not an instance) that inherits from :class:`BendersBase`.

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
            benders: Type[BendersBase],
            params: BendersParams = BendersParams(),
    ):
        self.complicating_vars = complicating_vars
        self.master_problem, self.sub_problem = self._decompose(original_problem, solver)
        self.params = params

        self.benders_instance = benders(
            master_problem=self.master_problem,
            sub_problem=self.sub_problem,
            complicating_vars=self.complicating_vars,
            params=self.params
        )
        """The Benders decomposition instance initialized from the ``benders`` parameter."""

        # Attributes
        self.result = self.benders_instance.result
        """An instance of :class:`BendersResult` that stores the results and statistics."""

    def _decompose(self, original_problem, solver: Type[SolverBase]) -> tuple[MasterProblem, SubProblem]:
        """
        Decomposes the original problem into a master problem and a subproblem
        based on the specified complicating variables.

        Parameters
        ----------
        original_problem:
            The original optimization problem in a solver-specific format.
        solver: Type[SolverBase]
            The solver class to be used for solving the master and subproblems.

        Returns
        -------
        tuple[MasterProblem, SubProblem]
            A tuple containing the master problem and subproblem instances.
        """
        solver_backend = solver(original_problem)
        master = solver_backend.make_master_problem(self.complicating_vars)
        sub = solver_backend.make_sub_problem(self.complicating_vars)
        return MasterProblem(solver(master)), SubProblem(solver(sub))

    def solve(self, callback=None):
        """
        Call the ``solve`` method of the underlying Benders decomposition instance initialized from the ``benders``
        parameter, and store the result to the attribute :attr:`AnnotationBenders.result`.
        """
        self.benders_instance.solve(callback)
        self.result = self.benders_instance.result

    def add_optimality_cut(self, var_values: dict):
        """
        Call the ``add_optimality_cut`` method of the underlying Benders decomposition
        instance initialized from the ``benders`` parameter.
        """
        return self.benders_instance.add_optimality_cut(var_values)

    def add_feasibility_cut(self, var_values: dict):
        """
        Call the ``add_feasibility_cut`` method of the underlying Benders decomposition
        instance initialized from the ``benders`` parameter.
        """
        return self.benders_instance.add_feasibility_cut(var_values)


if __name__ == '__main__':
    # TODO: support methods other than ClassicalBenders
    pass

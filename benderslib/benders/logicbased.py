# coding:utf-8

import inspect
from typing import Callable, Type

from ..core import (
    BendersParams,
    MasterProblem,
    SubProblem,
    SubProblems,
    BendersSolver,
    LogicBasedSubProblem,
    CutGenerator,
    _FuncWrapperSub
)


class LogicBasedBenders(BendersSolver):
    """An implementation of :doc:`../tutorials/lbbd`.

    The Logic-based Benders Decomposition is highly customizable.
    When using non-standard solvers that are not natively supported by BendersLib (typically heuristics or exact algorithms),
    users need to define their own subproblem, inheriting from :class:`LogicBasedSubProblem`.
    Users also need to implement their own optimality/feasibility cut generator, inheriting from :class:`CutGenerator`.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : LogicBasedSubProblem | SubProblem | Callable | SubProblems
        An instance of :class:`LogicBasedSubProblem` representing the subproblem.
        Alternatively, users can provide a function that takes the values of complicating variables as input
        and returns the optimal objective value and cut information.
    complicating_vars : list[str]
        A list of names of the complicating variables.
    optimality_cut : Type[CutGenerator] | Callable | None, optional
        A class inheriting from :class:`CutGenerator` (or a function) to generate optimality cuts.
        If not provided, no optimality cut will be added.
    feasibility_cut : Type[CutGenerator] | Callable | None, optional
        A class inheriting from :class:`CutGenerator` (or a function) to generate feasibility cuts.
        If not provided, no feasibility cut will be added.
    params : BendersParams, optional
        An instance of :class:`BendersParams` containing parameters for the Benders decomposition process.
        If not provided, default parameters will be used.

    Example
    ----------

    .. code-block:: python

        from benderslib import LogicBasedBenders, MasterProblem, LogicBasedSubProblem, CutGenerator
        from benderslib.solvers import Gurobi

        # Define master problem model
        master_model = ...  # Define your master problem model here
        mp = MasterProblem(Gurobi(master_model))

        # Define a custom logic-based subproblem
        class MyLogicBasedSubProblem(LogicBasedSubProblem):
            def solve():
                # Implement the logic to solve the subproblem given the complicating variable values
                self.status = ...
                self.obj = ...
                self.var_values = ...

        sp = MyLogicBasedSubProblem()

        # Define a custom optimality cut generator
        class MyOptimalityCutGenerator(CutGenerator):
            def generate_cut(self, master_solution, subproblem):
                cuts = []
                # Implement the logic to generate an optimality cut
                cut = ...
                cuts.append(cut)
                return cuts

        # Define complicating variables
        complicating_vars = ['x1', 'x2', 'x3']

        # Initialize and solve
        BD = LogicBasedBenders(mp, sp, complicating_vars, optimality_cut=MyOptimalityCutGenerator)
        BD.solve()
    """

    def __init__(
            self,
            master_problem: MasterProblem,
            sub_problem: LogicBasedSubProblem | SubProblem | Callable | SubProblems,
            complicating_vars: list[str],
            optimality_cut: Type[CutGenerator] | Callable | None = None,
            feasibility_cut: Type[CutGenerator] | Callable | None = None,
            params: BendersParams | None = None
    ):
        if inspect.isfunction(sub_problem):
            sub_problem = _FuncWrapperSub(complicating_vars, sub_problem)

        super().__init__(
            master_problem,
            sub_problem,
            complicating_vars,
            optimality_cut,
            feasibility_cut,
            params
        )

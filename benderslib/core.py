# coding:utf-8

import itertools
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Union, Iterable, Callable, Iterator
import inspect

from .consts import BendersConsts as CST
from .params import BendersParams
from .solver import SolverBase
from .logger import BendersLogger


@dataclass
class BendersResult:
    """
    Includes the results and statistics from the Benders decomposition process.
    """

    lb: float = -float('Inf')
    """Lower bound on the objective value."""
    lb_list: list = field(default_factory=list)
    """List of lower bounds over iterations."""
    ub: float = float('Inf')
    """Upper bound on the objective value."""
    ub_list: list = field(default_factory=list)
    """List of upper bounds over iterations."""
    obj: float = float('Inf')
    """Best objective value found."""
    gap_abs: float = float('Inf')
    """Absolute gap between upper and lower bounds, defined as `abs(ub - lb)`."""
    gap: float = float('Inf')
    """Relative gap between upper and lower bounds, defined as `abs(ub - lb) / abs(ub)`."""
    n_sol: int = 0
    """Number of feasible solutions found."""
    n_iter: int = 0
    """Number of Benders iterations performed."""
    runtime: float = 0.0
    """Total runtime of the Benders decomposition process."""
    runtime_master: float = 0.0
    """Total runtime spent solving the master problem."""
    runtime_sub: float = 0.0
    """Total runtime spent solving the subproblem."""
    n_opt_cuts: int = 0
    """Number of optimality cuts added."""
    n_feas_cuts: int = 0
    """Number of feasibility cuts added."""
    n_cuts: int = 0
    """Total number of optimality cuts and feasibility cuts added."""
    status = CST.UNSOLVED
    """Final status of the Benders decomposition process, see :class:`BendersConsts` for possible values."""

    # Values of decision variables in the best solution
    solution: dict = field(default_factory=dict)
    """Dictionary of variable names to their values in the best solution found."""

    def __str__(self):
        summary = (
            f"Benders Result:\n"
            f"  - {'Status:'.ljust(CST.LOG_NAME_WIDTH)}{self.status}\n"
            f"  - {'Incumbent:'.ljust(CST.LOG_NAME_WIDTH)}{self.obj:.4f}\n"
            f"  - {'Bound:'.ljust(CST.LOG_NAME_WIDTH)}{self.lb:.4f}\n"
            f"  - {'Gap (abs.):'.ljust(CST.LOG_NAME_WIDTH)}{self.gap_abs:.4f}\n"
            f"  - {'Gap (rel.):'.ljust(CST.LOG_NAME_WIDTH)}{self.gap:.2%}\n"
            f"  - {'Solutions No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.n_sol}\n"
            f"  - {'Iteration No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.n_iter}\n"
            f"  - {'Cuts No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.n_opt_cuts + self.n_feas_cuts}"
            f" [Optimality: {self.n_opt_cuts}, Feasibility: {self.n_feas_cuts}]\n"
            f"  - {'Solve Time (sec.):'.ljust(CST.LOG_NAME_WIDTH)}{self.runtime:.2f}"
            f" [Master: {self.runtime_master:.2f}, Sub: {self.runtime_sub:.2f}]"
        )
        return summary


class ProblemBase:
    """
    The base class for :class:`MasterProblem` and :class:`SubProblem` in Benders decomposition.

    Parameters
    ----------
    solver_backend : SolverBase
        An instance of a solver backend (e.g., :class:`Gurobi`) that implements the :class:`SolverBase` interface.
    complicating_vars : list, optional
        A list of names of the complicating variables in the master problem.
    """

    def __init__(self, solver_backend: SolverBase):
        self.model: SolverBase = solver_backend
        """The solver backend instance (e.g., :class:`Gurobi`) that implements the :class:`SolverBase`"""
        self._solver_model = self.model._solver_model
        """The underlying solver model instance (e.g., ``gurobipy.Model``)."""
        self.status = CST.UNSOLVED
        """The status of the problem, see :class:`BendersConsts` for possible values."""

    def __repr__(self):
        n_vars = len(self.model._all_vars)
        n = "Master Problem"
        if self.__class__.__name__ == "SubProblem":
            n_vars -= len(self.complicating_vars)
            n = "Sub Problem"

        return (
            f"{n}: \n"
            f" - {'Variable No.:'.ljust(CST.LOG_NAME_WIDTH)}{n_vars}"
            f" [Integer: {len(self.model._int_vars)}, Binary: {len(self.model._bin_vars)}]\n"
            f" - {'Constraint No.:'.ljust(CST.LOG_NAME_WIDTH)}{len(self._solver_model.getConstrs())}\n"
            f" - {'Solver:'.ljust(CST.LOG_NAME_WIDTH)}{self.model.__class__.__name__}"
        )

    def __getattr__(self, name):
        return getattr(self.model, name)

    def fix_vars(self, var_values: dict):
        """
        Fix the values of specified variables in the model.

        Parameters
        ---------------
        var_values : dict
            A dictionary mapping variable names to their fixed values.

        Example
        ---------------

        .. code-block:: python

                problem.fix_vars({'x1': 10, 'x2': 5.5})
        """
        self.model.fix_vars(var_values)

    def unfix_vars(self, vars: list[str]):
        """
        Unfix the specified variables in the model, restoring their original bounds.

        Parameters
        ---------------
        vars : list
            A list of variable names to be unfixed.

        Example
        ---------------

        .. code-block:: python

                problem.unfix_vars(['x1', 'x2'])
        """
        self.model.unfix_vars(vars)

    def get_var_values(self, vars: list[str] = None) -> dict[str, float | int]:
        """
        Get the current values of specified variables in the model.

        Parameters
        ---------------
        vars : list or None
            A list of variable names to retrieve values for. If None, retrieves values for all variables

        Returns
        ---------------
        dict[str, float]
            A dictionary mapping variable names to their current values.

        Example
        ---------------

        .. code-block:: python

                values = problem.get_var_values(['x1', 'x2'])
                # or get all variable values
                all_values = problem.get_var_values()

        """
        return self.model.get_var_values(vars)

    def get_var_coefs(self, vars: list[str] = None) -> dict[str, list]:
        """
        Get the coefficients of specified variables in all the constraints of the model.

        Parameters
        ---------------
        vars : list or None
            A list of variable names to retrieve coefficients for. If None, retrieves coefficients for all variables.

        Returns
        ---------------
        dict[str, list]
            A dictionary mapping variable names to a list of their coefficients in each constraint.

        Example
        ---------------
        .. code-block:: python

                coefs = problem.get_var_coefs(['x1', 'x2'])
                # or get coefficients for all variables
                all_coefs = problem.get_var_coefs()
        """
        return self.model.get_var_coefs(vars)

    def get_rhs(self) -> list[float | int]:
        """
        Get the right-hand side values of all constraints in the model.

        Returns
        ---------------
        list[float]
            A list of right-hand side values for each constraint.

        Example
        ---------------
        .. code-block:: python

                rhs = problem.get_rhs()
        """
        return self.model.get_rhs()

    def get_dual_values(self) -> list[float | int]:
        """
        Get the dual values (shadow prices) of all constraints in the model.
        This is essential for generating Classical Benders optimality cuts,
        which are used by :class:`ClassicalBenders`.

        Returns
        ---------------
        list[float]
            A list of dual values for each constraint.

        Example
        ---------------
        .. code-block:: python

                pi = problem.get_dual_values()
        """
        return self.model.get_dual_values()

    def get_extreme_ray(self) -> list[float | int]:
        """
        Get the extreme ray of the model.
        This is essential for generating Classical Benders feasibility cuts,
        which are used by :class:`ClassicalBenders`.

        Returns
        ---------------
        lst[float]
            A list representing the extreme ray.

        Example
        ---------------
        .. code-block:: python

                ray = problem.get_extreme_ray()
        """
        return self.model.get_extreme_ray()

    def get_obj(self) -> float:
        """
        Get the objective value of the model after solving.

        Returns
        ---------------
        float
            The objective value.

        Example
        ---------------
        .. code-block:: python

                obj_val = problem.get_obj()
        """
        return self.model.get_obj()

    def solve(self):
        """
        Solve :attr:`model` by calling :func:`SolverBase.solve()` and update the :attr:`status` attribute.
        """
        self.model.solve()
        self.status = self.model.status


class MasterProblem(ProblemBase):
    """
    The master problem in Benders decomposition.

    Parameters
    ----------
    solver_backend : SolverBase
        An instance of a solver backend (e.g., :class:`Gurobi`) that implements the :class:`SolverBase` interface.
    complicating_vars : list, optional
        A list of names of the complicating variables in the master problem.
    """

    def __init__(self, solver_backend: SolverBase, complicating_vars: list = None):
        self.complicating_vars = complicating_vars
        super().__init__(solver_backend)

        self.optimality_cuts: list[Cut] = []
        """List of optimality cuts (:class:`OptimalityCut`) added to the master problem."""
        self.feasibility_cuts: list[Cut] = []
        """List of feasibility cuts (:class:`FeasibilityCut`) added to the master problem."""

        self.__oc_id = itertools.count(1)
        self.__fc_id = itertools.count(1)

        self.__added_cut = set()

    def add_cut(self, cut):
        """
        Add a cut (optimality or feasibility) to the master problem, and update the corresponding cut lists
        :attr:`optimality_cuts` or :attr:`feasibility_cuts`.

        Parameters
        ----------
        cut : Cut
            An instance of :class:`Cut`, either an :class:`OptimalityCut` or :class:`FeasibilityCut`.

        Returns
        ----------
        str
            The name of the added cut in the master problem.
        """
        if cut in self._added_cut:
            # BendersLogger.warning(f"Warning: Duplicate cut detected: {cut}. This cut will not be added again.")
            return None
        else:
            self.__added_cut.add(cut)

        if cut.ctype == CST.OPTIMALITY:
            cut_id = f"OC{next(self.__oc_id)}"
            cut.cut_id = cut_id
            self.optimality_cuts.append(cut)
        else:
            cut_id = f"FC{next(self.__fc_id)}"
            cut.cut_id = cut_id
            self.feasibility_cuts.append(cut)

        cut_name = f"{cut.name}_{cut.cut_id}"
        self.model.add_cut(cut, name=cut_name)
        return cut_name

    def remove_cut(self, cut_name):
        """
        Remove a constraint from the solver's model by its name.

        Parameters
        ---------------
        cut_name : str
            The name of the constraint to be removed.

        Example
        ---------------
        .. code-block:: python

                problem.remove_cut('BendersOC_1')
        """
        self.model.remove_cut(cut_name)


class SubProblem(ProblemBase):
    """
    The sub problem in Benders decomposition.

    Parameters
    ----------
    solver_backend : SolverBase
        An instance of a solver backend (e.g., :class:`Gurobi`) that implements the :class:`SolverBase` interface.
    complicating_vars : list, optional
        A list of names of the complicating variables in the master problem.
    """

    def __init__(self, solver_backend: SolverBase, complicating_vars: list = None):
        self.complicating_vars = complicating_vars
        super().__init__(solver_backend)


class SubProblems:
    def __init__(
            self,
            sub_problems: Iterable['SubProblem'],
            prob: list[float] = None,
            estimators: list = None,
            multi_opti_cut: bool = False,
            multi_feas_cut: bool = False,
    ):
        self.sub_problems = list(sub_problems)
        self.prob = prob
        self.estimators = estimators
        self.multi_opti_cut = multi_opti_cut
        self.multi_feas_cut = multi_feas_cut

        self.status = CST.UNSOLVED
        """The status of the problem, see :class:`BendersConsts` for possible values."""

    def __repr__(self):
        return (
            f"Sub Problems: \n"
            f" - {'Scenario No.:'.ljust(CST.LOG_NAME_WIDTH)}{len(self.prob)}"
            # + self.sub_problems[0].__repr__().replace("Sub Problem: ", "")
        )

    def __iter__(self) -> Iterator['SubProblem']:
        return iter(self.sub_problems)

    def get_obj(self) -> float:
        objs = [sub.get_obj() for sub in self.sub_problems]
        return sum(ob * p for ob, p in zip(objs, self.prob))

    def fix_vars(self, var_values: dict):
        for sub in self.sub_problems:
            sub.fix_vars(var_values)

    def get_var_values(self, vars: list[str] = None):
        var_values = {}
        for i, sub in enumerate(self.sub_problems):
            var_values[i] = sub.get_var_values(vars)
        return var_values

    # def get_var_coefs(self, vars: list[str] = None):
    #     for sub in self.sub_problems:
    #         yield sub.get_var_coefs(vars)
    #
    # def get_rhs(self):
    #     for sub in self.sub_problems:
    #         yield sub.get_rhs()
    #
    # def get_dual_values(self):
    #     for sub in self.sub_problems:
    #         assert sub.status == CST.OPTIMAL, "Subproblem must be optimal to get dual values."
    #         yield sub.get_dual_values()
    #
    # def get_extreme_ray(self):
    #     for sub in self.sub_problems:
    #         assert sub.status == CST.INFEASIBLE, "Subproblem must be infeasible to get extreme ray."
    #         yield sub.get_extreme_ray()

    def solve(self):
        for sub in self.sub_problems:
            sub.solve()
            if sub.status == CST.INFEASIBLE and not self.multi_feas_cut:
                break

        if all(sub.status == CST.OPTIMAL for sub in self.sub_problems):
            self.status = CST.OPTIMAL
        elif any(sub.status == CST.INFEASIBLE for sub in self.sub_problems):
            self.status = CST.INFEASIBLE
        else:
            self.status = CST.ERROR
            raise RuntimeError("SubProblems status could not be determined.")


class Cut:
    """
    The base class for Benders cuts (:class:`OptimalityCut` or :class:`FeasibilityCut`) in Benders decomposition.

    Parameters
    ----------
    vars : list[str]
        A list of variable names involved in the cut.
    coefs : list[float | int]
        A list of coefficients corresponding to the variables in the cut.
    rhs : float | int
        The right-hand side value of the cut.
    sense : str
        The sense of the cut, must be in :attr:`senses`.
    ctype : str
        :attr:`BendersConsts.OPTIMALITY` or :attr:`BendersConsts.FEASIBILITY`.
    name : str
        A name for the cut.
    """

    senses = {CST.LE, CST.GE, CST.EQ}
    """Allowed senses for the cut, :attr:`BendersConsts.LE`, :attr:`BendersConsts.GE`, and :attr:`BendersConsts.EQ`."""

    def __init__(
            self,
            vars: list[str],
            coefs: list[float | int],
            rhs: float | int,
            sense: str,
            ctype: Union[CST.OPTIMAL, CST.FEASIBILITY],
            name: str,
    ):
        assert sense in self.senses, f"sense {sense} must be one of: {self.senses}"

        self.vars = vars
        self.coefs = coefs
        self.rhs = rhs
        self.sense = sense
        self.ctype = ctype
        self.name = name

        # Attributes
        self.cut_id = None
        """Unique identifier for the cut, assigned when the cut is added to the master problem."""

    def __repr__(self):
        return (f"{self.name} ({self.ctype}): "
                f"{' + '.join(f'{a} * {b}' for a, b in zip(self.coefs, self.vars))} "
                f"{self.sense} {self.rhs}")

    def __eq__(self, other):
        if not isinstance(other, Cut):
            raise TypeError(f"Can only compare <Cut> with another <Cut>, <{type(other)}> is given.")

        # Sort by variable name to ensure order doesn't matter
        self_sorted_pairs = tuple(sorted(zip(self.vars, self.coefs)))
        other_sorted_pairs = tuple(sorted(zip(other.vars, other.coefs)))

        return (
                self.ctype == other.ctype and
                self.sense == other.sense and
                self.rhs == other.rhs and
                self_sorted_pairs == other_sorted_pairs
        )

    def __hash__(self):
        # Sort by variable name to ensure hash is consistent
        sorted_pairs = tuple(sorted(zip(self.vars, self.coefs)))
        return hash((sorted_pairs, self.rhs, self.sense, self.ctype))


class OptimalityCut(Cut):
    """
    Class for optimality cuts in Benders decomposition.

    Parameters
    ----------
    vars : list[str]
        A list of variable names involved in the cut.
    coefs : list[float | int]
        A list of coefficients corresponding to the variables in the cut.
    rhs : float | int
        The right-hand side value of the cut.
    sense : str
        The sense of the cut, must be in :attr:`senses`.
    name : str
        A name for the cut.
    """

    def __init__(self, vars, coefs, rhs, sense, name="OC"):
        super().__init__(vars, coefs, rhs, sense, CST.OPTIMALITY, name)


class FeasibilityCut(Cut):
    """
    Class for feasibility cuts in Benders decomposition.

    Parameters
    ----------
    vars : list[str]
        A list of variable names involved in the cut.
    coefs : list[float | int]
        A list of coefficients corresponding to the variables in the cut.
    rhs : float | int
        The right-hand side value of the cut.
    sense : str
        The sense of the cut, must be in :attr:`senses`.
    name : str
        A name for the cut.
    """

    def __init__(self, vars, coefs, rhs, sense, name="FC"):
        super().__init__(vars, coefs, rhs, sense, CST.FEASIBILITY, name)


class CutGenerator(ABC):
    """
    A base class for cut generators in Benders decomposition.
    Any specific cut generation method (e.g., :class:`ClassicalOC`) should inherit from this class
    and implement the abstract method :meth:`generate`.
    Attributes that will not change during the Benders process should be ideally initialized in `__init__`
    for efficiency.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : SubProblem | SubProblems
        An instance of :class:`SubProblem` representing the subproblem,
        or :class:`SubProblems` for multiple subproblems.
    """

    def __init__(self, master_problem: MasterProblem, sub_problem: SubProblem | SubProblems):
        self._master_problem = master_problem
        """The master problem instance."""
        self._sub_problem = sub_problem
        """The subproblem instance."""
        self._complicating_vars = master_problem.complicating_vars
        """List of names of the complicating variables."""

        assert set(self._complicating_vars) == set(sub_problem.complicating_vars), \
            "Complicating variables in master and subproblem must match."

    @abstractmethod
    def generate(self) -> list['OptimalityCut'] | list['FeasibilityCut']:
        """
        This method should be implemented to generate cuts based on the current state of the master and subproblem(s).
        """
        ...


class _FuncWrapperCut(CutGenerator):
    """
    A wrapper class to allow using a function as a cut generator.
    """

    def __init__(self, master_problem, sub_problem, func: Callable):
        self._func = func
        super().__init__(master_problem, sub_problem)

    def generate(self):
        return self._func(self._master_problem, self._sub_problem)


class BendersSolver:
    """
    The core class for Benders decomposition methods.
    Any specific Benders decomposition method (e.g., :class:`ClassicalBenders`) is inherited from this class.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : SubProblem | SubProblems
        An instance of :class:`SubProblem` representing the subproblem,
        or :class:`SubProblems` for multiple subproblems.
    complicating_vars : list[str]
        A list of names of the complicating variables in the master problem.
    optimality_cut : Type[CutGenerator], optional
        An abstract class that inherits from :class:`CutGenerator` to be used for generating optimality
        cuts.
        It also accepts a function with signature ``func(master_problem, sub_problem) -> list[OptimalityCut]``.
        If `None`, no optimality cuts will be added.
    feasibility_cut : Type[CutGenerator], optional
        An abstract class that inherits from :class:`CutGenerator` to be used for generating feasibility
        cuts.
        It also accepts a function with signature ``func(master_problem, sub_problem) -> list[FeasibilityCut]``.
        If `None`, no feasibility cuts will be added.
    params : BendersParams, optional
        An instance of :class:`BendersParams` containing parameters for the Benders decomposition process.
        If not provided, default parameters will be used.

    Caution
    -------
    The ``optimality_cut`` parameter requires the ``CutGenerator``'s subclass itself, not an instance.
    For example, use ``ClassicalOC``, not ``ClassicalOC()``.
    This also applies to the ``feasibility_cut`` parameter.

    .. code-block:: python
        :emphasize-lines: 3

        from benderslib import ClassicalBenders, ClassicalOCGen, ClassicalFCGen

        BD = ClassicalBenders(mp, sp, com_vars, optimality_cut=ClassicalOC, feasibility_cut=ClassicalFC)

        # Wrong
        # BD = ClassicalBenders(mp, sp, com_vars, optimality_cut=ClassicalOC(), feasibility_cut=ClassicalFC())
    """

    def __init__(
            self,
            master_problem: MasterProblem,
            sub_problem: SubProblem | SubProblems,
            complicating_vars: list[str],
            optimality_cut=None,
            feasibility_cut=None,
            params: BendersParams = BendersParams()
    ):
        master_problem.complicating_vars = complicating_vars
        sub_problem.complicating_vars = complicating_vars

        self.master_problem = master_problem
        self.sub_problem = sub_problem
        self.complicating_vars = complicating_vars

        if inspect.isfunction(optimality_cut):
            self.optimality_cut = _FuncWrapperCut(master_problem, sub_problem, optimality_cut)
        elif inspect.isclass(optimality_cut):
            self.optimality_cut = optimality_cut(master_problem, sub_problem)
        elif optimality_cut is not None:
            raise ValueError("<optimality_cut> must be a <function> or a <class>.")

        if inspect.isfunction(feasibility_cut):
            self.feasibility_cut = _FuncWrapperCut(master_problem, sub_problem, feasibility_cut)
        elif inspect.isclass(feasibility_cut):
            self.feasibility_cut = feasibility_cut(master_problem, sub_problem)
        elif feasibility_cut is not None:
            raise ValueError("<feasibility_cut> must be a <function> or a <class>.")

        assert self.optimality_cut or self.feasibility_cut, "Provide at least <optimality_cut> or <feasibility_cut>."

        self.params = params

        # Attributes
        self.result = BendersResult()
        """An instance of :class:`BendersResult` that stores the results and statistics."""
        self.__logger = BendersLogger(self)
        """An instance of :class:`BendersLogger` for handling logging."""

    def __str__(self):
        all_model_com_vars = {self.master_problem._solver_model.getVarByName(v) for v in self.complicating_vars}
        integer_num = len([v for v in all_model_com_vars if v.VType == 'I'])
        binary_num = len([v for v in all_model_com_vars if v.VType == 'B'])
        continuous_num = len([v for v in all_model_com_vars if v.VType == 'C'])

        return (
            f"Benders Decomposition:\n"
            f" - {'Method:'.ljust(CST.LOG_NAME_WIDTH)}{self.__class__.__name__}\n"
            f" - {'Complicating Var. No.:'.ljust(CST.LOG_NAME_WIDTH)}{len(self.complicating_vars)}"
            f" [Integer: {integer_num}, Binary: {binary_num}, Continuous: {continuous_num}]\n"
            f" - {'Optimality Cut:'.ljust(CST.LOG_NAME_WIDTH)}{self.optimality_cut.__class__.__name__ or None}\n"
            f" - {'Feasibility Cut:'.ljust(CST.LOG_NAME_WIDTH)}{self.feasibility_cut.__class__.__name__ or None}"

        )

    def _add_optimality_cut(self):
        """
        The method to add one or multiple :class:`OptimalityCut` to :class:`MasterProblem`.
        """
        cuts = self.optimality_cut.generate()
        for cut in cuts:
            self.master_problem.add_cut(cut)

    def _add_feasibility_cut(self):
        """
        The method to add one or multiple :class:`FeasibilityCut` to :class:`MasterProblem`.
        """
        cuts = self.feasibility_cut.generate()
        for cut in cuts:
            self.master_problem.add_cut(cut)

    def __update_result(self, time_start):
        self.result.n_sol += 1
        self.result.status = CST.FEASIBLE

        self.result.lb = self.master_problem.get_obj()
        theta = self.master_problem.get_var_values(['theta'])['theta']
        self.result.ub = self.result.lb - theta + self.sub_problem.get_obj()

        if self.result.ub < self.result.obj:
            self.result.obj = self.result.ub
            self.result.solution = self.sub_problem.get_var_values()

        self.result.gap_abs = abs(self.result.obj - self.result.lb)
        if abs(self.result.ub) > self.params.tol_abs:
            # Non-zero ub
            self.result.gap = self.result.gap_abs / abs(self.result.ub)
        else:
            # Zero ub
            self.result.gap = 0 if self.result.lb == 0 else float('Inf')
        self.result.lb_list.append(self.result.lb)
        self.result.ub_list.append(self.result.ub)
        self.result.runtime = time.perf_counter() - time_start

    def __terminate(self, time_start):
        # Iteration limit
        if self.result.n_iter >= self.params.iter_limit:
            self.result.status = CST.TIMEOUT
            return True

        # Time limit
        if time.perf_counter() - time_start >= self.params.time_limit:
            self.result.status = CST.TIMEOUT
            return True

        # Optimality
        if any([
            self.result.gap <= self.params.tol_rel,
            self.result.gap_abs <= self.params.tol_abs,
        ]):
            self.result.status = CST.OPTIMAL
            return True

        return False

    def solve(self, callback=None) -> None:
        """
        Solve the Benders decomposition problem using the specified Benders decomposition method.
        This method implements the main Benders decomposition algorithm, iteratively solving the master and
        subproblems, adding cuts, and updating the results until convergence or stopping criteria are met.

        .. Note::

            After calling this method, the results and statistics of the Benders decomposition process can be accessed
            through the :attr:`BendersSolver.result` attribute, which is an instance of :class:`BendersResult`.

            .. code-block:: python
                :emphasize-lines: 4

                # Example usage:
                BD = ClassicalBenders(master_problem, sub_problem, complicating_vars)
                BD.solve()
                print(BD.result)

                # Output:
                Benders Result:
                  - Status:                  OPTIMAL
                  - Incumbent:               2.0000
                  - Bound:                   2.0000
                  - Gap (abs.):              0.0000
                  - Gap (rel.):              0.00%
                  - Solutions No.:           1
                  - Iteration No.:           3
                  - Cuts No.:                2 [Optimality: 0, Feasibility: 2]
                  - Solve Time (sec.):       0.00 [Master: 0.00, Sub: 0.00]

        Parameters
        ----------
        callback : function, optional
            A user-defined callback function that can be called at each iteration for custom processing.
        """

        # Initialize
        self.result.status = CST.UNSOLVED
        self.result.n_iter = 0
        time_start = time.perf_counter()
        _time_pre_log = time_start
        self.__logger.log_title()

        while self.result.n_iter <= self.params.iter_limit:
            self.result.n_iter += 1
            tm = time.perf_counter()
            self.master_problem.solve()
            self.result.runtime_master += time.perf_counter() - tm

            if self.master_problem.status == CST.OPTIMAL:
                # Master problem is optimal -> solve subproblem
                var_values = self.master_problem.get_var_values(self.complicating_vars)
                self.sub_problem.fix_vars(var_values)
                ts = time.perf_counter()
                self.sub_problem.solve()
                self.result.runtime_sub += time.perf_counter() - ts

                # Sub problem is infeasible -> add feasibility cut
                if self.sub_problem.status == CST.INFEASIBLE:
                    self.result.lb_list.append(self.result.lb)
                    self.result.ub_list.append(self.result.ub)
                    if self.__terminate(time_start):
                        break
                    self._add_feasibility_cut()

                # Sub problem is optimal -> add optimality cut
                elif self.sub_problem.status == CST.OPTIMAL:
                    self.__update_result(time_start)
                    _time_pre_log = self.__logger.log_line(time_start, _time_pre_log)
                    # REACH OPTIMALITY
                    if self.__terminate(time_start):
                        break
                    self._add_optimality_cut()

                # Sub problem is neither infeasible nor optimal -> error
                else:
                    self.result.status = CST.ERROR
                    raise ValueError(f"Subproblem returned an unexpected status: {self.sub_problem.status}.")

            # Master problem is infeasible -> original problem is infeasible
            elif self.master_problem.status == CST.INFEASIBLE:
                self.result.status = CST.INFEASIBLE
                break

            # Master problem is neither infeasible nor optimal -> error
            else:
                self.result.status = CST.ERROR
                raise ValueError(f"Master problem returned an unexpected status: {self.master_problem.status}.")

        # Finalize
        self.result.time = time.perf_counter() - time_start
        self.result.n_opt_cuts = len(self.master_problem.optimality_cuts)
        self.result.n_feas_cuts = len(self.master_problem.feasibility_cuts)
        self.result.n_cuts = self.result.n_opt_cuts + self.result.n_feas_cuts
        self.__logger.log_end()

    # def save_result(self):
    #     pass
    #
    # def save_checkpoint(self):
    #     pass
    #
    # def load_checkpoint(self):
    #     pass


if __name__ == '__main__':
    pass

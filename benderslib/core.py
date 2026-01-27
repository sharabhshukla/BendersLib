# coding:utf-8

import itertools
import time
from abc import ABC, abstractmethod
from typing import Union, Iterable, Callable, Iterator, Type
import inspect

from .consts import BendersConsts as CST
from .params import BendersParams
from .result import BendersResult
from .solvers import SolverBase
from .logger import BendersLogger


class ProblemBase:
    """The base class for :class:`MasterProblem` and :class:`SubProblem` in Benders decomposition.

    Parameters
    ---------------

    solver_backend : SolverBase
        An instance of a solver backend (e.g., :class:`~.solvers.Gurobi`) that implements the :class:`SolverBase` interface.
    complicating_vars : list, optional
        A list of names of the complicating variables.
    """

    def __init__(self, solver_backend: SolverBase):
        self.solver: SolverBase = solver_backend
        """An instance of the solver backend (see classes in :doc:`../api/solver`)."""
        self.model = self.solver.model
        """A copy of the original solver model instance.
        
        This attribute is exactly the solver-specific model instance passed during initialization.
        It allows direct access to solver-specific features (attributes and methods) not covered by the abstract interface.
        Refer to :ref:`solver-table` for supported solvers, and their documentation.
        """
        self.status = CST.UNSOLVED
        """The status of the problem (see :class:`BendersConsts` for possible values)."""

    def __repr__(self):
        n_vars = len(self.solver._all_vars)
        n = "Master Problem"
        if self.__class__.__name__ == "SubProblem":
            n_vars -= len(self.complicating_vars)
            n = "Sub Problem"

        return (
            f"{n}: \n"
            f" - {'Variable No.:'.ljust(CST.LOG_NAME_WIDTH)}{n_vars}"
            f" [Integer: {len(self.solver._int_vars)}, Binary: {len(self.solver._bin_vars)}]\n"
            f" - {'Constraint No.:'.ljust(CST.LOG_NAME_WIDTH)}{self.solver._constr_num}\n"
            f" - {'Solver:'.ljust(CST.LOG_NAME_WIDTH)}{self.solver.__class__.__name__}"
        )

    def __getattr__(self, name):
        # Make attributes of the solver backend accessible directly
        return getattr(self.solver, name)

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        """Add estimator variable(s) to the objective function of the model.

        Parameters
        ---------------

        estimators : list[str]
            A list of names for the estimator variables to be added.
        prob : list[float]
            A list of probabilities (weights) associated with each estimator variable.
            The length of ``prob`` should match that of ``estimators``.
            If ``None``, equal weights are assigned to all estimator variables.
            Note that the sum of probabilities does not need to equal 1.
        lb : float
            The lower bound for the estimator variables. Default is ``0.0``.

        Example
        ---------------

        .. code-block:: python

                # Adding multiple estimators with specified probabilities
                solver.add_estimators(
                    estimators=['theta1', 'theta2'],
                    prob=[0.3, 0.7],
                    lb=0.0
                )

                # Adding a single estimator
                solver.add_estimators(['theta'])
        """
        self.solver.add_estimators(estimators, prob, lb)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        """
        Fix the values of specified variables in the model.

        Parameters
        ---------------

        var_values : dict[str, float]
            A dictionary mapping variable names to their fixed values.

        Example
        ---------------

        .. code-block:: python

                problem.fix_vars({'x1': 10, 'x2': 5.5})
        """
        self.solver.fix_vars(var_values)

    def unfix_vars(self, vars: list[str]) -> None:
        """
        Unfix the specified variables in the model by restoring their original bounds.

        Parameters
        ---------------

        vars : list
            A list of variable names to be unfixed.

        Example
        ---------------

        .. code-block:: python

                problem.unfix_vars(['x1', 'x2'])
        """
        self.solver.unfix_vars(vars)

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        """
        Get the current values of specified variables in the model.

        Parameters
        ---------------

        vars : list[str] or None
            A list of variable names to retrieve values for. If ``None``, retrieves values for all variables

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
        return self.solver.get_var_values(vars)

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        """
        Get the coefficients of specified variables in all the constraints of the model.

        Parameters
        ---------------

        vars : list[str] or None
            A list of variable names to retrieve coefficients for. If ``None``, retrieves coefficients for all variables.

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
        return self.solver.get_var_coefs(vars)

    def get_rhs(self) -> list[float]:
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
        return self.solver.get_rhs()

    def get_dual_values(self) -> list[float]:
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
        return self.solver.get_dual_values()

    def get_extreme_ray(self) -> list[float]:
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
        return self.solver.get_extreme_ray()

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
        return self.solver.get_obj()

    def solve(self) -> None:
        """Solve the problem and update the :attr:`status` attribute."""
        self.solver.solve()
        self.status = self.solver.status

    def compute_iis(self) -> set[str]:
        """Compute the Irreducible Infeasible Subsystem (IIS) of the model if it is infeasible.

        This method can be useful for :doc:`../tutorials/cbd` to identify a set of conflicting
        (binary) variables that causing subproblem infeasibility.
        This set of variables can be smaller than the full set of complicating variables,
        thus potentially leading to stronger :class:`~benderslib.NoGoodFC`.

        .. caution::

            IIS is not guaranteed to be unique.

        Returns
        ---------------
        list[str]
            A list of variable names involved in the IIS.

        Example
        ---------------
        .. code-block:: python

                iis_vars = sub_problem.compute_iis()

        """
        return self.solver.compute_iis()


class MasterProblem(ProblemBase):
    """The master problem in Benders decomposition.

    Parameters
    ---------------

    solver_backend : SolverBase
        An instance of a solver backend (e.g., :class:`~.solvers.Gurobi`) that implements the :class:`SolverBase` interface.
    complicating_vars : list, optional
        A list of names of the complicating variables.
    params : BendersParams, optional
        The parameters that can be set by the user (see :class:`BendersParams`).
        If not provided, default parameters will be used.

    Example
    ---------------

    .. code-block:: python

            from benderslib import MasterProblem
            from benderslib.solvers import Gurobi

            model = ...  # Define your master problem model here
            solver_backend = Gurobi(model)
            master_problem = MasterProblem(solver_backend)
    """

    def __init__(
            self,
            solver_backend: SolverBase,
            complicating_vars: list = None,
            params: BendersParams = BendersParams()
    ):
        super().__init__(solver_backend)

        # Public attributes
        self.complicating_vars = complicating_vars
        """A list of names of the complicating variables."""
        self.optimality_cuts: set[Cut] = set()
        """A set of optimality cuts added to the master problem."""
        self.feasibility_cuts: set[Cut] = set()
        """A set of feasibility cuts added to the master problem."""
        self.cuts: dict[str, Cut] = dict()
        """A dictionary mapping cut names to their corresponding instances."""
        self.estimators: list[str] = []
        """A list of estimator variable names added to the master problem."""
        self.params: BendersParams = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""

        # Private attributes
        self.__oc_id = itertools.count(1)
        self.__fc_id = itertools.count(1)

    def _add_estimators(self, multiple: bool = False, prob: list[float] = None, lb: float = 0.0) -> None:
        """
        Add estimator variable(s) to the master problem.

        Parameters
        ---------------

        multiple : bool, optional
            If ``True``, add multiple estimator variables (only for stochastic Benders);
            if ``False``, add a single estimator variable. Default is ``False``.
        prob : list[float], optional
            A list of probabilities (or weights) for each estimator variable when ``multiple`` is ``True``.
            Default is ``None``.
        lb : float, optional
            The lower bound for the estimator variable(s). Default is ``0.0``.
        """

        # Number of estimator variables
        _num = len(prob) if multiple else 1

        # Define estimator variable names
        estimators = [CST.ESTIMATOR_FORMAT.format(i + 1) for i in range(_num)] if multiple else [CST.ESTIMATOR_NAME]

        self.add_estimators(estimators=estimators, prob=prob, lb=lb)
        self.estimators = estimators

    def get_estimator_values(self) -> dict[str, float]:
        """Get the current values of the estimator variables in the master problem.

        Returns
        ---------------

        dict[str, float]
            A dictionary mapping estimator variable names to their current values.
        """
        return self.get_var_values(self.estimators)

    def add_cut(self, cut) -> str | None:
        """Add a Benders cut to the master problem.

        Parameters
        ---------------

        cut : Cut
            An instance of :class:`Cut`, either an :class:`OptimalityCut` or :class:`FeasibilityCut`.

        Returns
        ---------------

        str
            The name of the added cut in the master problem.
        """

        if cut in self.optimality_cuts or cut in self.feasibility_cuts:
            # raise Exception(f"Duplicate cut detected: {cut}")

            BendersLogger.warning(f"Duplicate cut is ignored: {cut}")
            return None
        else:
            if cut.ctype == CST.OPTIMALITY:
                cut_id = f"OC{next(self.__oc_id)}"
                cut.name = f"{cut.name}_{cut_id}"
                self.optimality_cuts.add(cut)
            else:
                cut_id = f"FC{next(self.__fc_id)}"
                cut.name = f"{cut.name}_{cut_id}"
                self.feasibility_cuts.add(cut)

            self.cuts[cut.name] = cut
            self.solver.add_cut(cut, name=cut.name)
            return cut.name

    def remove_cut(self, cut_name: str) -> None:
        """Remove a cut from the master problem by its name.

        Parameters
        ---------------

        cut_name : str
            The name of the constraint to be removed.

        Example
        ---------------

        .. code-block:: python

                problem.remove_cut('BendersOC_1')
        """
        # Remove from MasterProblem
        # Set.discard will not raise KeyError if the cut does not exist, unlike Set.remove
        self.optimality_cuts.discard(self.cuts[cut_name])
        self.feasibility_cuts.discard(self.cuts[cut_name])
        # Dict.pop will raise KeyError if the cut does not exist
        self.cuts.pop(cut_name)

        # Remove from the solver model
        self.solver.remove_cut(cut_name)


class SubProblem(ProblemBase):
    """The sub problem in Benders decomposition.

    Parameters
    ---------------

    solver_backend : SolverBase
        An instance of a solver backend (e.g., :class:`~.solvers.Gurobi`) that implements the :class:`SolverBase` interface.
    complicating_vars : list, optional
        A list of names of the complicating variables.
    params : BendersParams, optional
        The parameters that can be set by the user (see :class:`BendersParams`).
        If not provided, default parameters will be used.

    Example
    ---------------

    .. code-block:: python

            from benderslib import SubProblem
            from benderslib.solvers import Gurobi

            model = ...  # Define your sub problem model here
            solver_backend = Gurobi(model)
            sub_problem = SubProblem(solver_backend)
    """

    def __init__(
            self,
            solver_backend: SolverBase,
            complicating_vars: list = None,
            params: BendersParams = BendersParams()
    ):
        super().__init__(solver_backend)

        # Public attributes
        self.complicating_vars = complicating_vars
        """A list of names of the complicating variables."""
        self.params = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""


class LogicBasedSubProblem(ABC):
    """The abstract base class for the subproblem in the Logic-based Benders Decomposition.

    To implement a customized subproblem, at least :meth:`solve` required to be overridden,
    as it will be called during the Benders solving process after :meth:`BendersSolver.solve` is invoked.
    Other methods and attributes can be added as needed, based on the specific implementation of :class:`CutGenerator`.

    Parameters
    ---------------

    complicating_vars : list[str]
        A list of names of the complicating variables.
    params : BendersParams, optional
        The parameters that can be set by the user (see :class:`BendersParams`).
        If not provided, default parameters will be used.
    """

    def __init__(self, complicating_vars: list[str], params: BendersParams = BendersParams()):
        self.complicating_vars: list[str] = complicating_vars
        """A list of names of the complicating variables.
        
        Example
        ---------------
        
        .. code-block:: python

            complicating_vars = ['x1', 'x2', 'x3']
        """
        self.complicating_var_values: dict[str, float | int] = {}
        """The values of complicating variables provided by the master problem.
        
        After calling :meth:`BendersSolver.solve`, this attribute will be updated via :meth:`fix_vars`
        after the master problem is solved. Therefore, users do not need to set it manually, 
        and can directly use it when implementing :meth:`solve`.
           
        Example
        ---------------
        
        .. code-block:: python
        
            complicating_var_values = {'x1': 10, 'x2': 5.5, 'x3': 0}
        """
        self.obj: float | int | None = None
        """The objective value of the subproblem after solving."""
        self.var_values: dict[str, float | int] = {}
        """The values of variables in the subproblem after solving."""
        self.status = CST.UNSOLVED
        """The status of the problem (see :class:`BendersConsts` for possible values)."""
        self.params: BendersParams = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""

    @abstractmethod
    def solve(self) -> None:
        """Solve the subproblem and update the :attr:`status`, :attr:`obj`, and :attr:`var_values` attributes.

        This method is **required** to be implemented.

        *   :attr:`status` is used in :meth:`SubProblems.solve` to indicate if the subproblem is
            optimal (:attr:`BendersConsts.OPTIMAL`) or infeasible (:attr:`BendersConsts.INFEASIBLE`),
            guiding whether to add optimality or feasibility cuts.
        *   :attr:`obj` is used in :meth:`BendersSolver.solve` to compute the upper bound,
            determining convergence.
        *   :attr:`var_values` is used in :meth:`BendersSolver.solve` when saving the final solution.

        .. caution::
            * It is safe to assume that :attr:`complicating_var_values` has been set.
            * Always update :attr:`status`, :attr:`obj`, and :attr:`var_values` after solving the subproblem.
              Returning values from this method will be ignored.

        Example
        ---------------

        .. code-block:: python

            from benderslib import LogicBasedSubProblem, CST

            class MyCustomSubproblem(LogicBasedSubProblem):
                def solve(self):
                    # Access master variables' values
                    x_val = self.complicating_var_values['x']

                    # Implement your custom solving logic here
                    # and set the status, obj, and var_values attributes
                    if x_val > 5:
                        self.status = CST.INFEASIBLE
                        self.obj = None
                        self.var_values = {}
                    else:
                        self.status = CST.OPTIMAL
                        self.obj = 10 - x_val
                        self.var_values = {'y': 2 * x_val}

            custom_subproblem = MyCustomSubproblem(complicating_vars=['x'])

        .. note::
           Alternatively, BendersLib allows using a lightweight function
           (instead of the class :class:`LogicBasedSubProblem`) as the subproblem solver.
           The signature of the function should be as follows.

           .. code-block:: python

                from benderslib import CST

                def subproblem_solver(master_vars: dict[str, float]) -> tuple[str, float, dict[str, float]]:
                    # Access master variables' values
                    x_val = master_vars['x']

                    # Implement your custom solving logic here
                    if x_val > 5:
                        status = CST.INFEASIBLE
                        obj = None
                        var_values = {}
                    else:
                        status = CST.OPTIMAL
                        obj = 10 - x_val
                        var_values = {'y': 2 * x_val}

                    # Return status, objective value, and variable values (as a dict)
                    return status, obj, var_values

           To maintain state, implement a class inherited from :class:`LogicBasedSubProblem` instead.

        .. seealso::

            Please refer to :ref:`Custom subproblem & Multiple custom subproblems <manual_custom_sub>` for the manual.
        """
        ...

    def fix_vars(self, var_values: dict[str, float]) -> None:
        """Fix the values of specified variables in the model (do **not** override it).

        This method simply update :attr:`complicating_var_values`.
        It ise used by :meth:`BendersSolver.solve`.
        """
        self.complicating_var_values = var_values

    def get_var_values(self, vars: list[str] = None) -> dict[str, float]:
        """Get the current values of specified variables in the model (do **not** override it).

        It is used for saving the final solution.
        This method simply return :attr:`var_values`, which should be updated in :meth:`solve`.
        It ise used by :meth:`BendersSolver.solve`.
        """
        if vars is None:
            return self.var_values
        else:
            return {var: self.var_values[var] for var in vars}

    def get_obj(self) -> float:
        """Get the objective value of the model after solving (do **not** override it).

        This method simply return :attr:`obj`, which should be updated in :meth:`solve`.
        It ise used by :meth:`BendersSolver.solve`.
        """
        return self.obj

    def __repr__(self):
        return (
            f"Logic-Based Sub Problem: \n"
            f" - `{self.__class__.__name__}`"
        )


class _FuncWrapperSub(LogicBasedSubProblem):
    """A wrapper class to allow using a function as a logic-based subproblem."""

    def __init__(self, complicating_vars, func: Callable, params: BendersParams = BendersParams()):
        self._func = func
        super().__init__(complicating_vars, params)

    def solve(self):
        status, obj, var_values = self._func(self.complicating_var_values)
        self.status = status
        self.obj = obj
        self.var_values = var_values

    def __repr__(self):
        return (
            f"Logic-Based Sub Problem: \n"
            f" - `{self._func.__name__}`"
        )


class SubProblems:
    """A collection of multiple subproblems in Benders decomposition for stochastic programming.

    Parameters
    ---------------

    sub_problems : list[SubProblem | LogicBasedSubProblem]
        A list of :class:`SubProblem` or :class:`LogicBasedSubProblem` instances.
    prob : list[float], optional
        A list of probabilities (weights) associated with each subproblem.
        The length of ``prob`` should match that of ``sub_problems``.
        If ``None``, equal weights are assigned to all subproblems.
    params : BendersParams, optional
        The parameters that can be set by the user (see :class:`BendersParams`).
        If not provided, default parameters will be used.

    Example
    ---------------

    .. code-block:: python

            from benderslib import SubProblems, SubProblem
            from benderslib.solvers import Gurobi

            model1 = ...  # Define the first subproblem model
            model2 = ...  # Define the second subproblem model
            solver_backend1 = Gurobi(model1)
            solver_backend2 = Gurobi(model2)

            sub1 = SubProblem(Gurobi(model1))
            sub2 = SubProblem(Gurobi(model2))
            sub_problems = SubProblems([sub1, sub2], prob=[0.4, 0.6])
    """

    def __init__(
            self,
            sub_problems: Iterable,
            prob: list[float] | None = None,
            params: BendersParams = BendersParams()
    ):
        self.sub_problems = list(sub_problems)
        """A list of :class:`SubProblem` or :class:`LogicBasedSubProblem` instances."""
        self.prob = prob or [1.0 / len(self.sub_problems)] * len(self.sub_problems)
        """A list of probabilities or weights associated with each subproblem. 
        
        If ``None``, equal weights are assumed.
        """
        self.params: BendersParams = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""
        self.status = CST.UNSOLVED
        """The status of the problem (see :class:`BendersConsts` for possible values)."""

    def __repr__(self):
        return (
            f"Sub Problems: \n"
            f" - {'Scenario No.:'.ljust(CST.LOG_NAME_WIDTH)}{len(self.prob)}"
            # + self.sub_problems[0].__repr__().replace("Sub Problem: ", "")
        )

    def __iter__(self) -> Iterator['SubProblem']:
        return iter(self.sub_problems)

    def __len__(self) -> int:
        return len(self.sub_problems)

    def get_obj(self) -> float:
        """Get the :attr:`prob` weighted objective value of all subproblems.

        It ise used by :meth:`BendersSolver.solve`.

        Returns
        ---------------

        float
            The weighted objective value.

        Example
        ---------------

        .. code-block:: python

                obj_val = sub_problems.get_obj()
        """
        objs = [sub.get_obj() for sub in self.sub_problems]
        return sum(obj * p for obj, p in zip(objs, self.prob))

    def fix_vars(self, var_values: dict[str, float]) -> None:
        """Fix the values of specified variables in all subproblems.

        It ise used by :meth:`BendersSolver.solve`.

        Parameters
        ---------------

        var_values : dict[str, float]
            A dictionary mapping variable names to their fixed values.

        Example
        ---------------

        .. code-block:: python

                sub_problems.fix_vars({'x1': 10, 'x2': 5.5})
        """
        for sub in self.sub_problems:
            sub.fix_vars(var_values)

    def get_var_values(self, vars: list[str] = None) -> dict[int, dict[str, float]]:
        """Get the current values of specified variables in all subproblems.

        It ise used by :meth:`BendersSolver.solve`.

        Parameters
        ---------------

        vars : list[str], optional
            A list of variable names to retrieve values for. If ``None``, retrieves values for all variables.

        Returns
        ---------------

        dict[int, dict[str, float]]
            A dictionary mapping subproblem indices to dictionaries of variable names and their current values.

        Example
        ---------------

        .. code-block:: python

                values = sub_problems.get_var_values(['x1', 'x2'])
                # or get all variable values
                all_values = sub_problems.get_var_values()
        """

        var_values = {}
        for i, sub in enumerate(self.sub_problems):
            var_values[i] = sub.get_var_values(vars)
        return var_values

    def solve(self) -> None:
        """Solve all subproblems and update the :attr:`status` attribute.

        If any subproblem is infeasible and :attr:`BendersParams.multi_feas_cut` is ``False``,
        the solving process will stop early.

        It ise used by :meth:`BendersSolver.solve`.
        """
        for sub in self.sub_problems:
            sub.solve()
            if sub.status == CST.INFEASIBLE and not self.params.multi_feas_cut:
                break

        if all(sub.status == CST.OPTIMAL for sub in self.sub_problems):
            self.status = CST.OPTIMAL
        elif any(sub.status == CST.INFEASIBLE for sub in self.sub_problems):
            self.status = CST.INFEASIBLE
        else:
            self.status = CST.UNKNOWN
            raise RuntimeError("SubProblems status could not be determined.")


class Cut:
    """The base class for Benders cuts in Benders decomposition.

    Parameters
    ---------------

    vars : list[str]
        The list of variable names involved in the cut.
    coefs : list[float | int]
        The list of coefficients corresponding to the variables in the cut.
    rhs : float | int
        The right-hand side value of the cut.
    sense : str
        The sense of the cut (:attr:`BendersConsts.LE`, :attr:`BendersConsts.GE`, or :attr:`BendersConsts.EQ`).
    ctype : str
        It should be :attr:`BendersConsts.OPTIMALITY` or :attr:`BendersConsts.FEASIBILITY`.
    name : str
        The name for the cut.

    Example
    ---------------

    .. code-block:: python

            from benderslib import Cut, CST

            cut = Cut(
                vars=['x1', 'x2'],
                coefs=[1.0, -2.0],
                rhs=5.0,
                sense=CST.LE,
                ctype=CST.OPTIMALITY,
                name='MyCut'
            )
    """

    def __init__(
            self,
            vars: list[str],
            coefs: list[float | int],
            rhs: float | int,
            sense: str,
            ctype: Union[CST.OPTIMAL, CST.FEASIBILITY],
            name: str,
    ):
        assert sense in {CST.LE, CST.GE, CST.EQ}, f"sense {sense} must be one of: {{CST.LE, CST.GE, CST.EQ}}"

        # Public attributes
        self.vars: list[str] = vars
        """The list of variable names involved in the cut."""
        self.coefs: list[float | int] = coefs
        """The list of coefficients corresponding to the variables in the cut."""
        self.rhs: float | int = rhs
        """The right-hand side value of the cut."""
        self.sense: str = sense
        """The sense of the cut.

        It must be :attr:`BendersConsts.LE`, :attr:`BendersConsts.GE`, or :attr:`BendersConsts.EQ`.
        """
        self.ctype: Union[CST.OPTIMAL, CST.FEASIBILITY] = ctype
        """The indicator of the cut type.

        It should be either :attr:`BendersConsts.OPTIMALITY` or :attr:`BendersConsts.FEASIBILITY`.
        """
        self.name: str = name
        """The name for the cut."""

        # Private attributes
        self._params: BendersParams | None = None
        """The parameters that can be set by the user (see :class:`BendersParams`)."""

    def __repr__(self):
        return (f"{self.name} ({self.ctype}): "
                f"{' + '.join(f'{a} * {b}' for a, b in zip(self.coefs, self.vars))} "
                f"{self.sense} {self.rhs}")

    def __eq__(self, other):
        # Sort by variable name to ensure order doesn't matter
        self_sorted_pairs = sorted(zip(self.vars, self.coefs))
        other_sorted_pairs = sorted(zip(other.vars, other.coefs))

        if len(self_sorted_pairs) != len(other_sorted_pairs):
            return False

        if self.sense != other.sense:
            return False

        # Handle comparison out of Benders iterations
        tol = self._params.tol_cut_diff if self._params else BendersParams.tol_cut_diff

        if abs(self.rhs - other.rhs) > tol:
            return False

        for (v1, c1), (v2, c2) in zip(self_sorted_pairs, other_sorted_pairs):
            if v1 != v2 or abs(c1 - c2) > tol:
                return False

        return True

    def __hash__(self):
        # Sort by variable name to ensure hash is consistent
        sorted_pairs = sorted(zip(self.vars, self.coefs))

        # Handle comparison out of Benders iterations
        tol = self._params.tol_cut_diff if self._params else BendersParams.tol_cut_diff

        # Discretize floating-point values for hashing
        discretized_rhs = round(self.rhs / tol)
        discretized_coefs = tuple(round(c / tol) for _, c in sorted_pairs)

        # Extract var names
        var_names = tuple(v for v, _ in sorted_pairs)

        h = hash((var_names, discretized_coefs, discretized_rhs, self.sense))
        return h


class OptimalityCut(Cut):
    """The class of optimality cuts in Benders decomposition.

    Parameters
    ---------------

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

    Example
    ---------------

    .. code-block:: python

            from benderslib import OptimalityCut, CST

            oc = OptimalityCut(
                vars=['x1', 'x2'],
                coefs=[1.0, -2.0],
                rhs=5.0,
                sense=CST.LE,
                name='MyOptimalityCut'
            )
    """

    def __init__(self, vars, coefs, rhs, sense, name="OC"):
        super().__init__(vars, coefs, rhs, sense, CST.OPTIMALITY, name)


class FeasibilityCut(Cut):
    """The class of feasibility cuts in Benders decomposition.

    Parameters
    ---------------

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

    Example
    ---------------

    .. code-block:: python

            from benderslib import FeasibilityCut, CST

            fc = FeasibilityCut(
                vars=['x1', 'x2'],
                coefs=[1.0, -2.0],
                rhs=5.0,
                sense=CST.LE,
                name='MyFeasibilityCut'
            )
    """

    def __init__(self, vars, coefs, rhs, sense, name="FC"):
        super().__init__(vars, coefs, rhs, sense, CST.FEASIBILITY, name)


class CutGenerator(ABC):
    """The base class for cut generators in Benders decomposition.

    Any specific cut generation method (e.g., :class:`ClassicalOCGen`) should inherit from this class
    and implement the abstract method :meth:`generate`.
    Attributes that will not change during the Benders process should be ideally initialized in ``__init__``
    for efficiency.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : SubProblem | SubProblems
        An instance of :class:`SubProblem` representing the subproblem,
        or :class:`SubProblems` for multiple subproblems.
    params : BendersParams, optional
        The parameters that can be set by the user (see :class:`BendersParams`).
        If not provided, default parameters will be used.
    """

    def __init__(
            self,
            master_problem: MasterProblem,
            sub_problem: SubProblem | SubProblems,
            params: BendersParams = BendersParams()
    ):
        self._master_problem = master_problem
        """The master problem instance."""
        self._sub_problem = sub_problem
        """The subproblem instance."""
        self._complicating_vars = master_problem.complicating_vars
        """A list of names of the complicating variables."""
        self.params = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""

        assert set(self._complicating_vars) == set(sub_problem.complicating_vars), \
            "Complicating variables in master and subproblem must match."

    @abstractmethod
    def generate(self) -> list['OptimalityCut'] | list['FeasibilityCut']:
        """Generate a list of Benders cuts based on the current state of the master and subproblem(s) (**required** to be implemented).

        This method generates and returns a list of cuts (either :class:`OptimalityCut` or :class:`FeasibilityCut`)
        with the information from :attr:`_master_problem` and :attr:`_sub_problem`, which are updated during
        the Benders solving process.

        Example implementations can be found in the source code of :class:`ClassicalOCGen` and :class:`ClassicalFCGen`.

        .. note::
           Alternatively, BendersLib allows using a lightweight function
           (instead of the class :class:`CutGenerator`) as the cut generator.
           The signature of the function should be as follows.

           .. code-block:: python

                from benderslib import Cut, OptimalityCut, FeasibilityCut

                def cut_generator(master_problem: MasterProblem, sub_problem: SubProblem) -> list[Cut]:
                    cuts = []
                    cut = Cut(...) # implement the cut generation logic here
                    cuts.append(cut)
                    return cuts  # a list of OptimalityCut or FeasibilityCut

           To maintain state, implement a class inherited from :class:`CutGenerator` instead.
        """
        ...

    def _generate(self):
        """Inject parameters to cuts generated by :meth:`generate`."""
        cuts = self.generate()
        for cut in cuts:
            cut._params = self.params
        return cuts


class _FuncWrapperCut(CutGenerator):
    """A wrapper class to allow using a function as a cut generator."""

    def __init__(self, master_problem, sub_problem, func: Callable, params: BendersParams = BendersParams()):
        self._func = func
        super().__init__(master_problem, sub_problem, params)

    def generate(self):
        return self._func(self._master_problem, self._sub_problem)


class BendersSolver:
    """The core class for Benders decomposition methods.

    Any specific Benders decomposition method (e.g., :class:`ClassicalBenders`) is inherited from this class.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : SubProblem | SubProblems
        An instance of :class:`SubProblem` representing the subproblem,
        or :class:`SubProblems` for multiple subproblems.
    complicating_vars : list[str]
        A list of names of the complicating variables.
    optimality_cut : Type[CutGenerator], optional
        An abstract class that inherits from :class:`CutGenerator` to be used for generating optimality
        cuts.
        It also accepts a function with signature ``func(master_problem, sub_problem) -> list[OptimalityCut]``.
        If ``None``, no optimality cuts will be added.
    feasibility_cut : Type[CutGenerator], optional
        An abstract class that inherits from :class:`CutGenerator` to be used for generating feasibility
        cuts.
        It also accepts a function with signature ``func(master_problem, sub_problem) -> list[FeasibilityCut]``.
        If ``None``, no feasibility cuts will be added.
    params : BendersParams, optional
        The parameters that can be set by the user (see :class:`BendersParams`).
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
        # Override complicating vars in master and subproblem
        master_problem.complicating_vars = complicating_vars
        sub_problem.complicating_vars = complicating_vars

        # Override params in master and subproblem
        master_problem.params = params
        sub_problem.params = params

        # Public attributes
        self.master_problem = master_problem
        """An instance of :class:`MasterProblem` representing the master problem."""
        self.sub_problem = sub_problem
        """An instance of :class:`SubProblem` or :class:`SubProblems` representing the subproblem(s)."""
        self.complicating_vars = complicating_vars
        """A list of names of the complicating variables."""
        self.optimality_cut = self.__initialize_cut(optimality_cut, master_problem, sub_problem, params)
        """An instance of :class:`CutGenerator` for generating optimality cuts."""
        self.feasibility_cut = self.__initialize_cut(feasibility_cut, master_problem, sub_problem, params)
        """An instance of :class:`CutGenerator` for generating feasibility cuts."""
        self.params = params
        """The parameters that can be set by the user (see :class:`BendersParams`)."""
        self.result = BendersResult()
        """An instance of :class:`BendersResult` that stores the results and statistics."""

        # Private attributes
        self.__logger = BendersLogger(self)
        """An instance of :class:`BendersLogger` for handling logging."""
        self.__prob = self.sub_problem.prob if isinstance(self.sub_problem, SubProblems) else None

        # Ensure at least one cut generator is provided
        assert self.optimality_cut or self.feasibility_cut, "Provide at least <optimality_cut> or <feasibility_cut>."

    def __initialize_cut(self, cut, master_problem, sub_problem, params):
        if inspect.isfunction(cut):
            return _FuncWrapperCut(master_problem, sub_problem, cut, params)
        elif inspect.isclass(cut):
            return cut(master_problem, sub_problem, params)
        elif cut is not None:
            raise ValueError("<cut> must be a <function> or a <class>.")
        return None

    @classmethod
    def from_models(
            cls,
            master_model,
            master_solver: Type[SolverBase],
            sub_model,
            sub_solver: Type[SolverBase],
            complicating_vars: list[str],
            optimality_cut: Type[CutGenerator] | Callable = None,
            feasibility_cut: Type[CutGenerator] | Callable = None,
            prob: list[float] | None = None,
            params: BendersParams = BendersParams()
    ):
        """Class method to create a :class:`BendersSolver` instance directly from solver models.

        Parameters
        ---------------

        master_model :
            Solver model instance for the master problem (e.g., ``gurobipy.Model``).
        master_solver : Type[SolverBase]
            An abstract class that inherits from :class:`SolverBase` to be used as the solver backend for the master problem.
        sub_model :
            Solver model instance for the subproblem (e.g., ``gurobipy.Model``).
        sub_solver : Type[SolverBase]
            An abstract class that inherits from :class:`SolverBase` to be used as the solver backend for the subproblem.
        complicating_vars : list[str]
            A list of names of the complicating variables.
        optimality_cut : Type[CutGenerator], optional
            An abstract class that inherits from :class:`CutGenerator` to be used for generating optimality
            cuts.
            It also accepts a function with signature ``func(master_problem, sub_problem) -> list[OptimalityCut]``.
            If ``None``, no optimality cuts will be added.
        feasibility_cut : Type[CutGenerator], optional
            An abstract class that inherits from :class:`CutGenerator` to be used for generating feasibility
            cuts.
            It also accepts a function with signature ``func(master_problem, sub_problem) -> list[FeasibilityCut]``.
            If ``None``, no feasibility cuts will be added.
        prob : list[float], optional
            A list of probabilities (or weights) for each subproblem when using multiple subproblems (L-shaped method).
        params : BendersParams, optional
            The parameters that can be set by the user (see :class:`BendersParams`).
            If not provided, default parameters will be used.

        Example
        ---------------

        .. code-block:: python

            from benderslib import BendersSolver
            from benderslib.solvers import Gurobi
            from gurobipy import Model

            # Create master and subproblem models using Gurobi
            master_model = Model()
            # ... (define master problem variables, constraints, and objective)
            sub_model = Model()
            # ... (define subproblem variables, constraints, and objective)
            complicating_vars = ['x1', 'x2']

            # Create BendersSolver instance from models
            benders_solver = BendersSolver.from_models(
                master_model = master_model,
                master_solver = Gurobi,
                sub_model = sub_model,
                sub_solver = Gurobi,
                complicating_vars = complicating_vars
            )
        """

        master_problem = MasterProblem(master_solver(master_model))

        if isinstance(sub_model, Iterable):
            # if len(sub_model) > 1:
            sub_problem = (SubProblem(sub_solver(sub)) for sub in sub_model)
            sub_problem = SubProblems(sub_problem, prob=prob)
        else:
            sub_problem = SubProblem(sub_solver(sub_model))

        return cls(
            master_problem,
            sub_problem,
            complicating_vars,
            optimality_cut,
            feasibility_cut,
            params
        )

    def __str__(self):
        integer_num = len(set(self.complicating_vars) & set(self.master_problem.solver._int_vars))
        binary_num = len(set(self.complicating_vars) & set(self.master_problem.solver._bin_vars))

        return (
            f"Benders Decomposition:\n"
            f" - {'Method:'.ljust(CST.LOG_NAME_WIDTH)}{self.__class__.__name__}\n"
            f" - {'Complicating Var. No.:'.ljust(CST.LOG_NAME_WIDTH)}{len(self.complicating_vars)}"
            f" [Integer: {integer_num}, Binary: {binary_num}]\n"
            f" - {'Optimality Cut:'.ljust(CST.LOG_NAME_WIDTH)}{self.optimality_cut.__class__.__name__ or None}\n"
            f" - {'Feasibility Cut:'.ljust(CST.LOG_NAME_WIDTH)}{self.feasibility_cut.__class__.__name__ or None}"
        )

    def __add_optimality_cut(self):
        """
        The method to add one or multiple :class:`OptimalityCut` to :class:`MasterProblem`.
        """
        cuts = self.optimality_cut._generate()
        for cut in cuts:
            self.master_problem.add_cut(cut)

    def __add_feasibility_cut(self):
        """
        The method to add one or multiple :class:`FeasibilityCut` to :class:`MasterProblem`.
        """
        cuts = self.feasibility_cut._generate()
        for cut in cuts:
            self.master_problem.add_cut(cut)

    def __update_result(self, time_start):
        self.result.n_sol += 1
        self.result.status = CST.FEASIBLE

        self.result.lb = self.master_problem.get_obj()
        estimator_vals = self.master_problem.get_estimator_values()

        if isinstance(self.sub_problem, SubProblem) or not self.params.multi_opti_cut:
            # Deterministic problem, or stochastic problem with a single estimator
            estimator = self.master_problem.estimators[0]
            theta = estimator_vals[estimator]
        else:
            # Stochastic problem with multiple estimators
            theta = sum(
                estimator_vals[self.master_problem.estimators[i]] * p
                for i, p in enumerate(self.__prob)
            )

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

    def __preprocess(self):
        # Add estimators to the master problem
        if isinstance(self.sub_problem, SubProblem) or not self.params.multi_opti_cut:
            # Deterministic problem, or stochastic problem with a single estimator
            self.master_problem._add_estimators(lb=self.params.theta_lb)
        else:
            # Stochastic problem with multiple estimators
            self.master_problem._add_estimators(multiple=True, prob=self.__prob, lb=self.params.theta_lb)

        # Other preprocessing steps can be added here
        ...

    def solve(self, callback=None) -> None:
        """Solve the problem using Benders decomposition.

        This method implements the main Benders decomposition algorithm, iteratively solving the master and
        subproblems, adding cuts, and updating the results until convergence or stopping criteria are met.

        After calling this method, the results and statistics of the Benders decomposition process can be accessed
        through the :attr:`BendersSolver.result` attribute, which is an instance of :class:`BendersResult`.

        Parameters
        ---------------

        callback : function, optional
            A user-defined callback function that can be called at each iteration for custom processing.
        """

        # Initialize
        self.__preprocess()

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
                    self.__add_feasibility_cut()

                # Sub problem is optimal -> add optimality cut
                elif self.sub_problem.status == CST.OPTIMAL:
                    self.__update_result(time_start)
                    _time_pre_log = self.__logger.log_line(time_start, _time_pre_log)
                    # REACH OPTIMALITY
                    if self.__terminate(time_start):
                        break
                    self.__add_optimality_cut()

                # Sub problem is neither infeasible nor optimal -> error
                else:
                    self.result.status = CST.UNKNOWN
                    raise ValueError(f"Subproblem returned an unexpected status: {self.sub_problem.status}.")

            # Master problem is infeasible -> original problem is infeasible
            elif self.master_problem.status == CST.INFEASIBLE:
                self.result.status = CST.INFEASIBLE
                break

            # Master problem is neither infeasible nor optimal -> error
            else:
                self.result.status = CST.UNKNOWN
                raise ValueError(f"Master problem returned an unexpected status: {self.master_problem.status}.")

        # Finalize
        self.result.time = time.perf_counter() - time_start
        self.result.n_opt_cuts = len(self.master_problem.optimality_cuts)
        self.result.n_feas_cuts = len(self.master_problem.feasibility_cuts)
        self.result.n_cuts = self.result.n_opt_cuts + self.result.n_feas_cuts
        self.__logger.log_end()


if __name__ == '__main__':
    pass

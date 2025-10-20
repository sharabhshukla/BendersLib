# coding:utf-8

from abc import ABC, abstractmethod

from ..consts import BendersConsts as CST


class SolverBase(ABC):
    """
    This is an abstract base class for solver interfaces in BendersLib.
    It defines the essential methods and attributes that any solver interface must implement
    to be compatible with BendersLib.

    Parameters
    ---------------
    model :
        An instance of the solver's model class (e.g., Gurobi's ```gurobipy.Model```).
    """

    def __init__(self, model) -> None:
        self.model = model
        self.status = CST.UNSOLVED
        """
        The status of the last solve attempt, initialized to :const:`BendersConsts.UNSOLVED`.
        It should be updated to :const:`BendersConsts.OPTIMAL` or :const:`BendersConsts.INFEASIBLE`, 
        after calling the :func:`SolverBase.solve` method.

        .. caution::
            ``status`` should only be set to :const:`BendersConsts.OPTIMAL` or :const:`BendersConsts.INFEASIBLE`,
            since it is not clear how other statuses (e.g., feasible but not optimal)
            would impact convergence of Benders decomposition.
        """
        self._solver_model = model
        """A copy of the original solver model instance (:data:`model`), 
        used to access the original model data and methods."""

        # Attributes to be set in the subclass
        self._sense = CST.MIN
        """It specifies if the model is a minimization problem
         (:const:`BendersConsts.MIN`) or a maximization problem (:const:`BendersConsts.MAX`).
        """
        self._all_vars: list[str] = []
        """A list of all variable names in the model."""
        self._int_vars: list[str] = []
        """A list of all integer variable names in the model."""
        self._bin_vars: list[str] = []
        """A list of all binary variable names in the model."""
        self._var_bounds: dict[str, tuple[float, float]] = {}
        """A dictionary mapping variable names to their (lower_bound, upper_bound) tuples."""
        self._rhs: list[float] = []
        """A list of right-hand side values for all constraints in the model."""

    @abstractmethod
    def fix_vars(self, var_values: dict) -> None:
        """
        Fix the values of specified variables in the model.

        Parameters
        ---------------
        var_values : dict
            A dictionary mapping variable names to their fixed values.

        Example
        ---------------

        .. code-block:: python

                solver.fix_vars({'x1': 10, 'x2': 5.5})
        """
        ...

    @abstractmethod
    def unfix_vars(self, vars: list) -> None:
        """
        Unfix the specified variables in the model, restoring their original bounds.

        Parameters
        ---------------
        vars : list
            A list of variable names to be unfixed.

        Example
        ---------------

        .. code-block:: python

                solver.unfix_vars(['x1', 'x2'])
        """
        ...

    @abstractmethod
    def get_var_values(self, vars=None) -> dict:
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

                values = solver.get_var_values(['x1', 'x2'])
                # or get all variable values
                all_values = solver.get_var_values()

        """
        ...

    @abstractmethod
    def get_var_coefs(self, vars=None) -> dict[str, list]:
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

                coefs = solver.get_var_coefs(['x1', 'x2'])
                # or get coefficients for all variables
                all_coefs = solver.get_var_coefs()
        """
        ...

    @abstractmethod
    def get_rhs(self) -> list:
        """
        Get the right-hand side values of all constraints in the model.

        Returns
        ---------------
        list[float]
            A list of right-hand side values for each constraint.

        Example
        ---------------
        .. code-block:: python

                rhs = solver.get_rhs()
        """
        ...

    @abstractmethod
    def get_dual_values(self) -> list:
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

                pi = solver.get_dual_values()
        """
        ...

    @abstractmethod
    def get_extreme_ray(self) -> list:
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

                ray = solver.get_extreme_ray()
        """
        ...

    @abstractmethod
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

                obj_val = solver.get_obj()
        """
        ...

    @abstractmethod
    def add_cut(self, cut, name) -> None:
        """
        Add a BendersLib :class:`Cut` instance to the solver's model as a constraint.

        Parameters
        ---------------
        cut : :class:`Cut`
            An instance of a :class:`Cut`, either :class:`OptimalityCut` or :class:`FeasibilityCut`.
        name : str
            The name of the constraint to be added.

        Example
        ---------------
        .. code-block:: python

                from benderslib import OptimalityCut

                cut = OptimalityCut(vars=['x1', 'x2'], coefs=[1.0, 2.0], rhs=10.0, sense=CST.GEQ)
                solver.add_cut(cut, name='BendersOC_1')
        """
        ...

    @abstractmethod
    def remove_cut(self, cut_name) -> None:
        """
        Remove a constraint from the solver's model by its name.

        Parameters
        ---------------
        cut_name : str
            The name of the constraint to be removed.

        Example
        ---------------
        .. code-block:: python

                solver.remove_cut('BendersOC_1')
        """
        ...

    @abstractmethod
    def solve(self) -> None:
        """
        Solve the optimization model using the solver's built-in optimization method.
        Solver-specific parameters can be set in this method,
        such as hiding the solver's output log in the console.
        After solving, ``status`` should be updated accordingly
        to :const:`BendersConsts.OPTIMAL` or :const:`BendersConsts.INFEASIBLE`.

        .. caution::
            ``status`` should only be set to :const:`BendersConsts.OPTIMAL` or :const:`BendersConsts.INFEASIBLE`,
            since it is not clear how other statuses (e.g., feasible but not optimal)
            would impact convergence of Benders decomposition.
        """
        ...

    def make_master_problem(self, complicating_vars: list[str]) -> object:
        """
        Create a master problem by extracting the complicating variables from the original model.

        Parameters
        ---------------
        complicating_vars : list[str]
            A list of variable names that are considered complicating variables.

        Returns
        ---------------
        object
            A new model instance representing the master problem, in the solver-specific format.

        Example
        ---------------
        .. code-block:: python

                master_model = solver.make_master_problem(['x1', 'x2'])
        """
        ...

    def make_sub_problem(self, complicating_vars: list[str]) -> object:
        """
        Create a subproblem by fixing the complicating variables in the original model.

        Parameters
        ---------------
        complicating_vars : list[str]
            A list of variable names that are considered complicating variables.

        Returns
        ---------------
        object
            A new model instance representing the subproblem, in the solver-specific format.

        Example
        ---------------
        .. code-block:: python

                sub_model = solver.make_sub_problem(['x1', 'x2'])
        """
        ...


if __name__ == '__main__':
    pass

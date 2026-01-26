# coding:utf-8

import copy

from ortools.sat.python import cp_model

from ..consts import BendersConsts as CST
from ._base import SolverCPBase


class Ortools(SolverCPBase):
    """OR-Tools solver interface for BendersLib.

    This class provides an interface to the OR-Tools CP-SAT solver for use with BendersLib.
    Refer to :ref:`solver-table` for the supported features of this solver interface
    and the link to the backend solver's official documentation.

    .. warning::

        Constraint Programming (CP) solvers does not technically support dual or extreme rays like
        Mathematical Programming (MP) solvers. Therefore, dual-based Benders methods like
        :class:`~benderslib.ClassicalBenders` are not compatible with :class:`Ortools`.
        :class:`Ortools` is typically used with :class:`~benderslib.CombinatorialBenders` and
        :class:`~benderslib.LogicBasedBenders` for solving subproblems modeled as CP problems.

    Parameters
    ---------------
    model: ortools.sat.python.cp_model.CpModel
        An instance of OR-Tools' ``cp_model.CpModel``.
    vars_map: dict[str, object]
        A dictionary mapping **all** (not only complicating) variable names to OR-Tools variable objects.
        This is necessary because OR-Tools does not provide a direct way to access variables by name.
    solver_options: dict, optional
        A dictionary of solver-specific options.
    """

    def __init__(self, model: cp_model.CpModel, vars_map: dict, solver_options: dict = None) -> None:
        super().__init__(model)

        # Attributes required by SolverBase
        self.model = model
        self.status = CST.UNSOLVED

        # Private attributes
        self._solver = cp_model.CpSolver()
        self._original_model = model
        self._original_vars_map = vars_map
        self._vars_map = vars_map

        self._sense = CST.MIN
        self._all_vars = [v.name for v in self.model.Proto().variables]
        self._int_vars = []
        self._bin_vars = []
        # self._var_bounds = {}
        # self._rhs = []
        self._constr_num = len(self.model.Proto().constraints)

        self.__standardize()
        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()

    def __sense_to_minimize(self):
        if self.model.Proto().objective.scaling_factor == -1.0:
            raise NotImplementedError("BendersLib currently only supports minimization problems.")

    def __setup_model(self, solver_options: dict = None):
        if solver_options:
            for key, value in solver_options.items():
                setattr(self._solver.parameters, key, value)

    def __copy_model(self):
        # See https://github.com/google/or-tools/blob/stable/ortools/sat/docs/model.md#model-copy
        # for how to copy models in OR-Tools
        to_clone = [self._original_model, self._original_vars_map]
        self.model, self._vars_map = copy.deepcopy(to_clone)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        self.__copy_model()
        var_values = {n: int(v) for n, v in var_values.items()}

        for var_name, value in var_values.items():
            var = self._vars_map[var_name]
            self.model.Add(var == value)

    def unfix_vars(self, vars: list[str]) -> None:
        self.__copy_model()

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        res = {var_name: self._solver.value(self._vars_map[var_name]) for var_name in vars_to_get}
        return res

    def get_obj(self) -> float:
        return self._solver.ObjectiveValue()

    def solve(self) -> None:
        status = self._solver.Solve(self.model)

        _ortools_status_map = {
            cp_model.OPTIMAL: CST.OPTIMAL,
            cp_model.INFEASIBLE: CST.INFEASIBLE,

            # Feasibility checking problem without objective function
            cp_model.FEASIBLE: CST.OPTIMAL,
        }
        self.status = _ortools_status_map.get(status, CST.UNKNOWN)


if __name__ == "__main__":
    pass

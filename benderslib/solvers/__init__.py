# coding:utf-8

__version__ = "0.1.0"
__author__ = "Peng-Hui Guo"
__email__ = "m@guo.ph"
__license__ = "GPL-3.0"
__url__ = "https://benders.dev"
__copyright__ = "Copyright 2025, https://guo.ph"

from abc import ABCMeta

from ._base import SolverBase


def _create_placeholder_solver(name: str, install_message: str):
    """Dynamically creates a placeholder solver class.

    This function is used to create a dummy solver class when the actual
    solver library is not installed. The created class inherits from
    `SolverBase` and raises an `ImportError` upon instantiation,
    prompting the user to install the required package.

    It also implements dummy versions of all abstract methods defined in
    `SolverBase` to ensure that the placeholder class can be created
    without `TypeError`s for un-implemented abstract methods.
    """

    def __init__(self, *args, **kwargs):
        # pylint: disable=super-init-not-called
        raise ImportError(
            f"<{name}> is not installed. {install_message}"
        )

    def dummy_method(*args, **kwargs):
        pass

    class_attrs = {
        '__init__': __init__,
        '__doc__': f"Placeholder for the '{name}' solver. Raises ImportError on instantiation."
    }

    if isinstance(SolverBase, ABCMeta) and hasattr(SolverBase, '__abstractmethods__'):
        for method_name in SolverBase.__abstractmethods__:
            class_attrs[method_name] = dummy_method

    PlaceholderSolver = type(name, (SolverBase,), class_attrs)
    return PlaceholderSolver


try:
    from ._gurobi import Gurobi
except ImportError:
    Gurobi = _create_placeholder_solver("Gurobi", "Install it via 'pip install gurobipy'.")

try:
    from ._copt import Copt
except ImportError:
    Copt = _create_placeholder_solver("Copt", "Install it via 'pip install coptpy'.")

try:
    from ._pyomo import Pyomo
except ImportError:
    Pyomo = _create_placeholder_solver("Pyomo", "Install it via 'pip install pyomo'.")

try:
    from ._scip import Scip
except ImportError:
    Scip = _create_placeholder_solver("SCIP", "Install it via 'pip install pyscipopt'.")

try:
    from ._cplex import Cplex
except ImportError:
    Cplex = _create_placeholder_solver("Cplex", "Install it via 'pip install cplex'.")

try:
    from ._ortools import Ortools
except ImportError:
    Ortools = _create_placeholder_solver("Ortools", "Install it via 'pip install ortools'.")

__all__ = [
    "SolverBase",
    "Gurobi",
    "Copt",
    "Pyomo",
    "Scip",
    "Cplex",
    "Ortools",
]

# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

from abc import ABCMeta

from ._base import SolverBase, SolverCPBase


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
    CPLEX = _create_placeholder_solver("CPLEX", "Install it via 'pip install cplex'.")

try:
    from ._ortools import Ortools
except ImportError:
    Ortools = _create_placeholder_solver("Ortools", "Install it via 'pip install ortools'.")

try:
    from ._cplexcp import CplexCP
except ImportError:
    CplexCP = _create_placeholder_solver("CPLEX (CP)", "Install it via 'pip install docplex'.")

__all__ = [
    "SolverBase",
    "SolverCPBase",
    "Gurobi",
    "Copt",
    "Pyomo",
    "Scip",
    "Cplex",
    "Ortools",
    "CplexCP",
]

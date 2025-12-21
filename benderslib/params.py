# coding:utf-8

from dataclasses import dataclass, fields

from .consts import BendersConsts as CST


@dataclass
class BendersParams:
    """Parameters for BendersLib that can be manipulated by the users.

    A :class:`BendersParams` instance is passed to the Benders algorithm during its initialization.
    The users may initialize a :class:`BendersParams` instance with customized parameters
    and then pass it to the Benders algorithm.
    Parameters that are not specified will take their default values.

    Example
    ----------------

    .. code-block:: python

        # Initialize with customized parameters
        params = BendersParams(tol_abs=1e-5, time_limit=3600)

        # Or, using a dictionary
        # params = BendersParams(**{'tol_abs': 1e-5, 'time_limit': 3600})

        # Or, using default parameters
        # params = BendersParams()

        BD = ClassicalBenders(mp, sp, complicating_vars, params=params)
    """

    # Theta (estimator in master problem for subproblem's objective)
    theta_lb: float = 0
    """Lower bound for the theta variable in the master problem."""

    # Convergence
    tol_abs: float = 1e-6
    """Absolute tolerance for convergence, terminate when ``abs(UB - LB) <= tol_abs``."""
    tol_rel: float = 1e-6
    """Relative tolerance for convergence, terminate when ``abs(UB - LB) / abs(UB) <= tol_rel``."""
    time_limit: float = float('Inf')
    """Time limit for the Benders algorithm in seconds."""
    iter_limit: int = float('Inf')
    """Iteration limit for the Benders algorithm."""

    # L-shaped method
    multi_opti_cut: bool = False
    """**[L-shaped method]** Whether to add multiple optimality cuts per scenario in each iteration of the L-shaped method."""
    multi_feas_cut: bool = False
    """**[L-shaped method]** Whether to add multiple feasibility cuts per scenario in each iteration of the L-shaped method.
    If ``False``, one feasibility cut is added when a infeasible subproblem is found;
    If ``True``, all extreme rays are used to generate multiple feasibility cuts."""

    # Logging
    log_freq_sec: float = 0.5
    """Frequency (in seconds) to log messages to the console/file."""
    log_freq_iter: int = 1
    """Frequency (in iterations) to log messages to the console/file."""
    log_level: str = 'INFO'
    """Logging level can be ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``. 
    See Python's `logging levels <https://docs.python.org/3/library/logging.html#logging-levels>`_ for details."""
    log_to_console: bool = True
    """Whether to print log messages to the console."""
    log_file: str = None
    """File path to save log messages. If ``None``, logs are not saved to a file."""

    def __repr__(self):
        # Only print non-default parameters
        default = BendersParams()

        non_default_params = []
        for field in fields(self):
            field_name = field.name
            current_value = getattr(self, field_name)
            default_value = getattr(default, field_name)
            if current_value != default_value:
                n = field_name + ':'
                non_default_params.append(
                    f" - {n.ljust(CST.LOG_NAME_WIDTH)}{current_value} [Default: {default_value}]")

        if non_default_params:
            return "Benders Parameters (non-default):\n" + "\n".join(non_default_params)
        else:
            return 'Benders Parameters: \n - All default'

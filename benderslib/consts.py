# coding:utf-8

class BendersConsts:
    """Immutable constants used in BendersLib.

    The constants can be used like ``CST.OPTIMAL``, where ``CST`` is a global alias
    for :class:`BendersConsts`.

    Example
    -----------

    .. code-block:: python

        from benderslib import CST

        if BD.result.status == CST.OPTIMAL:
            print("Benders algorithm found an optimal solution.")
    """

    # Ensure immutability
    __slot__ = ()

    # BendersLib/Solver status
    UNSOLVED = 'UNSOLVED'
    """Status indicating the problem has not been solved yet."""
    FEASIBLE = 'FEASIBLE'
    """Status indicating at least one feasible solution has been found."""
    OPTIMAL = 'OPTIMAL'
    """Status indicating an optimal solution has been found."""
    INFEASIBLE = 'INFEASIBLE'
    """Status indicating the problem is infeasible."""
    TIMEOUT = 'TIMEOUT'
    """Status indicating the solver reached the time limit."""
    ERROR = 'ERROR'
    """Status indicating an unknown error occurred during solving."""

    # Estimator
    ESTIMATOR_NAME = 'theta'
    """Name of the estimator variable in the master problem."""
    ESTIMATOR_FORMAT = 'theta_{}'
    """Format string for naming estimator variables with indices."""

    # Variable types
    BINARY = 'B'
    """Identifier for binary variable type."""
    INTEGER = 'I'
    """Identifier for integer variable type."""
    CONTINUOUS = 'C'
    """Identifier for continuous variable type."""

    # Cut types
    OPTIMALITY = 'OPTIMALITY'
    """Type identifier for optimality cuts."""
    FEASIBILITY = 'FEASIBILITY'
    """Type identifier for feasibility cuts."""

    # Cut senses
    LE = '<='
    """ Less than or equal to cut sense."""
    GE = '>='
    """ Greater than or equal to cut sense."""
    EQ = '=='
    """ Equal to cut sense."""

    # Objective senses
    MIN = 'MIN'
    """ Identifier for minimization objective sense."""
    MAX = 'MAX'
    """ Identifier for maximization objective sense."""

    # Logging
    LOG_NAME_WIDTH = 25
    """ For formatting log before and after iterations."""
    LOG_ITER_WIDTH = 12
    """ For formatting log during iterations."""

    # Ensure immutability
    def __setattr__(self, key, value):
        raise AttributeError(f"Cannot modify constant class attributes: {key}")


if __name__ == '__main__':
    pass

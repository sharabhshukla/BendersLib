# coding:utf-8

from dataclasses import dataclass, field

from .consts import BendersConsts as CST


@dataclass
class BendersResult:
    """Results and statistics from the Benders Decomposition process.

    Example
    -----------

    .. code-block:: python

        BD = BendersSolver(...)
        BD.solve()
        print(BD.result.obj)
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

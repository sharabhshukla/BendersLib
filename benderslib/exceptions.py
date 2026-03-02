# coding:utf-8

class BendersError(Exception):
    """Base class for exceptions in benderslib."""

    code = None
    description = "A generic error in the BendersLib library."

    def __init__(self, message=None, **kwargs):
        if message is None:
            message = self.description

        self.message = message
        self.context = kwargs
        super().__init__(self.message)

    def __str__(self):
        code_str = f"[{self.code}] " if self.code else ""
        context_str = ""
        if self.context:
            context_str = " (Context: " + ", ".join(f"{k}={v}" for k, v in self.context.items()) + ")"

        return f"{code_str}{self.message}{context_str}"


class BendersMasterError(BendersError):
    """Exception raised for errors in the master problem."""
    code = "MP-000"
    description = "An error occurred in the master problem."
    help_url = "https://benders.dev/docs/errors#MP-000"


class BendersSubError(BendersError):
    """Exception raised for errors in the subproblem."""
    code = "SP-000"
    description = "An error occurred in the subproblem."


class BendersCutError(BendersError):
    """Exception raised for errors in the cut generation."""
    code = "CT-000"
    description = "An error occurred during cut generation."


class BendersSolverError(BendersError):
    """Exception raised for errors in the solver."""
    code = "SL-000"
    description = "An error occurred during solving the problem."

# coding:utf-8

__version__ = "0.1.0"
__author__ = "Peng-Hui Guo"
__email__ = "m@guo.ph"
__license__ = "GPL-3.0"
__url__ = "https://benders.dev"
__copyright__ = "Copyright 2025"

from .consts import BendersConsts
from .consts import BendersConsts as CST
from .params import BendersParams
from .result import BendersResult

from .solvers import SolverBase, SolverCPBase

from .core import (
    ProblemBase,
    MasterProblem,
    SubProblem,
    LogicBasedSubProblem,
    SubProblems,
    Cut,
    OptimalityCut,
    FeasibilityCut,
    CutGenerator,
    BendersSolver
)

from .cuts import (
    # Cut types
    ClassicalOC,
    ClassicalFC,
    NoGoodFC,
    CombinatorialOC,
    LShapedOC,
    GeneralizedOC,
    GeneralizedFC,
    GeneLShapedOC,

    # Cut generators
    ClassicalFCGen,
    ClassicalOCGen,
    CombinatorialFCGen,
    CombinatorialOCGen,
    LShapedOCGen,
    LShapedFCGen,
    IntegerLShapedOCGen,
    IntegerLShapedFCGen,
    GeneralizedOCGen,
    GeneralizedFCGen,
    GeneLShapedOCGen
)

from .benders import (
    AnnotationBenders,
    ClassicalBenders,
    CombinatorialBenders,
    LShaped,
    IntegerLShaped,
    LogicBasedBenders,
    GeneralizedBenders,
    GeneLShaped
)

from .callback import (
    BendersContext,
    CallbackBase,
)

__all__ = [
    # Data
    "BendersConsts",
    "CST",
    "BendersParams",
    "BendersResult",

    # Solver
    "SolverBase",
    "SolverCPBase",

    # Core
    "ProblemBase",
    "MasterProblem",
    "SubProblem",
    "LogicBasedSubProblem",
    "SubProblems",
    "Cut",
    "OptimalityCut",
    "FeasibilityCut",
    "CutGenerator",
    "BendersSolver",

    # Cut types
    "ClassicalOC",
    "ClassicalFC",
    "NoGoodFC",
    "CombinatorialOC",
    "LShapedOC",
    "GeneralizedOC",
    "GeneralizedFC",
    "GeneLShapedOC",

    # Cut generators
    "ClassicalFCGen",
    "ClassicalOCGen",
    "CombinatorialFCGen",
    "CombinatorialOCGen",
    "LShapedOCGen",
    "LShapedFCGen",
    "IntegerLShapedOCGen",
    "IntegerLShapedFCGen",
    "GeneralizedOCGen",
    "GeneralizedFCGen",
    "GeneLShapedOCGen",

    # Benders methods
    "AnnotationBenders",
    "ClassicalBenders",
    "CombinatorialBenders",
    "LShaped",
    "IntegerLShaped",
    "LogicBasedBenders",
    "GeneralizedBenders",
    "GeneLShaped",

    # Callbacks
    "BendersContext",
    "CallbackBase",
]

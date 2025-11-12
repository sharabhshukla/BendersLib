# coding:utf-8

__version__ = "0.1.0"
__author__ = "Peng-Hui Guo"
__email__ = "m@guo.ph"
__license__ = "GPL-3.0"
__url__ = "https://benders.dev"
__copyright__ = "Copyright 2025"

from .consts import BendersConsts
from .consts import BendersConsts as CST

from .params import (
    BendersParams,
)

from .solver import (
    SolverBase,
    Gurobi,
)

from .core import (
    ProblemBase,
    MasterProblem,
    SubProblem,
    SubProblems,
    Cut,
    OptimalityCut,
    FeasibilityCut,
    CutGenerator,
    BendersResult,
    BendersSolver
)

from .cut import (
    ClassicalOC,
    ClassicalFC,
    NoGoodFC,
    CombinatorialOC,
    LShapedOC,

    ClassicalFCGen,
    ClassicalOCGen,
    CombinatorialFCGen,
    CombinatorialOCGen,
    LShapedOCGen,
    LShapedFCGen,
    IntegerLShapedOCGen,
    IntegerLShapedFCGen,
)

from .benders import (
    ClassicalBenders,
    CombinatorialBenders,
    LShaped,
    IntegerLShaped
)

from .annotation import (
    AnnotationBenders,
)

__all__ = [
    "BendersConsts",
    "CST",

    "BendersParams",

    "SolverBase",
    "Gurobi",

    "ProblemBase",
    "MasterProblem",
    "SubProblem",
    "SubProblems",
    "Cut",
    "OptimalityCut",
    "FeasibilityCut",
    "CutGenerator",
    "BendersResult",
    "BendersSolver",

    "ClassicalOC",
    "ClassicalFC",
    "NoGoodFC",
    "CombinatorialOC",
    "LShapedOC",

    "ClassicalFCGen",
    "ClassicalOCGen",
    "CombinatorialFCGen",
    "CombinatorialOCGen",
    "LShapedOCGen",
    "LShapedFCGen",
    "IntegerLShapedOCGen",
    "IntegerLShapedFCGen",

    "ClassicalBenders",
    "CombinatorialBenders",
    "LShaped",
    "IntegerLShaped",

    "AnnotationBenders",
]

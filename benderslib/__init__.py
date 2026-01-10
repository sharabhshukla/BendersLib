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

from .solvers import (
    SolverBase,
)

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
    BendersResult,
    BendersSolver
)

from .cut import (
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
    ClassicalBenders,
    CombinatorialBenders,
    LShaped,
    IntegerLShaped,
    LogicBasedBenders,
    GeneralizedBenders,
    GeneLShaped
)

from .annotation import (
    AnnotationBenders,
)

__all__ = [
    "BendersConsts",
    "CST",

    "BendersParams",

    "SolverBase",

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
    "BendersResult",
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
    "ClassicalBenders",
    "CombinatorialBenders",
    "LShaped",
    "IntegerLShaped",
    "LogicBasedBenders",
    "GeneralizedBenders",
    "GeneLShaped",

    "AnnotationBenders",
]

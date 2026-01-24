Core Classes
=======================================

.. currentmodule:: benderslib

Benders Cut
-----------------------------------------

.. autoclass:: Cut
   :inherited-members:
   :show-inheritance:
   :exclude-members: _params

.. autoclass:: OptimalityCut
   :inherited-members:
   :show-inheritance:
   :exclude-members: ctype, _params

.. autoclass:: FeasibilityCut
   :inherited-members:
   :show-inheritance:
   :exclude-members: ctype, _params

.. autoclass:: CutGenerator
   :inherited-members:
   :show-inheritance:
   :exclude-members: _generate

Master and Sub Problem
-----------------------------------------

.. autoclass:: ProblemBase
   :inherited-members:
   :show-inheritance:

.. autoclass:: MasterProblem
   :inherited-members:
   :show-inheritance:
   :exclude-members: _add_estimators


.. autoclass:: SubProblem
   :inherited-members:
   :show-inheritance:

.. autoclass:: SubProblems
   :inherited-members:
   :show-inheritance:

.. autoclass:: LogicBasedSubProblem
   :inherited-members:
   :show-inheritance:

Benders Algorithm
-----------------------------------------

.. autoclass:: BendersSolver
   :inherited-members:
   :show-inheritance:

.. _api-annotation:

Annotation Benders Decomposition
--------------------------------------

.. autoclass:: AnnotationBenders
    :inherited-members:

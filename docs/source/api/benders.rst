:tocdepth: 3

Benders Methods
======================================

.. currentmodule:: benderslib

.. _api-classical:

Classical Benders Decomposition
--------------------------------------

Please refer to :doc:`../tutorials/classical` for its theory and
the definition of classical optimality cut (:class:`ClassicalOC`)
and classical feasibility cut (:class:`ClassicalFC`).

.. autoclass:: ClassicalOCGen
   :show-inheritance:

.. autoclass:: ClassicalFCGen
   :show-inheritance:

.. autoclass:: ClassicalBenders
   :inherited-members:
   :show-inheritance:

.. _api-cbd:

Combinatorial Benders Decomposition
--------------------------------------

Please refer to :doc:`../tutorials/cbd` for its theory and
the definition of no-good (feasibility) cut (:class:`NoGoodFC`) and combinatorial optimality cut (:class:`CombinatorialCut`).

.. autoclass:: CombinatorialOCGen
    :show-inheritance:

.. autoclass:: CombinatorialFCGen
    :show-inheritance:

.. autoclass:: CombinatorialBenders
    :inherited-members:
    :show-inheritance:

.. _api-lshape:

L-shaped Method
--------------------------------------

Please refer to :doc:`../tutorials/lshape` for its theory and
the definition of optimality cut (:class:`LShapedOC` for single-cut version, :class:`ClassicalOC` for multi-cut version)
and feasibility cut (:class:`ClassicalFC`).
Note that L-shaped method is a generalization of classical Benders
decomposition applied to two-stage stochastic programming problems.
Therefore, :class:`ClassicalOC` and :class:`ClassicalFC` are also used in the L-shaped method.

.. autoclass:: LShapedOCGen
   :show-inheritance:

.. autoclass:: LShapedFCGen
   :show-inheritance:

.. autoclass:: LShaped
   :inherited-members:
   :show-inheritance:

.. _api-ilshape:

Integer L-shaped Method
--------------------------------------

Please refer to :doc:`../tutorials/ilshape` for its theory,
the definition of integer L-shaped optimality cut (:class:`CombinatorialOC`),
and no-good feasibility cut (:class:`NoGoodFC`).
The integer L-shaped method is an extension of the L-shaped method and the Combinatorial Benders decomposition
to solve two-stage stochastic integer programming problems.
The cut used in this method are the same as those in Combinatorial Benders decomposition,
and the algorithmic framework is similar to that of the L-shaped method.

.. autoclass:: IntegerLShapedOCGen
   :show-inheritance:

.. autoclass:: IntegerLShapedFCGen
   :show-inheritance:

.. autoclass:: IntegerLShaped
   :inherited-members:
   :show-inheritance:

.. _api-lbbd:

Logic-based Benders Decomposition
--------------------------------------

The Logic-based Benders Decomposition is highly customizable.
When using non-standard solvers that are not natively supported by BendersLib (typically heuristics or exact algorithms),
users need to define their own subproblem, inheriting from :class:`LogicBasedSubProblem`.
Users also need to implement their own optimality/feasibility cut generator, inheriting from :class:`CutGenerator`.

.. autoclass:: LogicBasedSubProblem
   :show-inheritance:

.. autoclass:: LogicBasedBenders
   :inherited-members:
   :show-inheritance:

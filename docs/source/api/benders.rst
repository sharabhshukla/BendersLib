:tocdepth: 3

Benders Methods
======================================

.. currentmodule:: benderslib

A specific Benders method is composed of a master problem, one or more
subproblems, and a Benders algorithm that orchestrates the solution process.
The master and subproblems are instances of :class:`MasterProblem` and
:class:`SubProblem`, respectively, while the Benders algorithm is an instance
of a class derived from :class:`BendersSolver`.
The Benders algorithm iteratively solves the master problem and subproblems,
adding Benders cuts to the master problem based on the solutions of the
subproblems until convergence is achieved.
What make different Benders methods different are the specific types of
Benders cuts used.
In this section, we present several Benders methods implemented in
BendersLib, each with its own unique Benders cuts.

Built-in Benders Cuts
--------------------------------------

.. autoclass:: ClassicalOC
   :inherited-members:
   :show-inheritance:

.. autoclass:: ClassicalFC
   :inherited-members:
   :show-inheritance:

.. autoclass:: NoGoodFC
   :inherited-members:
   :show-inheritance:

.. autoclass:: CombinatorialOC
   :inherited-members:
   :show-inheritance:

.. autoclass:: LShapedOC
   :inherited-members:
   :show-inheritance:

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

L-shaped Method
--------------------------------------

Please refer to :doc:`../tutorials/lshape` for its theory and
the definition of optimality cut (:class:`ClassicalOC` for single-cut
version, :class:`LShapedOC` for multi-cut version))
and feasibility cut (:class:`ClassicalFC`).
Note that L-shaped method is a generalization of classical Benders
decomposition applied to two-stage stochastic programming problems.
Therefore, the Benders cuts used in L-shaped method are the same as those
in classical Benders decomposition.

.. autoclass:: LShapedOCGen
   :show-inheritance:

.. autoclass:: LShapedFCGen
   :show-inheritance:

.. autoclass:: LShaped
   :inherited-members:
   :show-inheritance:

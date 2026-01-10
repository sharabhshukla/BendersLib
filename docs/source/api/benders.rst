:tocdepth: 3

Benders Methods
======================================

.. currentmodule:: benderslib

.. _api-classical:

Classical Benders Decomposition
--------------------------------------

.. autoclass:: ClassicalBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. _api-cbd:

Combinatorial Benders Decomposition
--------------------------------------

.. autoclass:: CombinatorialBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. _api-lshape:

L-shaped Method
--------------------------------------

.. autoclass:: LShaped
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. autoclass:: GeneLShaped
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. _api-ilshape:

Integer L-shaped Method
--------------------------------------

.. autoclass:: IntegerLShaped
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. _api-lbbd:

Logic-based Benders Decomposition
--------------------------------------

.. autoclass:: LogicBasedBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. _api-gbd:

Generalized Benders Decomposition
--------------------------------------

.. autoclass:: GeneralizedBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

Cut Generators
--------------------------------------

.. autoclass:: ClassicalOCGen
   :show-inheritance:

.. autoclass:: ClassicalFCGen
   :show-inheritance:

.. autoclass:: CombinatorialOCGen
    :show-inheritance:

.. autoclass:: CombinatorialFCGen
    :show-inheritance:

.. autoclass:: LShapedOCGen
   :show-inheritance:

.. autoclass:: LShapedFCGen
   :show-inheritance:

.. autoclass:: IntegerLShapedOCGen
   :show-inheritance:

.. autoclass:: IntegerLShapedFCGen
   :show-inheritance:

.. autoclass:: GeneralizedOCGen
   :show-inheritance:

.. autoclass:: GeneralizedFCGen
   :show-inheritance:

.. autoclass:: GeneLShapedOCGen
   :show-inheritance:

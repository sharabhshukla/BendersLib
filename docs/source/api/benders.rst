:tocdepth: 3

Benders Methods
======================================

.. currentmodule:: benderslib

Deterministic Benders Methods
--------------------------------------

.. autoclass:: ClassicalBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. autoclass:: CombinatorialBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. autoclass:: GeneralizedBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

Stochastic Benders Methods
--------------------------------------

.. autoclass:: LShaped
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. autoclass:: IntegerLShaped
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. autoclass:: LogicBasedBenders
    :inherited-members:
    :show-inheritance:
    :exclude-members: master_problem, sub_problem, complicating_vars, optimality_cut, feasibility_cut, params, result

.. autoclass:: GeneLShaped
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

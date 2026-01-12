Numerical Issues
===================

.. currentmodule:: benderslib

When working with optimization solvers, it's common to encounter numerical precision issues.
These can affect both the coefficients of generated cuts and the comparison of floating-point values like objective functions.
BendersLib handles these challenges as follows.

Comparing Objective Function Values
-----------------------------------

A core step in the Benders decomposition algorithm is to check if an optimality cut needs to be added.
This is done by comparing the objective value of the subproblem (``sub_obj``) with the current value of
the master problem's estimator variable (``theta``). A cut is added if ``sub_obj`` is *greater than* ``theta``.

However, due to floating-point inaccuracies, a direct comparison like ``sub_obj > theta`` can be unreliable.
The subproblem's objective might be trivially larger than the estimator due to numerical noise,
leading to the addition of weak or unnecessary cuts.

To perform a robust comparison, BendersLib involves a parameter :attr:`~BendersParams.tol_obj_diff` that defines
a tolerance level for the difference between ``sub_obj`` and ``theta``.
This ensures that a cut is only added when the violation is significant, i.e., when the difference exceeds this tolerance
(``sub_obj - theta > tol_obj_diff``).

This approach is used within BendersLib's own cut generators for Benders methods with multiple subproblems,
such as in :class:`LShapedOCGen`, :class:`IntegerLShapedOCGen`, and :class:`GeneLShapedOCGen`,
to ensure that only meaningful optimality cuts are added to the master problem.

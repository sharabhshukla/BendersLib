Numerical Issues
===================

.. currentmodule:: benderslib

When working with optimization solvers, it's common to encounter numerical precision issues.
These can affect both the coefficients of generated cuts and the comparison of floating-point values like objective functions.
BendersLib handles these challenges as follows.

Comparing Objective Function Values
--------------------------------------------

A core step in the stochastic Benders decomposition algorithm is to check if an optimality cut needs to be added.
This is done by comparing the objective value of the subproblem (``sub_obj``) with the current value of
the master problem's estimator variable (``theta``). A cut is added if ``sub_obj`` is *greater than* ``theta``.

However, due to floating-point inaccuracies, a direct comparison like ``sub_obj > theta`` can be unreliable.
The subproblem's objective might be trivially larger than the estimator due to numerical noise,
leading to the addition of unnecessary cuts.

To perform a robust comparison, BendersLib involves a parameter :attr:`~BendersParams.tol_obj_diff` that defines
a tolerance level for the difference between ``sub_obj`` and ``theta``.
This ensures that a cut is only added when the violation is significant, i.e., when the difference exceeds this tolerance
(``sub_obj - theta > tol_obj_diff``).

This approach is used within BendersLib's own cut generators for Benders methods with multiple subproblems,
such as in :class:`LShapedOCGen`, :class:`IntegerLShapedOCGen`, and :class:`GeneLShapedOCGen`,
to ensure that only meaningful optimality cuts are added to the master problem.

Determining Whether Two Cuts are Identical
--------------------------------------------

Another numerical challenge is identifying duplicate cuts. During the Benders decomposition process,
the same cut may be generated in different iterations. Adding duplicate cuts to the master problem is
inefficient and can slow down the solver.

Due to floating-point arithmetic, the coefficients and right-hand side (RHS) values of two cuts that are
mathematically identical might have small numerical differences.
A simple direct comparison would fail to identify them as duplicates.

To address this, BendersLib uses the :attr:`~BendersParams.tol_cut_diff` parameter.
When checking if a new cut is a duplicate of an existing one, the algorithm compares their coefficients
and RHS values within this tolerance. If all corresponding values are closer than ``tol_cut_diff``,
the cuts are considered identical, and the new cut is discarded.

This logic is implemented in the ``__eq__`` method of the :class:`~core.Cut` class.
To ensure consistency, the ``__hash__`` method is also adapted. It discretizes the floating-point numbers
(coefficients and RHS) based on the tolerance before hashing. This guarantees that cuts considered equal
under the specified tolerance will also have the same hash value, allowing them to be managed correctly.

.. _manual_numerical_large_cut_coefficients:

Handling Large Cutting Coefficients
--------------------------------------------

In Benders decomposition, cut coefficients can sometimes become excessively large, leading to numerical instability.
Mathematically equivalent cuts can lead to different convergence performances due to the
limitations of finite-precision floating-point arithmetic. Cuts with large coefficients
can make the master problem's constraint matrix ill-conditioned, leading to slower
convergence, inaccurate solutions, or even solver failure.
For instance, consider two mathematically equivalent cuts

.. math::

   10^9 x + 10^9 y & \ge 10^9 \\
   x + y & \ge 1.

Solvers use tolerances to determine whether a solution satisfies a constraint.
A constraint :math:`a^T x \ge b` is considered satisfied if :math:`a^T x - b \ge -\epsilon`,
where :math:`\epsilon` is a small positive number (e.g., :math:`10^{-6}`).
For the normalized constraint :math:`x + y \ge 1`, if a solution
results in :math:`x+y = 1 - 10^{-7}`, its violation is only :math:`10^{-7}`.
This solution is very close to the feasible boundary and would be accepted by the solver's tolerance.
However, for the constraint with large coefficients, :math:`10^9 x + 10^9 y \ge 10^9`,
the same solution yields :math:`10^9(x+y) = 10^9(1 - 10^{-7}) = 10^9 - 100`.
The constraint violation is a massive :math:`100`.
This far exceeds a solver's standard tolerance, and the solution would be flagged as infeasible.
This makes the solver struggle to find a feasible solution, leading to slow convergence or failure.

Normalizing the cut,
even though it doesn't change the feasible region, creates a better-conditioned problem
that is more numerically stable for the solver to handle, often resulting in faster and more reliable convergence.
Readers can refer to :doc:`../examples/expert/normalize_cut` for an example of how to normalize cuts
using :doc:`callbacks <../manual/callbacks>` in BendersLib.

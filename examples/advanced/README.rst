Advanced Examples
----------------------

For more complex problems that do not fit the standard Benders decomposition patterns,
BendersLib offers an advanced usage mode.
This mode provides the flexibility to :ref:`customize subproblem solver <manual_custom_sub>` and
:ref:`cut generator <manual_custom_cut>`, which are the key components of the Benders algorithm.
This feature is especially useful for implementing :doc:`../../tutorials/lbbd`,
as it allows the subproblem to be any type of optimization problem without a standard method for formulating Benders cuts.

Advanced Examples
----------------------

For more complex problems that do not fit the standard Benders decomposition patterns,
BendersLib offers an advanced usage mode.
This mode provides the flexibility to customize subproblem solver and cut generator, which are the
key components of the Benders algorithm.
This feature is especially useful for implementing :doc:`../../tutorials/lbbd`,
as it allows the subproblem to be any type of optimization problem without a standard method for formulating Benders cuts.

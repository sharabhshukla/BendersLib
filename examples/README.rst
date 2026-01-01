Examples
======================

This directory contains example scripts that demonstrate how to use the library.

Deterministic
----------------------

- :doc:`classical_benders`: A very simple example of classical Benders decomposition.
- :doc:`annotation_benders`: Automatic problem decomposition.
- :doc:`cbd`: Combinatorial Benders decomposition with binary complicated variables.
- :doc:`cbd_iis`: Combinatorial Benders decomposition with IIS for stronger, customized no-good cuts.
- :doc:`lbbd`: Logic-based Benders decomposition with custom subproblem solver.
- :doc:`gbd`: Generalized Benders decomposition with non-linear subproblems.

Stochastic
----------------------

- :doc:`lshape`: A simple two-stage stochastic programming example with LP recourse using the L-shaped method.
- :doc:`ilshape`: Integer L-shaped method for two-stage stochastic programming with binary complicating variables and integer recourse.
- :doc:`ilshape_iis`: Integer L-shaped method with IIS for stronger, customized no-good cuts.
- :doc:`lbbd_sp`: Logic-based Benders decomposition for two-stage stochastic programming with custom subproblem solver.
- :doc:`lbbd_lshape`: Implementation of the L-shaped method using Logic-based Benders Decomposition.

Applications
----------------------

- :doc:`lbbd_location`: Facility location problem solved using Logic-based Benders Decomposition.

Benchmarking
----------------------

Others
----------------------

- :doc:`custom_template`: A template for creating custom Benders decomposition implementations.
- :doc:`decompose`: Retrieving master and sub problems from a complete model.

Gallery
----------------------

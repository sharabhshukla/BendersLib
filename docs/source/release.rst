Release Notes
===================================

Version 0.5.0 (Beta) - 2026-04-17
-------------------------------------

We are excited to announce the first public beta release of *BendersLib*,
a Python library dedicated to Benders decomposition!
To get started, please see the :doc:`Quickstart <index>` section in our documentation.
We welcome any feedback. Please report any issues
or suggestions on our `GitHub Issues page <https://github.com/phguo/BendersLib/issues>`_.
We also welcome contributions to the library.

Features
~~~~~~~~~~~~~

*   **Benders Decomposition Variants**:
    :doc:`Classical Benders Decomposition <tutorials/classical>`,
    :doc:`Combinatorial Benders Decomposition <tutorials/cbd>`,
    :doc:`Generalized Benders Decomposition <tutorials/gbd>`,
    :doc:`L-shaped Method <tutorials/lshaped>` (linear and convex recourse),
    :doc:`Integer L-shaped Method <tutorials/ilshaped>`, and
    :doc:`Logic-based Benders Decomposition <tutorials/lbbd>`.

*   **Extensibility**:
    :ref:`Annotated Benders Decomposition <manual_decompose_solve>`,
    :ref:`Custom Cut Generation <manual_custom_cut>`,
    :ref:`Custom Subproblem Solvers <manual_custom_sub>`, and
    :doc:`Callbacks </manual/callbacks>`.

*   **Enhancement Options**:
    :ref:`Branch-and-check Method <enhance_branch_and_check>`,
    :ref:`Parallel Subproblem Solving <enhance_parallel>`,
    :ref:`Multi-cut Generation <enhance_multi_cut>`,
    :ref:`Cut Normalization <enhance_cut_normalization>`, and
    IIS-based Feasibility Cut Generation (:attr:`~benderslib.BendersParams.use_iis_cut`).

*   **Solver Agnostic**:
    Built-in interfaces for :ref:`popular solvers <solver-table>`.

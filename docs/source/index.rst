.. image:: _static/benderslib.png
   :align: center
   :height: 250px

------

Home
===================================

**BendersLib** (https://benders.dev) is a Python library that supports a range of Benders decomposition variants,
including :doc:`tutorials/classical`, :doc:`tutorials/cbd`, :doc:`tutorials/lshaped`, :doc:`tutorials/ilshaped`,
:doc:`tutorials/gbd`, and :doc:`tutorials/lbbd`.
While BendersLib provides :doc:`built-in implementations of these methods <api/benders>`,
it is designed to be extensible. Users can implement custom Benders decomposition methods by
customizing :ref:`subproblem solvers <manual_custom_sub>` and :ref:`cut generators <manual_custom_cut>`,
and defining :doc:`callback functions <manual/callbacks>` for :doc:`enhancement strategies <tutorials/enhance>`.
BendersLib is solver agnostic and has :doc:`built-in interfaces <manual/solvers>` for
popular Mathematical Programming and Constraint Programming solvers.
Its support for rapid prototyping and high extensibility are designed to meet the needs of
both researchers and practitioners in Operations Research and related fields.

Features
-----------------------------------

BendersLib provides tutorials, built-in implementations, and
code examples for various representative Benders decomposition
variants, as listed below. Since BendersLib is designed to
be extensible, allowing users to implement their own Benders cuts,
subproblem solvers, and callback functions, the variants supported
are not limited to the ones below.

.. list-table:: Benders Decomposition Variants
   :widths: auto
   :header-rows: 1

   * - Variant
     - API
     - Example
   * - :doc:`tutorials/classical`
     - :class:`~benderslib.ClassicalBenders`
     - :doc:`Example <_tags/benders-classical>`
   * - :doc:`tutorials/cbd`
     - :class:`~benderslib.CombinatorialBenders`
     - :doc:`Example <_tags/benders-combinatorial>`
   * - :doc:`tutorials/gbd`
     - :class:`~benderslib.GeneralizedBenders`
     - :doc:`Example <_tags/benders-generalized>`
   * - :doc:`tutorials/lshaped`
     - :class:`~benderslib.LShaped` (linear recourse)
     - :doc:`Example <_tags/benders-l-shaped>`
   * - :doc:`tutorials/lshaped`
     - :class:`~benderslib.GeneLShaped` (convex recourse)
     - :doc:`Example <examples/basic/glshaped>`
   * - :doc:`tutorials/ilshaped`
     - :class:`~benderslib.IntegerLShaped`
     - :doc:`Example <_tags/benders-integer-l-shaped>`
   * - :doc:`tutorials/lbbd`
     - :class:`~benderslib.LogicBasedBenders`
     - :doc:`Example <_tags/benders-lbbd>`
   * - Automatic Decomposition
     - :class:`~benderslib.AnnotationBenders`
     - :doc:`Example <examples/basic/annotation_benders>`

BendersLib works with a variety of solvers through its built-in interfaces.
See :ref:`solver-table` for a comprehensive list of features
of the built-in solver interfaces, which include
Mathematical Programming solvers (
:class:`~.solvers.Copt`,
:class:`~.solvers.Cplex`,
:class:`~.solvers.Gurobi`,
:class:`~.solvers.Scip`,
and :class:`~.solvers.Pyomo`
) and Constraint Programming solvers (
:class:`~.solvers.CplexCP` and
:class:`~.solvers.Ortools`
).

Quickstart
-----------------------------------

Install BendersLib and a solver of your choice (e.g., Gurobi) using pip.

.. code-block:: bash

    pip install benderslib
    pip install gurobipy

Test whether the installation is successful.

.. code-block:: python

    import benderslib as bd

    print(bd.__url__)

    # Should output "https://benders.dev"

BendersLib enables switching from a standard Mathematical Programming model
to Benders decomposition with only a few lines of code.

.. code-block:: python

    from benderslib import AnnotationBenders, ClassicalBenders
    from benderslib.solvers import Gurobi

    from gurobipy import Model, GRB

    # Create a standard Gurobi model
    model = Model()
    x = model.addVar(name="x", vtype=GRB.INTEGER)
    y = model.addVar(name="y", vtype=GRB.CONTINUOUS)
    model.addConstr(x + y >= 15)
    model.addConstr(2 * x + 5 * y >= 30)
    model.setObjective(3 * x + 4 * y)
    model.update()

    # Complicating variable
    complicating_vars = ["x"]

    # Create and solve using Benders decomposition
    benders = AnnotationBenders(
        model,
        solver=Gurobi,
        complicating_vars=complicating_vars,
        benders=ClassicalBenders
    )
    benders.solve()
    print(f"Objective: {benders.result.obj}")
    print(f"Solution: {benders.result.solution}")

The output will be similar to the following, showing the Benders decomposition process and results.

.. code-block:: console

    ====================================================================================
    BendersLib (v0.1.0, GPL-3.0, https://benders.dev) by Peng-Hui Guo (Copyright 2025)
    ------------------------------------------------------------------------------------
    Benders Decomposition:
     - Method:                  ClassicalBenders
     - Complicating Var. No.:   1 [Integer: 1, Binary: 0, Continuous: 0]
     - Optimality Cut:          ClassicalOCGen
     - Feasibility Cut:         ClassicalFCGen
    Master Problem:
     - Variable No.:            2 [Integer: 1, Binary: 0]
     - Constraint No.:          0
     - Solver:                  Gurobi
    Sub Problem:
     - Variable No.:            1 [Integer: 0, Binary: 0]
     - Constraint No.:          2
     - Solver:                  Gurobi
    Benders Parameters:
     - All default
    ------------------------------------------------------------------------------------
           Iter.,           LB,           UB,         Obj.,       Gap(%),   Runtime(s)
    ------------------------------------------------------------------------------------
               1,         0.00,        60.00,        60.00,       100.00,         0.00
    ------------------------------------------------------------------------------------
    Benders Result:
      - Status:                  OPTIMAL
      - Incumbent:               45.0000
      - Bound:                   45.0000
      - Gap (abs.):              0.0000
      - Gap (rel.):              0.00%
      - Solutions No.:           2
      - Iteration No.:           2
      - Cuts No.:                1 [Optimality: 1, Feasibility: 0]
      - Solve Time (sec.):       0.01 [Master: 0.01, Sub: 0.00]
    ====================================================================================
    Objective: 45.0
    Solution: {'x': 15.0, 'y': 0.0}

Citing BendersLib
-----------------------------------

If you use BendersLib in your research, please cite it as follows.

    Guo, PH (2025). *BendersLib: An Extensible Benders Decomposition Library in Python*. Retrieved from https://github.com/phguo/BendersLib

.. code-block:: bibtex

    @misc{Guo2025,
      author = {Guo, Peng-Hui},
      title = {BendersLib: An Extensible Benders Decomposition Library in Python},
      year = {2025},
      publisher = {GitHub},
      journal = {GitHub repository},
      howpublished = {\\url{https://github.com/phguo/BendersLib}}
    }

License
-----------------------------------

BendersLib is licensed under the `GPL-3.0 License <https://github.com/phguo/BendersLib/blob/main/LICENSE>`__.

Contents
-----------------------------------

.. toctree::
   :maxdepth: 4

   self
   tutorials/index.rst
   manual/index.rst
   api/index.rst
   examples/index.rst
   release.rst
   about.rst

.. toctree::
   :caption: Links
   :maxdepth: 1
   :hidden:

   Benders.dev <https://benders.dev>
   BendersLib @GitHub <https://github.com/phguo/BendersLib>
   BendersLib @PyPI <https://pypi.org/project/BendersLib/>
   Getting Help <https://github.com/phguo/BendersLib/issues?q=is%3Aissue>
   Author <https://guo.ph>

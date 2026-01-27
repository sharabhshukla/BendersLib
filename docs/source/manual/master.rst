Master Problem
===============================================

.. currentmodule:: benderslib

.. _manual_master_create:

Create a Master Problem
-----------------------------------------------

To create a master problem, you first need to define the problem using a :ref:`supported solver <solver-table>`.
Then, you can create a :class:`MasterProblem` instance by passing a solver backend instance.
The code snippets below demonstrates how to create master problems using model objects of different solvers.

.. note::

    * Make sure to :ref:`install the needed solver <solver-installation-table>` before running the code.
    * Refer to to :ref:`solver documentation <solver-table>` for more details on creating solver models.

.. hint::

    You do not need to define estimator variables (e.g., :math:`\theta` and :math:`\eta`)
    in the master problem for subproblem costs manually.
    They are defined automatically when you create a :class:`BendersSolver` instance.

Gurobi
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
    :emphasize-lines: 12-

    from gurobipy import Model, GRB
    from benderslib import MasterProblem
    from benderslib.solvers import Gurobi

    # Create a Gurobi model for the master problem
    master_model = Model("Master")
    x = master_model.addVar(name="x", vtype=GRB.INTEGER)
    z = master_model.addVar(name="z")
    master_model.addConstr(z <= x, name="c1")
    master_model.setObjective(x)
    master_model.update()

    # Create a MasterProblem instance
    master_problem = MasterProblem(solver_backend=Gurobi(master_model))
    # Or, simply
    # master_problem = MasterProblem(Gurobi(master_model))

.. seealso::

    **Executable Example**: :doc:`../examples/classical_benders`

.. _manual_decompose:

Create a Master Problem from an Annotated Model
------------------------------------------------

Alternatively, you can create a master/sub problem by decomposing an existing model.
This is useful when you have a complete model and want to apply Benders decomposition.
The :class:`AnnotationBenders` class provides a static method :meth:`~AnnotationBenders._decompose`
that splits a model into a master problem and a subproblem based on a list of master variable names.
Refer to :meth:`SolverBase.make_master_problem` and :meth:`SolverBase.make_sub_problem` for the logic
of creating master and sub problems.
Here is an example of how to create a master/sub problem from an annotated model.

.. code-block:: python
    :emphasize-lines: 17-

    from gurobipy import Model, GRB
    from benderslib import MasterProblem, SubProblem, AnnotationBenders
    from benderslib.solvers import Gurobi

    # Create an original model
    original_model = Model("Original")
    n_vars = 20
    y = original_model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = original_model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)
    original_model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr")
    original_model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)
    original_model.update()

    # Identify complicating variables
    complicating_vars = [v.VarName for v in y.values()]

    # Decompose the model
    master_model, sub_model = AnnotationBenders._decompose(
        original_model,
        Gurobi,
        master_vars=complicating_vars,
        solver_model=True  # Return a solver model
        # solver_model=False  # (Default) Return a MasterProblem instance directly
    )

    # Create MasterProblem/SubProblem instance
    master_problem = MasterProblem(Gurobi(master_model))
    sub_problem = SubProblem(Gurobi(sub_model))

.. seealso::

    - :ref:`manual_decompose_solve`
    - **Executable Examples**: :doc:`../examples/annotation_benders`, :doc:`../examples/api/decompose`

.. _manual_master_add_cut:

Add Benders Cuts to Master Problem
------------------------------------------------

Benders cuts are added to the master problem to iteratively refine the solution space.
The :class:`MasterProblem` class provides an :meth:`~MasterProblem.add_cut` method to add Benders cuts.

.. rubric:: Optimality Cut

An optimality cut is added when the subproblem is feasible and provides a lower bound on the subproblem's cost.
The :class:`ClassicalOC` is an example of an optimality cut.

.. code-block:: python

    from benderslib import ClassicalOC

    # Assume we have the following from the subproblem
    complicating_vars = ['x', 'z']
    var_coefs = {'x': [1, 1], 'z': [1, 0]}
    dual_values = [0.5, 0.5]
    rhs = [14, 2]

    # Create an optimality cut
    optimality_cut = ClassicalOC(
        vars=complicating_vars,
        var_coefs=var_coefs,
        dual_values=dual_values,
        rhs=rhs
    )

    # Add the cut to the master problem
    master_problem.add_cut(optimality_cut)

.. rubric:: Feasibility Cut

A feasibility cut is added when the subproblem is infeasible. It cuts off the master problem solution that led to the infeasibility.
The :class:`ClassicalFC` is an example of a feasibility cut.

.. code-block:: python

    from benderslib import ClassicalFC

    # Assume we have the following from the subproblem
    complicating_vars = ['x', 'z']
    var_coefs = {'x': [1, 1], 'z': [1, 0]}
    extreme_ray = [0.5, -0.5]
    rhs = [14, 2]

    # Create a feasibility cut
    feasibility_cut = ClassicalFC(
        vars=complicating_vars,
        var_coefs=var_coefs,
        extreme_ray=extreme_ray,
        rhs=rhs
    )

    # Add the cut to the master problem
    master_problem.add_cut(feasibility_cut)

.. rubric:: General-Purpose Cut

While BendersLib provides specialized classes like :class:`ClassicalOC` and :class:`ClassicalFC`,
you can also use the base :class:`Cut` class to create any custom linear cut.
This is useful for implementing non-standard Benders decomposition schemes or adding any valid inequality to the master problem.
The :class:`Cut` class requires you to explicitly define all components of a linear constraint:
**variables**, **coefficients**, **right-hand side**, and **sense** of the inequality.

.. code-block:: python

    from benderslib import Cut, CST

    # Define a custom cut: 2*x + 3*z >= 5
    custom_cut = Cut(
        vars=['x', 'z'],
        coefs=[2, 3],
        rhs=5,
        sense=CST.GE,
        ctype=CST.OPTIMALITY,  # Specify if it's for optimality or feasibility
        name="MyCustomCut"
    )

    # Add the custom cut to the master problem
    master_problem.add_cut(custom_cut)

.. seealso::

    Refer to :doc:`cut` for more details on Benders cuts in BendersLib.

Solve and Access Results
-------------------------------------------------

Once the master problem is defined, you can solve it and retrieve the results.

.. rubric:: Solve the Problem

The :meth:`~MasterProblem.solve` method is used to solve the current master problem relaxation.
After solving, you can check the status and objective value.

.. code-block:: python

    from benderslib import BendersConsts as CST

    # Solve the master problem
    master_problem.solve()

    # Check the solution status
    if master_problem.status == CST.OPTIMAL:
        print("Master problem solved to optimality.")
        # Get the objective value
        obj_val = master_problem.get_obj()
        print(f"Objective value: {obj_val}")

.. rubric:: Access Variable Values

After a successful solve, you can retrieve the values of the variables, which will be used to build the subproblem.

.. code-block:: python

    # Get the values of all complicating variables
    solution = master_problem.get_var_values()
    print("Solution:", solution)

    # Get the value of a specific variable
    x_value = master_problem.get_var_values(['x'])
    print("Value of x:", x_value['x'])

.. seealso::

    Refer to :ref:`manual_master_attributes` and :class:`API Reference <MasterProblem>`
    for more details on the attributes and methods of the master problem.

====

.. _manual_master_attributes:

Attributes & Methods
-------------------------------------------------

Below are the attributes and methods of the master problem class :class:`MasterProblem`.
It is inherited from the base class :class:`ProblemBase`, but tailored for master problems in Benders Decomposition.
:class:`ProblemBase` takes an instance that inherits from
:class:`SolverBase` as an argument to handle the underlying optimization solver.

.. mermaid::
    :caption: Master Problem Inheritance Diagram
    :align: center

    flowchart LR
        MasterProblem --inherits--> ProblemBase
        ProblemBase --uses--> SolverBase
    style SolverBase fill:#f2f2f2,stroke:#333,stroke-width:1px

.. rubric:: :class:`MasterProblem` - Attributes

.. autosummary::
   :nosignatures:

   ~MasterProblem.solver
   ~MasterProblem.model
   ~MasterProblem.status
   ~MasterProblem.params
   ~MasterProblem.complicating_vars
   ~MasterProblem.optimality_cuts
   ~MasterProblem.feasibility_cuts
   ~MasterProblem.cuts
   ~MasterProblem.estimators

.. tip::

    Use :attr:`MasterProblem.model` to access to more attributes.

.. rubric:: :class:`MasterProblem` - Methods

.. autosummary::
   :nosignatures:

   ~MasterProblem.add_cut
   ~MasterProblem.remove_cut
   ~MasterProblem.get_estimator_values
   ~MasterProblem.add_estimators
   ~MasterProblem.fix_vars
   ~MasterProblem.unfix_vars
   ~MasterProblem.get_var_values
   ~MasterProblem.get_var_coefs
   ~MasterProblem.get_rhs
   ~MasterProblem.get_dual_values
   ~MasterProblem.get_extreme_ray
   ~MasterProblem.get_obj
   ~MasterProblem.solve

Master Problem
===============================================

.. currentmodule:: benderslib

.. _manual_master_create:

Create a Master Problem
-----------------------------------------------

To create a master problem, you first need to build a ``model`` using one of the
:ref:`supported solvers <solver-table>`' official modeling APIs.
The solvers' official documentation provides detailed instructions on how to create models.
Then, you can create a :class:`MasterProblem` instance by passing the ``model``
wrapped with its corresponding :doc:`solver interface <../api/solver>` in BendersLib.

The Benders decomposition methods typically involve estimating the subproblem costs in the master problem.
These estimates are represented by special variables called **estimator variables** (:math:`\theta` or :math:`\eta`).
You do not need to define them manually in your model.
BendersLib automatically creates and manages these variables
after you instantiate a :doc:`Benders decomposition instance <../api/benders>`.

The code snippets below demonstrates how to create master problems using ``model`` objects of different solvers.
Make sure to :ref:`install the needed solver <solver-installation-table>` before running the code.

COPT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import coptpy
    from coptpy import COPT
    from benderslib import MasterProblem
    from benderslib.solvers import Copt

    # Create a COPT model
    env = coptpy.Envr()
    model = env.createModel("Master")
    x = model.addVar(name="x", vtype=COPT.INTEGER)
    z = model.addVar(name="z")
    model.addConstr(z <= x, name="c1")
    model.setObjective(x)

    # Create a MasterProblem
    master_problem = MasterProblem(Copt(model))
    print(master_problem)

CPLEX
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import cplex
    from benderslib import MasterProblem
    from benderslib.solvers import Cplex

    # Create a CPLEX model
    model = cplex.Cplex()
    model.variables.add(names=["x"], types=[model.variables.type.integer])
    model.variables.add(names=["z"])
    model.linear_constraints.add(lin_expr=[cplex.SparsePair(ind=["z", "x"], val=[1, -1])], senses=["L"], rhs=[0])
    model.objective.set_sense(model.objective.sense.minimize)
    model.objective.set_linear("x", 1)

    # Create a MasterProblem
    master_problem = MasterProblem(Cplex(model))
    print(master_problem)

Gurobi
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from gurobipy import Model, GRB
    from benderslib import MasterProblem
    from benderslib.solvers import Gurobi

    # Create a Gurobi model
    model = Model("Master")
    x = model.addVar(name="x", vtype=GRB.INTEGER)
    z = model.addVar(name="z")
    model.addConstr(z <= x, name="c1")
    model.setObjective(x)
    model.update()

    # Create a MasterProblem
    master_problem = MasterProblem(Gurobi(model))
    print(master_problem)

.. admonition:: Example
    :class: note

    :doc:`../examples/basic/classical_benders`

Pyomo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import pyomo.environ as pyo
    from benderslib import MasterProblem
    from benderslib.solvers import Pyomo

    # Create a Pyomo model
    model = pyo.ConcreteModel("Master")
    model.x = pyo.Var(domain=pyo.Integers, bounds=(0, 10))
    model.z = pyo.Var(bounds=(0, 10))
    model.c1 = pyo.Constraint(expr=model.z <= model.x)
    model.obj = pyo.Objective(expr=model.x)

    # Create a MasterProblem
    solver_name = 'gurobi_direct'  # Change to your preferred solver
    master_problem = MasterProblem(Pyomo(model, solver=solver_name))
    print(master_problem)

.. admonition:: Example
    :class: note

    Tested solver backends for :doc:`../examples/solvers/solver_pyomo`

SCIP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pyscipopt import Model
    from benderslib import MasterProblem
    from benderslib.solvers import Scip

    # Create a SCIP model
    model = Model("Master")
    x = model.addVar(vtype="I", name="x")
    z = model.addVar(vtype="C", name="z")
    model.addCons(z <= x)
    model.setObjective(x, "minimize")

    # Create a MasterProblem
    master_problem = MasterProblem(Scip(model))
    print(master_problem)

Above are all Mathematical Programming solvers.
Constraint Programming solvers currently are not supported to be used for master problems.
You can also refer to :doc:`../examples/solvers/index` for executable examples of using different solvers.

.. _manual_decompose:

Create a Master Problem from an Annotated Model
------------------------------------------------

Alternatively, you can create a master/sub problem by decomposing an existing model.
This is useful when you have a complete model and want to apply Benders decomposition.
The :class:`AnnotationBenders` class provides a static method :meth:`~AnnotationBenders.decompose`
that splits a model into a master problem and a subproblem based on a list of master variable names.
Refer to :meth:`~SolverBase.make_master_problem` and :meth:`~SolverBase.make_sub_problem` for the logic
of creating master and sub problems.
Here is an example of how to create a master/sub problem from an annotated model.

.. code-block:: python

    from gurobipy import Model, GRB
    from benderslib import MasterProblem, SubProblem, AnnotationBenders
    from benderslib.solvers import Gurobi

    # Create a model
    original_model = Model("Original")
    n_vars = 20
    y = original_model.addVars(n_vars, name="y", lb=1, ub=40, vtype=GRB.INTEGER)
    z = original_model.addVars(n_vars, name="z", lb=1, ub=40, vtype=GRB.CONTINUOUS)
    original_model.addConstr(y.sum() + z.sum() <= 50 * n_vars, "main_constr")
    original_model.setObjective(2 * y.sum() + 3 * z.sum(), sense=GRB.MINIMIZE)
    original_model.update()

    # Specify complicating variables
    complicating_vars = [v.VarName for v in y.values()]

    # Decompose the model
    master_model, sub_model = AnnotationBenders.decompose(
        original_model,
        Gurobi,
        master_vars=complicating_vars,
        solver_model=True  # Return solver models
        # solver_model=False  # (Default) Return MasterProblem/SubProblem instances
    )

    master_problem = MasterProblem(Gurobi(master_model))
    sub_problem = SubProblem(Gurobi(sub_model))

.. admonition:: Example
    :class: note

    :ref:`manual_decompose_solve`, :doc:`../examples/basic/annotation_benders`, :doc:`../examples/api/decompose`,
    :doc:`../examples/basic/cbd`

.. _manual_master_add_cut:

Add Benders Cuts to Master Problem
------------------------------------------------

The :class:`MasterProblem` class provides an :meth:`~MasterProblem.add_cut` method to add Benders cuts.
The method :meth:`~MasterProblem.add_cut` take an instance of the :class:`Cut` class or its
subclasses (:class:`OptimalityCut`, :class:`FeasibilityCut`, and :doc:`more <../api/cuts>`)
as an argument.

An optimality cut is added when the subproblem is feasible and provides a lower bound on the subproblem's cost.

.. code-block:: python

    from benderslib import ClassicalOC

    # Data for the cut
    complicating_vars = ['x', 'z']
    var_coefs = {'x': [1, 1], 'z': [1, 0]}
    dual_values = [0.5, 0.5]
    rhs = [14, 2]

    # Create an optimality cut
    optimality_cut = ClassicalOC(
        vars=complicating_vars,
        var_coefs=var_coefs,
        dual_values=dual_values,
        rhs=rhs,
        name="OptimalityCut"
    )

    # Add the cut to the master problem
    master_problem.add_cut(optimality_cut)


A feasibility cut is added when the subproblem is infeasible.
It cuts off the master problem solution that led to the infeasibility.

.. code-block:: python

    from benderslib import ClassicalFC

    # Data for the cut
    complicating_vars = ['x', 'z']
    var_coefs = {'x': [1, 1], 'z': [1, 0]}
    extreme_ray = [0.5, -0.5]
    rhs = [14, 2]

    # Create a feasibility cut
    feasibility_cut = ClassicalFC(
        vars=complicating_vars,
        var_coefs=var_coefs,
        extreme_ray=extreme_ray,
        rhs=rhs,
        name="FeasibilityCut"
    )

    # Add the cut to the master problem
    master_problem.add_cut(feasibility_cut)


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
        ctype=CST.OPTIMALITY,  # CST.FEASIBILITY
        name="MyCustomCut"
    )

    # Add the custom cut to the master problem
    master_problem.add_cut(custom_cut)

While the cut definition method described above is general and flexible, it is verbose.
For standard Benders cuts, refer to :doc:`../api/cuts` for more convenient ways to create cuts.

Access and Remove Cuts
------------------------------------------------

BendersLib provides attributes to access the cuts that have been added to the master problem and a method to remove them.
You can access all cuts, or filter them by type (optimality or feasibility), using the following attributes.

- :attr:`MasterProblem.cuts`: a dictionary mapping cut names to cut objects, containing all cuts.
- :attr:`MasterProblem.optimality_cuts`: a set of all optimality cut objects.
- :attr:`MasterProblem.feasibility_cuts`: a set of all feasibility cut objects.

.. code-block:: python

    # Assuming `master_problem` is an instance of MasterProblem with cuts added

    all_cuts = master_problem.cuts
    print(f"Total number of cuts: {len(all_cuts)}")

    optimality_cuts = master_problem.optimality_cuts
    print(f"Number of optimality cuts: {len(optimality_cuts)}")

    feasibility_cuts = master_problem.feasibility_cuts
    print(f"Number of feasibility cuts: {len(feasibility_cuts)}")


To remove a cut from the master problem, you can use the :meth:`MasterProblem.remove_cut` method.
This method takes a cut name as an argument and removes it from the master problem.

.. code-block:: python

    # Assuming `optimality_cut` is a cut that was previously added

    master_problem.remove_cut(optimality_cut.name)
    print(f"Cut '{optimality_cut.name}' removed.")
    print(f"Total number of cuts after removal: {len(master_problem.cuts)}")


Solve and Access Results
-------------------------------------------------

Once the master problem is defined, you can solve it and retrieve the results.
The :meth:`MasterProblem.solve` method is used to solve the current master problem relaxation.
After solving, you can check the status and objective value.

.. code-block:: python

    from benderslib import BendersConsts as CST

    master_problem.solve()

    if master_problem.status == CST.OPTIMAL:
        print("Master problem solved to optimality.")
        obj_val = master_problem.get_obj()
        print(f"Objective value: {obj_val}")


After a successful solve, you can retrieve the values of the variables, which will be used to build the subproblem,
using the :meth:`MasterProblem.get_var_values` method.

.. code-block:: python

    solution = master_problem.get_var_values()
    print("Solution:", solution)

    x_value = master_problem.get_var_values(['x'])
    print("Value of x:", x_value['x'])


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

    More attributes can be accessed via :attr:`~MasterProblem.model`, which is the underlying solver model instance.

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

Subproblem
============================================

.. currentmodule:: benderslib

.. _manual_sub_create:

Create a Subproblem
-------------------------------------------

To create a subproblem, you first need to define the problem using a :ref:`supported solver <solver-table>`.
Then, you can create a :class:`SubProblem` instance by passing a solver backend instance.
The code snippets below demonstrates how to create subproblems using model objects of different solvers.

.. note::

    * Make sure to :ref:`install the needed solver <solver-installation-table>` before running the code.
    * Refer to to :ref:`solver documentation <solver-table>` for more details on creating solver models.

.. attention::

    The complicating variables in the master problem **must** also appear in the subproblem with exactly the same names.
    This is crucial for the correct functioning.

Gurobi
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python
    :emphasize-lines: 12-

    from gurobipy import Model, GRB
    from benderslib import SubProblem, Gurobi

    # Create a Gurobi model for the subproblem
    sub_model = Model("Sub")
    y = sub_model.addVar(name="y", vtype=GRB.CONTINUOUS)
    x = sub_model.addVar(name="x") # complicating variable
    sub_model.addConstr(y >= x)
    sub_model.setObjective(2 * y)
    sub_model.update()

    # Create a SubProblem instance
    sub_problem = SubProblem(solver_backend=Gurobi(sub_model))
    # Or, simply
    # sub_problem = SubProblem(Gurobi(sub_model))

.. seealso::

    **Executable Example**: :doc:`../examples/classical_benders`

Creating subproblems is similar to creating master problems.
Please refer to :ref:`manual_master_create` for more examples **using other solvers**.

Create a Subproblem from an Annotated Model
-------------------------------------------

Please refer to :ref:`manual_decompose`.

Create Multiple Subproblems
-------------------------------------------

For stochastic programming problems with multiple scenarios, you can create a :class:`SubProblems` instance to manage them.
This class takes an iterable of :class:`SubProblem` instances and their corresponding probabilities (if not provided, equal probabilities are assumed).

.. code-block:: python
    :emphasize-lines: 19-

    from gurobipy import Model, GRB
    from benderslib import SubProblem, SubProblems, Gurobi

    # Assume we have two scenarios
    scenarios = [10, 20]
    probs = [0.4, 0.6]

    # Create a subproblem for each scenario
    sub_models = []
    for s in scenarios:
        sub_model = Model(f"Sub_{s}")
        y = sub_model.addVar(name="y", vtype=GRB.CONTINUOUS)
        x = sub_model.addVar(name="x") # complicating variable
        sub_model.addConstr(y >= x + s)
        sub_model.setObjective(2 * y)
        sub_model.update()
        sub_models.append(sub_model)

    # Create SubProblem instances
    sub_problem_instances = [SubProblem(Gurobi(m)) for m in sub_models]

    # Create a SubProblems instance
    sub_problems = SubProblems(sub_problem_instances, prob=probs)

.. seealso::

    **Executable Example**: :doc:`../examples/lshape`

Solve and Access Results
-------------------------------------------

.. rubric:: Solve the Problem

To solve the subproblem, use the :meth:`~SubProblem.solve` method.
This method returns the status of the solver.
Before solving, you can first fix the values of the complicating variables,
which are obtained from the master problem's solution, using the :meth:`~SubProblem.fix_vars` method.

.. code-block:: python

    master_solution = {'x': 5}
    sub_problem.fix_vars(master_solution)

    sub_problem.solve()

.. rubric:: Access Results

After solving, you can get the values of the decision variables, objective value, and information for Benders cuts.

.. code-block:: python

    # Access solution
    var_values = sub_problem.get_var_values(['y'])
    print(f"Variable values: {var_values}")

    # Access objective
    obj_val = sub_problem.get_obj()
    print(f"Objective value: {obj_val}")

    # For optimality cuts
    if sub_problem.status == 'OPTIMAL':
        dual_values = sub_problem.get_dual_values()
        print(f"Dual values: {dual_values}")

    # For feasibility cuts
    elif sub_problem.status == 'INFEASIBLE':
        extreme_ray = sub_problem.get_extreme_ray()
        print(f"Extreme ray: {extreme_ray}")

.. note::

    * The process is similar for a :class:`SubProblems` instance, which manages multiple subproblems.
      When you call methods like :meth:`~SubProblems.fix_vars`, :meth:`~SubProblems.solve`, :meth:`~SubProblems.get_var_values`, or :meth:`~SubProblems.get_obj`
      on a :class:`SubProblems` instance, the action is applied to all subproblems it contains.
      The results are aggregated (e.g., objective values are summed with probabilities).
    * To access information for each individual subproblem, you can iterate through the :attr:`~SubProblems.sub_problems` attribute.

.. seealso::

    Refer to :ref:`manual_sub_attributes` and :class:`API Reference <MasterProblem>`
    for more details on the attributes and methods of the subproblem(s).

====

.. _manual_custom_sub:

Customization
-------------------------------------------

Custom Subproblem Solver (class-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom Subproblem Solver (function-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Custom Subproblems
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

====

.. _manual_sub_attributes:

Attributes & Methods
-------------------------------------------

The class :class:`SubProblem` is inherited from the base class :class:`ProblemBase`,
but tailored for subproblems in Benders Decomposition.
:class:`ProblemBase` takes an instance that inherits from
:class:`SolverBase` as an argument to handle the underlying optimization solver.
For stochastic programming with multiple scenarios, the class :class:`SubProblems` manages multiple subproblem instances.

.. mermaid::
    :caption: Subproblem Inheritance Diagram
    :align: center

    flowchart LR
        SubProblem -- inherits --> ProblemBase
        ProblemBase -- uses --> SolverBase
        SubProblems -. contains .-> SubProblem
        SubProblems -. contains .-> LogicBasedSubProblem

    style SolverBase fill:#f2f2f2,stroke:#333,stroke-width:1px

*\*Note: Dashed arrows indicate optional relationships, from which exactly one must be selected for each usage.*

We also provide a :class:`LogicBasedSubProblem` template for custom subproblem,
especially for logic-based Benders Decomposition that do not rely on traditional optimization solvers.
Users can inherit from :class:`LogicBasedSubProblem` and implement the required abstract methods for custom subproblem logic.

Below are the attributes and methods :class:`SubProblem`, :class:`SubProblems`, and :class:`LogicBasedSubProblem`.

.. rubric:: :class:`SubProblem` - Attributes

.. autosummary::
   :nosignatures:

   ~SubProblem.model
   ~SubProblem._solver_model
   ~SubProblem.status
   ~SubProblem.params
   ~SubProblem.complicating_vars

.. tip::

    Use :attr:`SubProblem._solver_model` to access to more attributes.

.. rubric:: :class:`SubProblem` - Methods

.. autosummary::
   :nosignatures:

   ~SubProblem.add_vars
   ~SubProblem.get_obj_expr
   ~SubProblem.set_obj
   ~SubProblem.fix_vars
   ~SubProblem.unfix_vars
   ~SubProblem.get_var_values
   ~SubProblem.get_var_coefs
   ~SubProblem.get_rhs
   ~SubProblem.get_dual_values
   ~SubProblem.get_extreme_ray
   ~SubProblem.get_obj
   ~SubProblem.solve

.. rubric:: :class:`LogicBasedSubProblem` - Attributes

.. autosummary::
   :nosignatures:

   ~LogicBasedSubProblem.complicating_vars
   ~LogicBasedSubProblem.complicating_var_values
   ~LogicBasedSubProblem.obj
   ~LogicBasedSubProblem.var_values
   ~LogicBasedSubProblem.status
   ~LogicBasedSubProblem.params

.. rubric:: :class:`LogicBasedSubProblem` - Methods

.. autosummary::
   :nosignatures:

   ~LogicBasedSubProblem.solve
   ~LogicBasedSubProblem.fix_vars
   ~LogicBasedSubProblem.get_var_values
   ~LogicBasedSubProblem.get_obj

.. rubric:: :class:`SubProblems` - Attributes

.. autosummary::
   :nosignatures:

   ~SubProblems.sub_problems
   ~SubProblems.prob
   ~SubProblems.params
   ~SubProblems.status

.. rubric:: :class:`SubProblems` - Methods

.. autosummary::
   :nosignatures:

   ~SubProblems.solve
   ~SubProblems.fix_vars
   ~SubProblems.get_var_values
   ~SubProblems.get_obj

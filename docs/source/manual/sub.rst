Subproblem
============================================

.. currentmodule:: benderslib

.. _manual_sub_create:

Create a Subproblem
-------------------------------------------------

To create a master problem, you first need to build a ``model`` using one of the
:ref:`supported solvers <solver-table>`' official modeling APIs.
The solvers' official documentation provides detailed instructions on how to create models.
Then, you can create a :class:`SubProblem` instance by passing the ``model``
wrapped with its corresponding :doc:`solver interface <../api/solver>` in BendersLib.

The complicating variables in the master problem **must** also appear in the subproblem with exactly the same names.
This is crucial for the correct functioning.
Internally, BendersLib treats these variables as subproblem parameters,
which will be fixed to the values obtained from the master problem's solution during the Benders decomposition process.

The code snippets below demonstrates how to create master problems using ``model`` objects of different solvers.
Make sure to :ref:`install the needed solver <solver-installation-table>` before running the code.


COPT
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import coptpy
    from coptpy import COPT
    from benderslib import SubProblem
    from benderslib.solvers import Copt

    # Create a COPT model
    env = coptpy.Envr()
    sub_model = env.createModel("Sub")
    y = sub_model.addVar(name="y", vtype=COPT.CONTINUOUS)
    x = sub_model.addVar(name="x") # complicating variable
    sub_model.addConstr(y >= x)
    sub_model.setObjective(2 * y)

    # Create a SubProblem
    sub_problem = SubProblem(Copt(sub_model), complicating_vars=['x'])
    print(sub_problem)

CPLEX
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import cplex
    from benderslib import SubProblem
    from benderslib.solvers import Cplex

    # Create a CPLEX model
    sub_model = cplex.Cplex()
    sub_model.variables.add(names=["y"], types=[sub_model.variables.type.continuous])
    sub_model.variables.add(names=["x"]) # complicating variable
    sub_model.linear_constraints.add(
        lin_expr=[cplex.SparsePair(ind=["y", "x"], val=[1, -1])],
        senses=["G"],
        rhs=[0]
    )
    sub_model.objective.set_sense(sub_model.objective.sense.minimize)
    sub_model.objective.set_linear("y", 2)

    # Create a SubProblem
    sub_problem = SubProblem(Cplex(sub_model), complicating_vars=['x'])
    print(sub_problem)

Gurobi
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from gurobipy import Model, GRB
    from benderslib import SubProblem
    from benderslib.solvers import Gurobi

    # Create a Gurobi model
    sub_model = Model("Sub")
    y = sub_model.addVar(name="y", vtype=GRB.CONTINUOUS)
    x = sub_model.addVar(name="x") # complicating variable
    sub_model.addConstr(y >= x)
    sub_model.setObjective(2 * y)
    sub_model.update()

    # Create a SubProblem
    sub_problem = SubProblem(Gurobi(sub_model), complicating_vars=['x'])
    print(sub_problem)

.. admonition:: Example
    :class: note

    :doc:`../examples/basic/classical_benders`

Pyomo
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import pyomo.environ as pyo
    from benderslib import SubProblem
    from benderslib.solvers import Pyomo

    # Create a Pyomo model
    sub_model = pyo.ConcreteModel("Sub")
    sub_model.y = pyo.Var(domain=pyo.NonNegativeReals)
    sub_model.x = pyo.Var(domain=pyo.NonNegativeReals) # complicating variable
    sub_model.c = pyo.Constraint(expr=sub_model.y >= sub_model.x)
    sub_model.obj = pyo.Objective(expr=2 * sub_model.y)

    # Create a SubProblem
    solver_name = 'gurobi_direct'  # Change to your preferred solver
    sub_problem = SubProblem(Pyomo(sub_model, solver=solver_name), complicating_vars=['x'])
    print(sub_problem)

.. admonition:: Example
    :class: note

    Tested solver backends for :doc:`../examples/solvers/solver_pyomo`

SCIP
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from pyscipopt import Model
    from benderslib import SubProblem
    from benderslib.solvers import Scip

    # Create a SCIP model
    sub_model = Model("Sub")
    y = sub_model.addVar(vtype="C", name="y")
    x = sub_model.addVar(name="x") # complicating variable
    sub_model.addCons(y >= x)
    sub_model.setObjective(2 * y, "minimize")

    # Create a SubProblem
    sub_problem = SubProblem(Scip(sub_model), complicating_vars=['x'])
    print(sub_problem)

Above are Mathematical Programming solvers.
In addition, BendersLib also supports Constraint Programming solvers for subproblems.
This feature is useful for :doc:`../tutorials/cbd` and :doc:`../tutorials/lbbd`
that involve combinatorial subproblems.
Below are code snippets using :class:`~solvers.Ortools` and :class:`~solvers.CplexCP` as subproblem solvers.

OR-Tools (Constraint Programming)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from ortools.sat.python import cp_model
    from benderslib.solvers import Ortools
    from benderslib import SubProblem

    # Create an Ortools model
    model = cp_model.CpModel()
    y = model.NewIntVar(0, 10, 'y')
    x = model.NewIntVar(0, 10, 'x') # complicating variable
    model.Add(y >= x)
    model.Minimize(2 * y)

    vars_map = {'x': x, 'y': y}

    # Create a SubProblem
    sub_problem = SubProblem(Ortools(model, vars_map=vars_map), complicating_vars=['x'])
    print(sub_problem)

Cplex (Constraint Programming)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from benderslib import SubProblem
    from benderslib.solvers import CplexCP
    from docplex.cp.model import CpoModel

    # Create a CplexCP model
    model = CpoModel()
    y = model.integer_var(0, 10, 'y')
    x = model.integer_var(0, 10, 'x')  # complicating variable
    model.add(y >= x)
    model.minimize(2 * y)

    vars_map = {'x': x, 'y': y}

    # Create a SubProblem
    sub_problem = SubProblem(CplexCP(model, vars_map=vars_map), complicating_vars=['x'])
    print(sub_problem)

Please refer to :doc:`../examples/solvers/index` for executable examples of using different solvers.

Create a Subproblem from an Annotated Model
-------------------------------------------------

Please refer to :ref:`manual_decompose`.

Compute Irreducible Infeasible Subsystem (IIS)
-------------------------------------------------

In :doc:`../tutorials/cbd` and :doc:`../tutorials/lbbd`,
the feasibility cut is not derived from dual but is instead formulated based on the IIS of the subproblem.
This makes the ability to compute an IIS a key feature for these methods.
BendersLib provides a unified interface to compute the IIS for subproblems, regardless of the underlying solver.
You can use the :meth:`~SubProblem.compute_iis` method, which will invoke the solver's IIS computation capabilities.
Not all solvers support IIS computation, refer to the :ref:`solver-table` for details.

.. code-block:: python

    # Assuming sub_problem is an infeasible SubProblem instance
    iis_vars = sub_problem.compute_iis()
    print(f"IIS consists of: {iis_vars}")

This method returns a set of variable names that are part of the IIS.

.. admonition:: Example
    :class: note

    :doc:`../examples/iis/index`, :doc:`../examples/advanced/cbd_iis`, :doc:`../examples/advanced/ilshaped_iis`


Create Multiple Subproblems
-------------------------------------------------

For stochastic programming problems with multiple scenarios, you can create a :class:`SubProblems` instance to manage them.
This class takes an iterable of :class:`SubProblem` instances and their corresponding probabilities (if not provided, equal probabilities are assumed).

.. code-block:: python

    from gurobipy import Model, GRB
    from benderslib import SubProblem, SubProblems
    from benderslib.solvers import Gurobi

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

    # Create a SubProblems instance with a list of SubProblem instances
    sub_problem_instances = [SubProblem(Gurobi(m)) for m in sub_models]
    sub_problems = SubProblems(sub_problem_instances, prob=probs)

.. admonition:: Example
    :class: note

    :doc:`../examples/basic/lshaped`, :doc:`../examples/advanced/lbbd_lshaped`

Solve and Access Results
-------------------------------------------------

Before solving, you can first fix the values of the complicating variables,
which are obtained from the master problem's solution, using the :meth:`SubProblem.fix_vars` method.
To solve the subproblem, use the :meth:`SubProblem.solve` method.

.. code-block:: python

    master_solution = {'x': 5}
    sub_problem.fix_vars(master_solution)

    sub_problem.solve()

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

The process is similar for a :class:`SubProblems` instance, which manages multiple subproblems.
When you call methods like :meth:`~SubProblems.fix_vars`, :meth:`~SubProblems.solve`, :meth:`~SubProblems.get_var_values`, or :meth:`~SubProblems.get_obj`
on a :class:`SubProblems` instance, the action is applied to all subproblems it contains.
The results are aggregated (e.g., objective values are summed with probabilities).
To access information for each individual subproblem, you can iterate through the :attr:`~SubProblems.sub_problems` attribute.

====

.. _manual_custom_sub:

Customization
-------------------------------------------------

For certain problems, especially :doc:`../tutorials/lbbd`,
the subproblem may not be a standard optimization model that can be handled by a conventional solver.
Instead, it might be solved by a combinatorial algorithm, a heuristic, or some other custom logic.
BendersLib provides a flexible way to handle such cases through custom subproblem implementations.

Custom Subproblem (class-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can create a custom subproblem solver by defining a class that inherits from the abstract base class :class:`LogicBasedSubProblem`.
You must implement the :meth:`LogicBasedSubProblem.solve` method, where you define the logic for solving the subproblem.
Inside this method, you should update the attributes ``status``, ``obj``, and ``var_values``.

- :attr:`~LogicBasedSubProblem.status`: :attr:`BendersConsts.OPTIMAL` or :attr:`BendersConsts.INFEASIBLE`.
- :attr:`~LogicBasedSubProblem.obj`: The objective value of the subproblem solution.
- :attr:`~LogicBasedSubProblem.var_values`: A dictionary mapping variable names to their values in the subproblem solution.

When doing so, you can assume that the values of the complicating variables from the master problem
are available in the :attr:`~LogicBasedSubProblem.complicating_var_values` attribute.

.. code-block:: python

    from benderslib import LogicBasedSubProblem, CST

    class MyCustomSubproblem(LogicBasedSubProblem):
        def solve(self):
            # Access master variables' values
            x_val = self.complicating_var_values['x']

            # Implement your custom solving logic here
            # and set the status, obj, and var_values attributes
            if x_val > 5:
                self.status = CST.INFEASIBLE
                self.obj = None
                self.var_values = {}
            else:
                self.status = CST.OPTIMAL
                self.obj = 10 - x_val
                self.var_values = {'y': 2 * x_val}

    custom_subproblem = MyCustomSubproblem(complicating_vars=['x'])

Custom Subproblem (function-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For simpler, stateless subproblems, you can define a function instead of a class.
The function must accept a dictionary of the complicating variables' values and return
a tuple containing the attributes ``status``, ``obj``, and ``var_values``.
This function can be passed directly to :class:`LogicBasedBenders` as a subproblem.

.. code-block:: python

    from benderslib import CST

    def subproblem_solver(master_vars: dict[str, float]) -> tuple[str, float, dict[str, float]]:
        # Access master variables' values
        x_val = master_vars['x']

        # Implement your custom solving logic here
        if x_val > 5:
            status = CST.INFEASIBLE
            obj = None
            var_values = {}
        else:
            status = CST.OPTIMAL
            obj = 10 - x_val
            var_values = {'y': 2 * x_val}

        # Return status, objective value, and variable values (as a dict)
        return status, obj, var_values


Using a function is convenient for simple cases.
However, for more complex subproblems that require maintaining state across iterations (e.g., caching results),
a class-based approach is recommended.

.. admonition:: Example
    :class: note

    - See :doc:`../examples/applications/lbbd_location` for how to implement a custom subproblem solver
      with a function, using logic-based Benders decomposition.

Multiple Custom Subproblems (class-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When your problem involves multiple scenarios that are solved with custom logic (e.g., stochastic programming with a combinatorial subproblem), you can manage them using the :class:`SubProblems` class.
Simply create instances of your custom subproblem class for each scenario and pass them to :class:`SubProblems`.

.. code-block:: python

    from benderslib import SubProblems, LogicBasedSubProblem, CST

    class MyScenarioSubproblem(LogicBasedSubProblem):
        def __init__(self, complicating_vars, scenario_data):
            super().__init__(complicating_vars)
            self.scenario_data = scenario_data

        def solve(self):
            # Access master variables' values
            x_val = self.complicating_var_values['x']

            # Use ``self.scenario_data`` in the solving logic
            if x_val > self.scenario_data:
                self.status = CST.INFEASIBLE
                self.obj = None
                self.var_values = {}
            else:
                self.status = CST.OPTIMAL
                self.obj = self.scenario_data - x_val
                self.var_values = {'y': 2 * x_val}

    scenarios = [1, 2, 3]
    probs = [0.3, 0.4, 0.3]
    subproblem_instances = [MyScenarioSubproblem(['x'], s) for s in scenarios]
    sub_problems = SubProblems(subproblem_instances, prob=probs)

.. admonition:: Example
    :class: note

    See :doc:`../examples/advanced/lbbd_lshaped` for how to implement the L-shaped method,
    which involves multiple subproblems, using logic-based Benders decomposition with custom subproblem classes.

Multiple Custom Subproblems (function-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, BendersLib does not support function-based custom subproblems.
But you can define the logic of solving multiple subproblems within a function,
then using that function as a subproblem in a Benders decomposition algorithm.

.. admonition:: Example
    :class: note

    See :doc:`../examples/advanced/lbbd_sp` for how to solve multiple subproblems
    with a function, using logic-based Benders decomposition.

====

.. _manual_sub_attributes:

Attributes & Methods
-------------------------------------------------

The class :class:`SubProblem` is inherited from the base class :class:`ProblemBase`,
but tailored for subproblems in Benders Decomposition.
:class:`ProblemBase` takes an instance that inherits from
:class:`SolverBase` or :class:`SolverCPBase` as an argument to handle the underlying optimization solver.
For stochastic programming with multiple scenarios, the class :class:`SubProblems` manages multiple subproblem instances.

We also provide a :class:`LogicBasedSubProblem` template for custom subproblem,
especially for :doc:`../tutorials/lbbd` that do not rely on traditional optimization solvers.
Users can inherit from :class:`LogicBasedSubProblem` and implement the required abstract methods for custom subproblem logic.

.. mermaid::
    :caption: Subproblem Inheritance Diagram
    :align: center

    flowchart LR
        SubProblem -- inherits --> ProblemBase
        ProblemBase -. uses .-> SolverBase
        ProblemBase -. uses .-> SolverCPBase
        SubProblems -. contains .-> SubProblem
        SubProblems -. contains .-> LogicBasedSubProblem

    style SolverBase fill:#f2f2f2,stroke:#333,stroke-width:1px
    style SolverCPBase fill:#f2f2f2,stroke:#333,stroke-width:1px

*\*Note: Dashed arrows indicate optional relationships, from which exactly one must be selected for each usage.*

Below are the attributes and methods :class:`SubProblem`, :class:`SubProblems`, and :class:`LogicBasedSubProblem`.

.. rubric:: :class:`SubProblem` - Attributes

.. autosummary::
   :nosignatures:

   ~SubProblem.solver
   ~SubProblem.model
   ~SubProblem.status
   ~SubProblem.params
   ~SubProblem.complicating_vars

.. tip::

    More attributes can be accessed via :attr:`~SubProblem.model`, which is the underlying solver model instance.

.. rubric:: :class:`SubProblem` - Methods

.. autosummary::
   :nosignatures:

   ~SubProblem.add_estimators
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

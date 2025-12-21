How-To Guides
=============================================================

.. currentmodule:: benderslib

*To be added (common issues will be summarized here)...*

How to access to attributes not listed in the API reference?
--------------------------------------------------------------

Sometimes, users may want to access to certain attributes of the underlying solver model
that are not directly exposed in the BendersLib API reference.
In such cases, users can utilize the attribute :attr:`ProblemBase._solver_model`
(the base class for :class:`MasterProblem` and :class:`SubProblem`)
to access the underlying solver model directly.

For example, if you are using :class:`Gurobi`, you can access the Gurobi model as follows.

.. code-block:: python

    from benderslib import Gurobi, AnnotationBenders, ClassicalBenders
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

    # Access the underlying Gurobi model
    gurobi_model = benders.master_problem._solver_model
    print(f"Gurobi Model Status: {gurobi_model.Status}")

.. seealso::

    Refer to the :ref:`documentation of the specific solver <solver-table>` for more available attributes.
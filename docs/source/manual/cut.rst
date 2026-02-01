Benders Cut
============================================

.. currentmodule:: benderslib

Cut
-------------------------------------------

.. important::

   BendersLib currently supports only **linear** Benders cuts.

A linear Benders cut is a linear inequality (constraint) added to the master problem.
This cut is generated to approximate the subproblem's value function or exclude infeasible solutions.
In BendersLib, all linear Benders cuts are implemented using the :class:`Cut` class,
which holds all the information needed to define a linear cut, which is a linear inequality of the
following form.

.. math::

   \mathbf{c}^{\top} \mathbf{x} \le d

In the above inequality,
:math:`\mathbf{x}` represents the vector of variables (``vars``) involved in the cut,
:math:`\mathbf{c}` represents the vector of corresponding coefficients (``coefs``),
and :math:`d` is the right-hand side value (``rhs``).
The sense of the inequality can be less than or equal to (``'<='``), greater than or equal to (``'>='``), or equal to (``'=='``).
Correspondingly, the :class:`Cut` class includes attributes to store these components.

- ``vars``: A list of variables involved in the cut.
- ``coefs``: The coefficients corresponding to the variables.
- ``rhs``: The right-hand side value of the inequality.
- ``sense``: The sense of the inequality (e.g., ``'<='``, ``'>='``, or ``'=='``).

Here is an example of how to create a :class:`Cut` instance.

.. code-block:: python

    from benderslib import Cut, CST

    # Create a cut: 2*x1 + 3*x2 <= 10
    my_cut = Cut(
        vars=['x1', 'x2'],
        coefs=[2, 3],
        rhs=10,
        sense=CST.LE,  # or '<='
        ctype=CST.OPTIMALITY, # or CST.FEASIBILITY
        name="my_custom_cut"
    )

**Any** linear Benders cut can be represented using an instance of the :class:`Cut` class.
The built-in cut types listed below are essentially
:abbr:`syntactic sugar (syntax that provides a simpler, more convenient, or more readable way to write code for a common operation, without adding new functionality)` of :class:`Cut`,
providing convenient ways to define standard Benders cuts.

.. rubric:: Built-in Benders Cuts

.. autosummary::
   :nosignatures:

   ~ClassicalOC
   ~ClassicalFC
   ~CombinatorialOC
   ~NoGoodFC
   ~LShapedOC
   ~GeneralizedOC
   ~GeneralizedFC
   ~GeneLShapedOC

*\* Note: "OC" stands for Optimality Cut, and "FC" stands for Feasibility Cut.*

.. seealso::

    - For details on how to define these cuts, please refer to the :doc:`API reference <../api/cut>`.
    - :ref:`manual_master_add_cut`

Cut Generator
-------------------------------------------

In BendersLib, the generation of Benders cuts is managed by the :class:`CutGenerator` class.
While a :class:`Cut` instance simply holds the data for a linear inequality,
the :class:`CutGenerator` contains the logic for creating that data.
It acts as a factory for :class:`Cut` objects,
using information from the master problem and subproblem(s) to construct the appropriate cuts at each iteration of the Benders decomposition algorithm.
The key design aspects of the :class:`CutGenerator` are as follows.

- **Separation of Concerns**:
  It separates the cut generation logic from the cut data structure.
  The :class:`Cut` is a simple data container, while the :class:`CutGenerator` is
  responsible for the complex logic of calculating coefficients and right-hand side values.

- **Efficiency**:
  A ``CutGenerator`` instance is initialized only **once** when the :class:`BendersSolver` is instantiated.
  This allows the generator to pre-process and cache any information that remains constant throughout the solving process,
  such as the subproblem's constraint matrix structure.
  This avoids redundant computations at each iteration, significantly improving performance.
  For example, :class:`ClassicalOCGen` retrieves the subproblem's variable coefficients and right-hand side values in its constructor.

- **Statefulness**:
  Since the same ``CutGenerator`` instance is used across all iterations, it can maintain state.
  This is crucial for advanced strategies like cut strengthening, stabilization techniques,
  or other acceleration methods that require information aggregated over multiple iterations.

- **Lifecycle**:
  The ``CutGenerator`` is instantiated within the ``__init__`` method of a :class:`BendersSolver` subclass (e.g., :class:`ClassicalBenders`).
  During the :meth:`ClassicalBenders.solve()` loop of the solver,
  its :meth:`CutGenerator.generate()` method is called whenever a new cut is needed.
  The ``generate()`` method then accesses the most recent solutions from the master and subproblems
  to create and return a list of :class:`Cut` instances (or :class:`FeasibilityCut` / :class:`OptimalityCut` instances).

Here is an example of how cut generators :class:`ClassicalOCGen` and :class:`ClassicalFCGen` are
passed to the :class:`ClassicalBenders` solver.

.. code-block:: python
   :emphasize-lines: 10-11

    from benderslib import ClassicalBenders, ClassicalOCGen, ClassicalFCGen, MasterProblem, SubProblem

    # Assume master_problem, sub_problem, and complicating_vars are defined
    master_problem: MasterProblem = ...
    sub_problem: SubProblem = ...
    complicating_vars: list[str] = ...

    solver = ClassicalBenders(
        master_problem, sub_problem, complicating_vars,
        optimality_cut=ClassicalOCGen,
        feasibility_cut=ClassicalFCGen
    )
    solver.solve()

.. note::

    The class passed to the solver (e.g., ``ClassicalOCGen``) is **not** instantiated at this point.
    Instead, the BendersLib will instantiate it internally during its own initialization.

.. rubric:: Built-in Cut Generators

The classes listed below are all subclasses of :class:`CutGenerator`.
Each one implements a specific logic for generating cuts by overriding the :meth:`CutGenerator.generate` method.
Here are a couple of examples to illustrate how they work.

.. admonition:: Example: ClassicalOCGen

   The :class:`ClassicalOCGen` generates an optimality cut using the dual values from the subproblem.

   .. code-block:: python

       # Inside ClassicalOCGen
       def generate(self) -> list[ClassicalOC]:
           dual_values = self.sub_problem.get_dual_values()

           cut = ClassicalOC(self.complicating_vars, self.var_coefs, dual_values, self.rhs)
           return [cut]

   - ``self.complicating_vars``, ``self.var_coefs``, and ``self.rhs`` are attributes cached at initialization for efficiency.
   - The ``dual_values`` are retrieved from the subproblem at each iteration, as they depend on the master problem's solution.

.. admonition:: Example: CombinatorialFCGen

   The :class:`CombinatorialFCGen` generates a no-good cut based on the values of the binary complicating variables from the master problem.

   .. code-block:: python

       # Inside CombinatorialFCGen
       def generate(self) -> list[NoGoodFC]:
           var_values = self.master_problem.get_var_values(self.complicating_vars)

           cut = NoGoodFC(var_values)
           return [cut]

.. autosummary::
   :nosignatures:

   ~ClassicalOCGen
   ~ClassicalFCGen
   ~CombinatorialOCGen
   ~CombinatorialFCGen
   ~LShapedOCGen
   ~LShapedFCGen
   ~IntegerLShapedOCGen
   ~IntegerLShapedFCGen
   ~GeneralizedOCGen
   ~GeneralizedFCGen
   ~GeneLShapedOCGen

*\* Note: "OC" stands for Optimality Cut, and "FC" stands for Feasibility Cut.*

.. caution::

   These classes are tailored for their respective Benders decomposition variants.
   Use them with caution in your own custom Benders decomposition unless you are certain that your implementation matches one of these variants.

====

.. _manual_custom_cut:

Customization
-------------------------------------------

BendersLib is designed to be highly customizable, allowing you to define your own Benders cuts and the logic for generating them.
This is particularly useful when implementing advanced non-standard Benders decomposition schemes.

Custom Benders Cut
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

While BendersLib's built-in cut types are convenient,
you can create your own custom cut class for clarity or to encapsulate specific logic.
A custom cut class should inherit from :class:`OptimalityCut` or :class:`FeasibilityCut`.
The primary purpose of a custom cut class is to structure the data required for a cut
in a way that is meaningful to your specific problem.
The base classes handle the core attributes (``vars``, ``coefs``, ``rhs``, ``sense``),
so your custom class can focus on providing a user-friendly ``__init__`` method.

.. admonition:: Example: NoGoodFC

   Here is an example of BendersLib's built-in :class:`NoGoodFC` cut,
   which excludes a specific binary solution from the master problem.

   .. code-block:: python

        from benderslib import FeasibilityCut, CST

        class NoGoodFC(FeasibilityCut):

            def __init__(self, bin_var_values: dict):
                # Retrieve variable values required for the cut
                var_zeros = [var for var, val in bin_var_values.items() if val <= 0.5]
                var_ones = [var for var, val in bin_var_values.items() if val > 0.5]

                vars = var_ones + var_zeros
                coefs = [1.0] * len(var_ones) + [-1.0] * len(var_zeros)
                rhs = len(var_ones) - 1

                # Call the parent constructor
                super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='<=', name="NoGoodFC")

.. seealso::

    See :doc:`API Reference <../api/cut>` for BendersLib's built-in cut types.

Custom Cut Generator (class-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The core of customization lies in creating a custom cut generator,
especially when implementing advanced decomposition schemes like
:doc:`../tutorials/lbbd` that require **non-standard cuts**.
This requires obtaining the necessary information from the master and subproblems
and computing the cut's coefficients and right-hand side according to your specific logic.
A class-based generator is the standard and most flexible approach in BendersLib.

To create and use one class-based cut generator, follow these steps.

- **Step 1**.  Define a class that inherits from :class:`CutGenerator`.

- **Step 2**.  Implement the ``__init__`` method to receive the master problem, subproblem(s), and parameters.
  This is the ideal place to cache data that does not change between iterations.

- **Step 3**.  Implement the :meth:`CutGenerator.generate` method.
  This method is called in each iteration of the Benders algorithm and must return a list of one or more cut objects.

- **Step 4**.  Pass the custom cut generator class (not an instance) to the Benders solver when instantiating it.

.. admonition:: Example: Class-based Cut Generator

   Here is an example of a custom cut generator that creates the ``NoGoodFC`` instances defined earlier.

   .. code-block:: python

       from benderslib import CutGenerator, BendersSolver, Cut

       # Step 1: Define the custom cut generator class
       class MyCutGen(CutGenerator):

           def __init__(self, master_problem, sub_problem, params):
               # Step 2: Initialization and caching
               # No data needs to be cached for this simple generator.
               # The __init__ can be left empty if no pre-processing is needed.
               super().__init__(master_problem, sub_problem, params)

           def generate(self) -> list[NoGoodFC]:
               # Step 3: Generate the cuts
               # Retrieve the values of the complicating variables from the master problem.
               # Create the custom cut
               infeasible_solution = self.master_problem.get_var_values(self.complicating_vars)
               cut = NoGoodFC(infeasible_solution)
               # cut = Cut(...)  # Alternatively, create a Cut instance directly.
               return [cut]  # Return a list of cuts, even if it's just one.

       # Step 4: Use the custom cut generator in the Benders solver
       solver = BendersSolver(
           master_problem,
           sub_problem,
           complicating_vars,
           feasibility_cut=MyCutGen,  # Pass the custom cut generator class
       )
       solver.solve()

.. seealso::

    See :doc:`API Reference <../api/benders>` for BendersLib's built-in cut generators.

Custom Cut Generator (function-based)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For simpler cases, you may not need a full class for your cut generation logic.
BendersLib also supports using a simple function as a cut generator.
This can make the code more concise if you don't need to cache data or maintain state between iterations.

A generator function must accept three arguments: ``master_problem``, ``sub_problem``, and ``complicating_vars``.
It should return a list of one or more cut objects.

.. admonition:: Example: Function-based Cut Generator

   Here is an example of a function-based generator for a no-good feasibility cut.
   It is equivalent to the earlier class-based example but implemented with a simple function.

   .. code-block:: python

       from benderslib import Cut, CST, BendersSolver

       def simple_fc_generator(master_problem, sub_problem, complicating_vars) -> list[Cut]:
           # Retrieve the values of the complicating variables from the master problem.
           bin_var_values = master_problem.get_var_values(complicating_vars)

           # Create the cut using NoGoodFC
           cut = NoGoodFC(bin_var_values)
           return [cut]

       # To use it, simply pass the function to the solver.
       solver = BendersSolver(
           master_problem,
           sub_problem,
           complicating_vars,
           feasibility_cut=simple_fc_generator,  # Pass the custom cut generator function
       )
       solver.solve()

.. seealso::

    - **Executable Examples**: :doc:`../examples/ilshape_iis`, :doc:`../examples/lbbd`, :doc:`../examples/lbbd_location`.

====

Attributes & Methods
-------------------------------------------

Let ``BendersCut`` and ``BendersCutGen`` be generic names for Benders cut classes (e.g., :class:`ClassicalOC`)
and cut generator classes (e.g., :class:`ClassicalOCGen`), respectively.
The diagram below illustrates the inheritance and usage relationships among the relevant classes.
Any ``BendersCut`` inherits from :class:`Cut`, :class:`OptimalityCut`, or :class:`FeasibilityCut`,
and is generated by a ``BendersCutGen`` that inherits from :class:`CutGenerator`.
The ``BendersCutGen`` uses information from :class:`SubProblem` (or :class:`SubProblems`, :class:`LogicBasedSubProblem`)
and :class:`MasterProblem` instances to generate the cuts,
and the generated ``BendersCut`` is added to the :class:`MasterProblem`.

.. mermaid::
    :caption: Cut and Cut Generator Inheritance Diagram
    :align: center

    flowchart LR
        BendersCutGen -- generates --> BendersCut
        BendersCutGen -- inherits --> CutGenerator

        BendersCut -- is added to --> MasterProblem
        OptimalityCut -- inherits --> Cut
        FeasibilityCut -- inherits --> Cut
        BendersCut -. inherits .-> OptimalityCut
        BendersCut -. inherits .-> FeasibilityCut
        BendersCut -. inherits .-> Cut

        BendersCutGen -- uses --> SubProblem
        BendersCutGen -- uses --> MasterProblem

    style MasterProblem fill:#f2f2f2,stroke:#333,stroke-width:1px
    style SubProblem fill:#f2f2f2,stroke:#333,stroke-width:1px
    style BendersCutGen fill:white,stroke:#333,stroke-width:1px
    style BendersCut fill:white,stroke:#333,stroke-width:1px

*\*Note: Dashed arrows indicate optional relationships, from which exactly one must be selected for each usage.*

Below are the attributes and methods of the :class:`Cut` and :class:`CutGenerator` classes.
:class:`OptimalityCut` and :class:`FeasibilityCut` inherit from :class:`Cut`, and share the same attributes and methods.
Please refer to :doc:`Benders Cuts <../api/cut>` and :doc:`Cut Generators <../api/benders>`
for the attributes and methods of specific implementations.

.. rubric:: :class:`Cut` - Attributes

.. autosummary::
   :nosignatures:

   ~Cut.vars
   ~Cut.coefs
   ~Cut.rhs
   ~Cut.sense
   ~Cut.ctype
   ~Cut.name

.. rubric:: :class:`Cut` - Methods

There is no public method.

.. rubric:: :class:`CutGenerator` - Attributes

.. autosummary::
   :nosignatures:

   ~CutGenerator.master_problem
   ~CutGenerator.sub_problem
   ~CutGenerator.complicating_vars
   ~CutGenerator.params

.. rubric:: :class:`CutGenerator` - Methods

.. autosummary::
   :nosignatures:

   ~CutGenerator.generate

Contributor Guide
==================================================

.. currentmodule:: benderslib

.. important::

   If you have a new feature in mind or have found a bug,
   please `open an issue <https://github.com/phguo/BendersLib/issues>`_
   to discuss it before you start working on it.
   This helps ensure that your contribution aligns with the project's goals and avoids duplicate work.

Development Workflow
--------------------------------------------------

This project uses the
`Gitflow workflow <https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow>`_
(or `git-flow <https://nvie.com/posts/a-successful-git-branching-model/>`_, not decided yet)
for development. If you'd like to contribute, please follow these steps.

The primary branches are as follows.

- ``main``: Contains the latest stable release. Direct commits to this branch are not allowed.

- ``develop``: The active development branch. All feature branches are based on this branch.

1. **Fork the Repository**

   Start by forking the `BendersLib repository on GitHub <https://github.com/phguo/BendersLib>`_
   to your personal account.

2. **Clone Your Fork**

   Clone your forked repository to your local machine.

   .. code-block:: bash

      git clone https://github.com/phguo/BendersLib.git
      cd BendersLib

3. **Create a Feature Branch**

   Create a new branch for your feature or bugfix. Base your branch on the ``develop`` branch.

   .. code-block:: bash

      git checkout develop
      git pull origin develop
      git checkout -b feature/your-feature-name

4. **Make and Commit Changes**

   Make your changes to the codebase. Commit your changes with a descriptive message.
   Refer to `conventional commit messages <https://www.conventionalcommits.org/en/v1.0.0/>`_ for guidance.

   .. code-block:: bash

      git commit -am "feat: Add some feature"

5. **Push to Your Fork**

   Push your changes to your forked repository on GitHub.

   .. code-block:: bash

      git push origin feature/your-feature-name

6. **Submit a Pull Request**

   Open a pull request from your feature branch to the ``develop`` branch of the main BendersLib repository.
   In the pull request description, please explain the changes you have made and why.

Guidelines
--------------------------------------------------

Contributing a Solver Interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To add a new solver interface to BendersLib,
you need to create a new class that inherits from the :class:`SolverBase` abstract base class.
This new class will serve as a wrapper for the specific solver's Python API,
translating BendersLib's calls into the solver's specific methods and data structures.
The existing solver interfaces (e.g., :class:`~.solvers.Gurobi`) can serve as references for how to implement your own.
The :class:`SolverBase` class is located in ``benderslib/solver/base.py``.
Your new solver interface should be a new file in the ``benderslib/solver/`` directory,
for example ``benderslib/solver/new_solver.py``.

Contributing a Benders Method Implementation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Contributing a Benders method implementation to BendersLib involves creating a new class that inherits from
the :class:`BendersSolver` base class. This approach allows you to define a new Benders decomposition variant
by specifying the types of cuts it uses.
The :class:`BendersSolver` class is located in ``benderslib/core.py``.
Your new Benders method should be a new class in a relevant file, for example, in ``benderslib/benders.py``.

The core of a Benders method is the logic for generating optimality and feasibility cuts.
If your method uses novel cut formulations, you will need to implement new cut generators (and possibly cut types).
Cut generators are classes that inherit from :class:`CutGenerator` and implement the :meth:`~CutGenerator.generate` method.
The existing cut generators (e.g., ones in ``benderslib/cut.py``) can serve as references for how to implement your own.

If necessary, you may also define new cut types by creating classes that inherit from :class:`Cut`,
or inherit from :class:`OptimalityCut` or :class:`FeasibilityCut` for more specific cut types.
The existing cut types (e.g., ones in ``benderslib/cut.py``) can serve as references.

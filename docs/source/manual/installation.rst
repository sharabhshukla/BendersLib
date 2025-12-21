Installation
====================================

.. currentmodule:: benderslib

Installing BendersLib
------------------------------------

.. tip::

   If you are new to Python, we recommend using `conda <https://docs.conda.io/projects/conda/en/stable/user-guide/install/index.html>`_
   as your package and environment manager.
   By default, conda will install ``pip`` in the created environments, so you can use either ``pip`` or ``conda``
   to install BendersLib (and other packages).

BendersLib was written in pure Python, you can easily install it via ``pip`` or ``conda``.

Environment Setup (optional)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To avoid potential dependency conflicts, it is recommended to create a new ``conda`` environment
for BendersLib before installing it.

.. code-block:: bash

    # Create a new conda environment named "bendersenv" with Python 3.9 or higher
    conda create -n bendersenv python=3.9

    # Activate the new environment
    conda activate bendersenv

Installing via ``pip``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pip install benderslib

    # Upgrade to the latest version
    # pip install --upgrade benderslib

Installing via ``conda``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    conda install -c conda-forge benderslib

    # Upgrade to the latest version
    # conda update -c conda-forge benderslib

Verifying the Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To verify that BendersLib has been installed correctly, you can run the following code:

.. code-block:: python

    import benderslib as bd

    print("BendersLib version:", bd.__version__)

If you see the version number printed without any errors, the installation was successful.

Dependencies
------------------------------------

BendersLib requires ``Python>=3.9`` and the following dependencies to run.

* `NumPy <https://numpy.org/>`_ (>=1.20): Package for vectorized numerical computations.

A full list of dependencies can be found in the ``pyproject.toml`` file of the source code.
During the installation, these dependencies will be installed automatically if they are not already present
in your environment.
Mathematical optimization solvers are **NOT** included in the dependencies,
and will not be installed automatically.
You need to install the solvers separately based on your needs.

.. _manual_installing_solver:

Installing Solvers
------------------------------------

.. attention::

   BendersLib will **NOT** install any solver to your environment automatically.
   You need to install the solvers separately based on your needs.

BendersLib supports several popular optimization solvers.
You can install these solvers individually based on your needs. Installing all of them is not necessary.
Please refer to :doc:`solver` for a list of supported solvers and detailed instructions for each.

.. list-table:: Solvers Installation
    :widths: 15 70 70
    :header-rows: 1
    :name: solver-installation-table

    * - Solver
      - pip
      - conda
    * - :class:`Gurobi`
      - ``pip install gurobipy``
      - ``conda install -c gurobi gurobi``

Verifying the Installation
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To verify that a specific solver is correctly installed and accessible, you can run the following code (for Gurobi as an example):

.. code-block:: python

    from benderslib import Gurobi

    print("Gurobi installed:", Gurobi.is_available())

If the output is ``True``, it indicates that the Gurobi solver is correctly installed and accessible.
Otherwise, it will return ``False``.

Troubleshooting
------------------------------------

*To be added (common issues will be summarized here)...*

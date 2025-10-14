API Reference
======================

.. mermaid::

    classDiagram
        BendersBase <|-- ClassicalBenders

        ProblemBase <|-- MasterProblem
        ProblemBase <|-- SubProblem

        BendersBase o-- MasterProblem
        BendersBase o-- SubProblem
        BendersBase o-- BendersParams
        BendersBase o-- BendersResult

        ProblemBase o-- SolverBase
        SolverBase <|-- Gurobi

        Cut <|-- OptimalityCut
        Cut <|-- FeasibilityCut

        MasterProblem o-- Cut

        class BendersBase{
            +MasterProblem master_problem
            +SubProblem sub_problem
            +BendersParams params
            +solve()
        }
        <<Abstract>> BendersBase

        class ClassicalBenders

        class ProblemBase{
            +SolverBase model
        }

        class MasterProblem{
            +list~Cut~ optimality_cuts
            +list~Cut~ feasibility_cuts
            +add_cut(Cut)
        }
        class SubProblem

        class SolverBase{
            +solve()
        }
        <<Abstract>> SolverBase

        class Cut{
            +list~str~ vars
            +list~float~ coefs
            +float rhs
        }

        class OptimalityCut
        class FeasibilityCut

        class BendersResult{
            +float lb
            +float ub
            +float obj
        }

        class BendersParams{
            +float time_limit
            +float tol_rel
        }


Contents
----------------------

.. toctree::
   :maxdepth: 3

   data.rst
   solver.rst
   core.rst
   benders.rst

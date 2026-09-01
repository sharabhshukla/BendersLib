<div align="center">

![BendersLib Logo](https://raw.githubusercontent.com/phguo/BendersLib/397a53a490f2bbee0cccb3af39d4ee4e9d567301/docs/source/_static/benderslib.png)

[![GitHub Commits](https://img.shields.io/github/last-commit/phguo/benderslib?style=flat-square&logo=github)](https://github.com/phguo/BendersLib)
[![Codecov](https://img.shields.io/codecov/c/github/phguo/benderslib?style=flat-square&logo=codecov)](https://codecov.io/gh/phguo/BendersLib)
[![Pepy Downloads](https://img.shields.io/pepy/dt/benderslib?style=flat-square)](https://pepy.tech/projects/benderslib)
[![PyPI](https://img.shields.io/pypi/v/benderslib.svg?style=flat-square&logo=pypi)](https://pypi.org/project/benderslib/)
[![Python Versions](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fphguo%2FBendersLib%2Frefs%2Fheads%2Fdevelop%2Fpyproject.toml&style=flat-square&logo=python)](https://www.python.org/downloads/)
[![Read the Docs](https://img.shields.io/readthedocs/benderslib?style=flat-square&logo=readthedocs)](https://benders.dev)

</div>

---

# BendersLib: A Benders Decomposition Library in Python

**BendersLib** (https://benders.dev) is a Python library that supports a range of Benders decomposition 
variants, including 
Classical Benders Decomposition [<sup>[1]</sup>](#1), 
Combinatorial Benders Decomposition [<sup>[2]</sup>](#2), 
Generalized Benders Decomposition [<sup>[3]</sup>](#3), 
L-shaped Method [<sup>[4]</sup>](#4), 
Integer L-shaped Method [<sup>[5]</sup>](#5), 
and Logic-based Benders Decomposition [<sup>[6]</sup>](#6). 

While BendersLib provides built-in implementations of 
these methods, it is designed to be extensible. Users can implement custom Benders 
decomposition methods by customizing **subproblem solvers** and **cut generators**, 
and defining **callback functions** for enhancement strategies. 

BendersLib is solver 
agnostic and has built-in interfaces for popular Mathematical Programming and Constraint 
Programming solvers. Its support for rapid prototyping and high extensibility are designed 
to meet the needs of both researchers and practitioners in Operations Research and related fields.

See the [documentation](https://benders.dev) for
[tutorials](https://benders.dev/tutorials), 
[manual](https://benders.dev/manual), 
[API reference](https://benders.dev/api), 
and [examples](https://benders.dev/examples).

## Quick Start

Install BendersLib and a solver of your choice (e.g., Gurobi) using pip.

```bash
python --version
# Should be Python 3.10 or higher

pip install "benderslib[gurobi]"

python -c "import benderslib as bd; print(bd.__url__)"
# Should output "https://benders.dev"
```

BendersLib enables switching from a standard Mathematical Programming model
to Benders decomposition with only a few lines of code.

```python
from benderslib import AnnotatedBenders, ClassicalBenders
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
benders = AnnotatedBenders(
    model,
    solver=Gurobi,
    complicating_vars=complicating_vars,
    benders=ClassicalBenders
)
benders.solve()
print(f"Objective: {benders.result.obj}")
print(f"Solution: {benders.result.solution}")
```

The output will be similar to the following, showing the Benders decomposition process and results.

```
====================================================================================
BendersLib (v0.5.1, Apache-2.0, https://benders.dev) (C) 2021-2026 Peng-Hui Guo
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
```

### GPU-Accelerated Solving with NVIDIA cuOpt (Hybrid: CPU Master + GPU Subproblems)

BendersLib supports GPU-accelerated solving using [NVIDIA cuOpt](https://github.com/NVIDIA/cuopt) for LP and MILP problems.

#### Recommended architecture

In Benders decomposition, the **master MILP is small and re-solved every iteration**, while the
**subproblem LPs dominate the solve count** (e.g., one per scenario). cuOpt's strength is fast
LP solving on the GPU — not repeatedly solving tiny MIPs, where its fixed per-solve cost
(presolve, early heuristics, post-solve reconstruction) dwarfs the actual branch-and-bound time.

BendersLib therefore ships with first-class support for a **hybrid** pattern, which is the
recommended (and default-documented) way of using cuOpt:

- **Master problem (MILP)**: a CPU MIP backend — SCIP via `pyscipopt` — re-solved quickly each iteration.
- **Subproblems (LPs)**: cuOpt on the GPU, with all scenario LPs dispatched **together** in a
  single batch (`BendersParams.batch_sub`) via cuOpt's `BatchSolve`.

Master and subproblems each take their own solver backend, so the two can be mixed freely.
In our benchmarks (50-scenario L-shaped method), this hybrid pattern reduced the solve time
by **~8.5x** (367s → 43s) and the master-problem time by **~1000x** (329s → 0.3s) compared to a
pure-cuOpt run, with identical results.

#### Requirements
- **OS**: Linux or Windows Subsystem for Linux (WSL2)
- **GPU**: NVIDIA GPU with Volta architecture or newer (Compute Capability ≥ 7.0)
- **CUDA**: CUDA 12.x or 13.x
- **Python**: Python ≥ 3.11
- **SCIP** (for the recommended hybrid master): `pip install "benderslib[scip]"`

#### Installation

To install in an external project directly from this branch:

```bash
# Using pip directly
pip install "benderslib[cuopt,scip] @ git+https://github.com/sharabhshukla/BendersLib.git@cuda-cuopt-cu13"
```

Or add to your `requirements.txt`:
```text
benderslib[cuopt,scip] @ git+https://github.com/sharabhshukla/BendersLib.git@cuda-cuopt-cu13
```

*(Once merged and released to PyPI, standard `pip install "benderslib[cuopt,scip]"` will be supported).*

#### Quick Example: single problem, `master_solver` API

```python
from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Cuopt, Scip

from cuopt.linear_programming.problem import Problem, CONTINUOUS, INTEGER, MINIMIZE

# Build problem with native cuOpt Python API
problem = Problem("cuopt_example")
x = problem.addVariable(lb=0.0, ub=1.0, vtype=INTEGER, name="x")
y = problem.addVariable(lb=0.0, vtype=CONTINUOUS, name="y")

problem.addConstraint(x + y >= 15.0, name="c1")
problem.addConstraint(2.0 * x + 5.0 * y >= 30.0, name="c2")
problem.setObjective(3.0 * x + 4.0 * y, sense=MINIMIZE)

# Hybrid solving: subproblems on cuOpt (GPU), master MILP on SCIP (CPU)
benders = AnnotatedBenders(
    problem,
    solver=Cuopt,            # subproblem backend: cuOpt on GPU
    master_solver=Scip,      # master backend: SCIP on CPU (recommended)
    complicating_vars=["x"],
    benders=ClassicalBenders
)
benders.solve()

print(f"Objective: {benders.result.obj}")
print(f"Solution: {benders.result.solution}")
```

#### Quick Example: stochastic program, batched GPU subproblems

```python
from benderslib import LShaped, MasterProblem, SubProblem, SubProblems
from benderslib.solvers import Cuopt, Scip

# Master problem (MILP) — SCIP backend, built with pyscipopt
master_model = ...                        # pyscipopt.Model with integer capacity decisions
master_problem = MasterProblem(Scip(master_model))

# Scenario subproblems (LPs) — cuOpt backend, built with cuOpt's Problem
sub_problems = SubProblems(
    [SubProblem(Cuopt(cuopt_lp_model)) for ...],   # one LP per scenario
    prob=scenario_probabilities,
)

L = LShaped(
    master_problem=master_problem,
    sub_problem=sub_problems,
    complicating_vars=["cap_0", "cap_1", "cap_2", "cap_3"],
)
L.params.batch_sub = True          # dispatch all scenario LPs to cuOpt in one batch
L.params.multi_optim_cut = True
L.solve()
```

> **Note:** cuOpt's `BatchSolve` API is deprecated upstream by NVIDIA and may be removed in a future
> cuOpt release; only the subproblem side of the hybrid pattern depends on it
> (see `BendersParams.batch_sub`). The master backend is unaffected.

#### Model in any framework, batch-solve on the GPU

The hybrid pattern generalizes beyond cuOpt-native models: **any backend that implements
`to_structured()`** (Gurobi, COPT, Pyomo, SCIP) **can supply subproblems that get converted
and solved as a single GPU batch via cuOpt**, using `SubProblems.from_models`:

```python
from benderslib import SubProblems
from benderslib.solvers import Gurobi, Cuopt

scenario_models = [...]  # one gurobipy.Model per scenario, built however you like

sub_problems = SubProblems.from_models(
    scenario_models,
    solver=Gurobi,          # the format the models are built in
    batch_solver=Cuopt,     # convert + solve all scenario LPs on the GPU in one batch
    prob=scenario_probabilities,
)  # params.batch_sub is set to True automatically
```

The same idea is available for the single-subproblem workflow via `AnnotatedBenders(sub_solver=...)`,
symmetric to `master_solver=...`. This is powered by a generic cross-backend model exchange
(`SolverBase.to_structured()` / `SolverBase.from_structured()`) — see the
[API reference](https://benders.dev/api) for details.

More examples are available at https://benders.dev/examples.

## License

BendersLib's source code is licensed under the [Apache-2.0 License](https://github.com/phguo/BendersLib/blob/develop/LICENSE).

## References

- <a id="1">[1]</a> Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
- <a id="2">[2]</a> Codato, G., & Fischetti, M. (2006). Combinatorial Benders’ cuts for mixed-integer linear programming. Operations Research, 54(4), 756–766. https://doi.org/10.1287/opre.1060.0286
- <a id="3">[3]</a> Geoffrion, A. M. (1972). Generalized Benders Decomposition. Journal of Optimization Theory and Applications, 10(4), 237–260. https://doi.org/10.1007/BF00934810
- <a id="4">[4]</a> Van Slyke, R. M., & Wets, R. (1969). L-shaped linear programs with applications to optimal control and stochastic programming. SIAM Journal on Applied Mathematics, 17(4), 638–663. https://doi.org/10.1137/0117061
- <a id="5">[5]</a> Laporte, G., & Louveaux, F. V. (1993). The integer L-shaped method for stochastic integer programs with complete recourse. Operations Research Letters, 13(3), 133–142. https://doi.org/10.1016/0167-6377(93)90002-X
- <a id="6">[6]</a> Hooker, J. N., & Ottosson, G. (2003). Logic-based Benders Decomposition. Mathematical Programming, 96(1), 33–60. https://doi.org/10.1007/s10107-003-0375-9

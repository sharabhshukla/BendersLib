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

More examples are available at https://benders.dev/examples.

## GPU Subproblems with jaxipm

[`jaxipm`](https://github.com/johnviljoen/jaxipm) is a GPU-batched interior-point solver
implemented in JAX. BendersLib's `Jaxipm` backend
(`benderslib.solvers.Jaxipm`, in `benderslib/solvers/_jaxipm.py`) wraps it as a **subproblem-only**
backend for continuous ("nice") LP and convex QP subproblems — it never solves a master/MIP
problem. It targets exactly the case in the file's docstring: *"integrate jaxipm for subproblems
which are nice LP."*

**Requirements:** NVIDIA GPU (Turing / compute capability 7.5+), CUDA 13, Python 3.12+, Linux
x86-64 (including WSL2). Install with `pip install "benderslib[jaxipm]"`.

### Recommended pattern: model the overall problem in your usual tool, indicate jaxipm for the subproblem

jaxipm has no algebraic model-building API of its own — it's a functional NLP solver, not a
modeling library — so `Jaxipm`'s native model is a solver-agnostic **structured dict** (see the
class docstring in `benderslib/solvers/_jaxipm.py` for the exact schema, including the optional
`qobj` field for convex quadratic objectives). You are not expected to build that dict by hand:
model the overall problem (and its master problem) in whichever general-purpose backend you
already use — `Gurobi`, `Copt`, `Scip`, or `Pyomo` — and just indicate that the **subproblem**
specifically should run on jaxipm:

```python
from benderslib import AnnotatedBenders, ClassicalBenders
from benderslib.solvers import Gurobi, Jaxipm

BD = AnnotatedBenders(
    model,                  # built with gurobipy, as usual
    solver=Gurobi,          # overall problem / master problem: Gurobi
    sub_solver=Jaxipm,      # subproblem: jaxipm (GPU interior-point)
    complicating_vars=[...],
    benders=ClassicalBenders,
)
BD.solve()
```

`AnnotatedBenders` converts the subproblem from `solver`'s native format to jaxipm's via
`SolverBase.to_structured()` / `SolverBase.from_structured()` (cross-backend model exchange,
currently implemented for `Gurobi`, `Copt`, `Scip`, `Pyomo`, and `Jaxipm` itself) — no manual
conversion needed. The symmetric `master_solver` parameter exists too, and for multi-scenario
(L-shaped) subproblems, `SubProblems.from_models(models, solver=Gurobi, batch_solver=Jaxipm)`
does the same conversion for a whole batch at once. Working examples:
`examples/solvers/solver_jaxipm.py` (direct, structured-dict usage) and
`examples/solvers/solver_jaxipm_hybrid.py` (the hybrid pattern above).

### GPU batching for scenario subproblems

`Jaxipm.batch_solve()` fuses structurally-identical LP/QP subproblems (e.g., per-scenario
subproblems in `LShaped`, sharing the same constraint matrix and only differing in
right-hand-side data — the standard "fixed recourse" assumption) into **one** JAX `vmap`'d
interior-point solve. Set `BendersParams.batch_sub = True` for `SubProblems` to use it
automatically; if the subproblems aren't structurally compatible, it transparently falls back to
solving them one at a time.

### Operational notes for anyone (agent or human) picking this up

These were found by actually running jaxipm on real hardware (an RTX 500 Ada GPU under WSL2) —
worth knowing before re-deriving them:

- **First solve is slow; repeated solves are not.** A fresh jaxipm trace+compile for even a tiny
  2-variable LP took ~15–20 minutes in that environment. `Jaxipm.solve()` avoids re-compiling on
  every Benders iteration by folding `fix_vars()`-ed variables into the right-hand side (rather
  than baking them into jaxipm's *static* variable bounds) and reusing a compiled solve function
  across calls — empirically confirmed on real hardware to drop from ~1163s → 519s → 41s across
  three successive solves of the same subproblem structure. The cache is invalidated by
  `add_cut()`/`remove_cut()`/`add_estimators()` (which change the problem's structure) or by
  changing *which* variables are fixed (not just their values).
- **jaxipm's dual sign convention is opposite to Gurobi's.** For a MIN problem with a binding
  `>=` row, Gurobi's `Pi` is positive but jaxipm's raw `y_d`/`y_c` multiplier is negative. This is
  already corrected inside `Jaxipm.get_dual_values()` / `get_extreme_ray()` — you don't need to
  worry about it unless you're reading jaxipm's raw output directly.
- **jaxipm has a bug with purely-linear objectives**: a pure LP's objective Hessian is
  identically zero, which trips a malformed-sparsity-pattern bug in jaxipm's
  `initialization.calc_lhs_kkt_structure`. Worked around with a negligible (`1e-9`) quadratic
  regularization term added to the objective — see `_HESS_REGULARIZATION_EPS` in
  `benderslib/solvers/_jaxipm.py`.
- **`initialize_problem_regular()` (jaxipm) is not abstract-eval-safe under plain `jax.jit`**
  (raises `"nse must be specified"` from a sparse `.sum_duplicates()` call), but *is* safe under
  `jax.vmap`. `Jaxipm` therefore always calls it through `equinox.filter_vmap`, including for a
  single solve (a batch of size 1), never through `equinox.filter_jit` alone.
- **On WSL2, set `TF_GPU_ALLOCATOR=cuda_malloc_async` and
  `XLA_PYTHON_CLIENT_PREALLOCATE=false`** before importing jax/jaxipm — without them, JAX's
  default pinned-host-memory allocator can fail with `CUDA_ERROR_OUT_OF_MEMORY` even when the GPU
  itself has free memory (a WSL2 locked-memory (`ulimit -l`) limitation, not a real OOM).
- **Cross-backend `to_structured()` is linear-only for now.** `Gurobi`/`Copt`/`Scip`/`Pyomo`'s
  `to_structured()` only exports linear objectives; a `qobj` (convex QP) subproblem must currently
  be built directly as a structured dict, or converted with a custom `to_structured()`.
- Not yet re-verified after the caching refactor above (each GPU compile cycle is expensive, so
  budget time accordingly): `add_cut`/`remove_cut`, `get_extreme_ray`, and multi-instance
  `batch_solve`. They reuse the same validated core mechanics (`__solve_lp`, the sign-convention
  fix, the free-variable/RHS-shift reformulation) but weren't individually re-run end-to-end
  after the last edit — worth a smoke test (`tests/solvers/test_jaxipm_solver.py`) before
  depending on them in production.

## License

BendersLib's source code is licensed under the [Apache-2.0 License](https://github.com/phguo/BendersLib/blob/develop/LICENSE).

## References

- <a id="1">[1]</a> Benders, J. F. (1962). Partitioning procedures for solving mixed-variables programming problems. Numerische Mathematik, 4(1), 238–252. https://doi.org/10.1007/BF01386316
- <a id="2">[2]</a> Codato, G., & Fischetti, M. (2006). Combinatorial Benders’ cuts for mixed-integer linear programming. Operations Research, 54(4), 756–766. https://doi.org/10.1287/opre.1060.0286
- <a id="3">[3]</a> Geoffrion, A. M. (1972). Generalized Benders Decomposition. Journal of Optimization Theory and Applications, 10(4), 237–260. https://doi.org/10.1007/BF00934810
- <a id="4">[4]</a> Van Slyke, R. M., & Wets, R. (1969). L-shaped linear programs with applications to optimal control and stochastic programming. SIAM Journal on Applied Mathematics, 17(4), 638–663. https://doi.org/10.1137/0117061
- <a id="5">[5]</a> Laporte, G., & Louveaux, F. V. (1993). The integer L-shaped method for stochastic integer programs with complete recourse. Operations Research Letters, 13(3), 133–142. https://doi.org/10.1016/0167-6377(93)90002-X
- <a id="6">[6]</a> Hooker, J. N., & Ottosson, G. (2003). Logic-based Benders Decomposition. Mathematical Programming, 96(1), 33–60. https://doi.org/10.1007/s10107-003-0375-9

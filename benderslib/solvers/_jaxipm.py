# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import copy

import numpy as np

from ..consts import BendersConsts as CST
from ._base import SolverBase
from ..errors import BendersNotImplementedError, BendersBackendError

_SENSE_MAP = {CST.EQ: 'E', CST.LE: 'L', CST.GE: 'G'}

_HESS_REGULARIZATION_EPS = 1e-9
"""Tiny quadratic regularization added to the objective to work around a jaxipm bug where a
constant (exactly-zero) objective Hessian produces a malformed sparsity pattern -- see the
comment at its use site in ``Jaxipm.__solve_lp`` for details."""


def _row_coefs(coefs: dict, var_index: dict, nx: int) -> np.ndarray:
    row = np.zeros(nx)
    for name, coef in coefs.items():
        row[var_index[name]] = float(coef)
    return row


class Jaxipm(SolverBase):
    """`jaxipm <https://github.com/johnviljoen/jaxipm>`__ solver interface for BendersLib.

    jaxipm is a GPU-batched interior-point method implemented in JAX. This backend targets
    **continuous, convex subproblems** in Benders decomposition -- "nice" LPs, and convex QPs
    via the optional ``qobj`` field below -- it does not support integer/binary variables, so
    it is only suitable as a subproblem backend (e.g., for :class:`~benderslib.ClassicalBenders`
    or :class:`~benderslib.LShaped`), never as a master problem backend. A convex quadratic
    subproblem objective still yields valid Benders cuts from :meth:`get_dual_values` /
    :meth:`get_var_coefs` by the same convex-sensitivity argument :class:`~benderslib.GeneralizedBenders`
    relies on for nonlinear (but convex) subproblems in general.

    Unlike other backends, ``Jaxipm`` has no "native" solver-object format to wrap (jaxipm
    itself is a functional NLP solver, not a model-building API), so its native model is a
    solver-agnostic **structured dictionary**:

    .. code-block:: python

        {
            "sense": "min",
            "vars": [
                {"name": "x1", "lb": 0.0, "ub": float("inf"), "vtype": "C", "obj": 1.0},
                ...
            ],
            "constraints": [
                {"name": "c1", "sense": "G", "rhs": 6.0, "coefs": {"x1": 1.0, "x2": 2.0}},
                ...
            ],
            "qobj": [  # optional: convex quadratic objective terms, f(x) += coef * x_i * x_j
                {"vars": ["x1", "x1"], "coef": 0.5},
                ...
            ],
        }

    where constraint ``sense`` is ``"L"`` (:math:`\\leq`), ``"G"`` (:math:`\\geq`), or
    ``"E"`` (:math:`=`).

    .. note::
        ``qobj`` terms must be **convex** (the sum they define, as a quadratic form, must be
        positive semi-definite) -- this is not checked, and jaxipm's interior-point method will
        not reliably converge to a global optimum otherwise. They must also only involve
        variables that are never :meth:`fix_vars`-ed (i.e., not complicating variables) --
        see :meth:`make_sub_problem`, which already enforces this when auto-decomposing.

    This is also exactly the format returned by :meth:`to_structured` and accepted by
    :meth:`from_structured`, so a model built in any other backend that implements
    :meth:`~benderslib.solvers.SolverBase.to_structured` can be converted directly (note,
    however, that the built-in backends' ``to_structured()`` currently only export **linear**
    objectives -- a ``qobj`` subproblem must be built directly in this dict format, or with a
    custom ``to_structured()``)::

        from benderslib.solvers import Gurobi, Jaxipm

        sub = Jaxipm.from_structured(Gurobi(gurobi_sub_model).to_structured())

    .. admonition:: GPU batching for scenario subproblems
        :class: note

        :meth:`batch_solve` fuses many structurally-identical LP subproblems (e.g., the
        per-scenario subproblems of :class:`~benderslib.LShaped`, or repeated re-solves of the
        same subproblem across Benders iterations) into a **single** JAX ``vmap``'d interior-point
        solve — one block-diagonal KKT factorization per iteration for the whole batch, rather
        than one factorization per subproblem. Set :attr:`~benderslib.BendersParams.batch_sub`
        to ``True`` to have :class:`~benderslib.SubProblems` use it automatically; see
        :meth:`batch_solve` for the structural precondition this requires.

    .. warning::
        jaxipm requires an NVIDIA GPU (Turing / compute capability 7.5 or newer), CUDA 13,
        and Python 3.12+, on Linux x86-64. It is a general nonlinear interior-point solver
        (not an LP-specialized simplex/barrier method), so numerical behavior on
        degenerate/highly-structured LPs may differ from a dedicated LP solver.

    Parameters
    ---------------
    model: dict
        The structured, solver-agnostic model dict described above.
    solver_options: dict, optional
        Overrides applied on top of ``jaxipm.default_params()`` (IPOPT-style parameters).
    """

    def __init__(self, model: dict, solver_options: dict = None) -> None:
        super().__init__(model)

        self.model = copy.deepcopy(model)
        self.status = CST.UNSOLVED

        if self.model.get('sense', 'min') != 'min':
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")
        self._sense = CST.MIN

        var_defs = self.model.get('vars', [])
        if any(v.get('vtype', 'C') != 'C' for v in var_defs):
            raise BendersNotImplementedError(
                "The Jaxipm backend only supports continuous, convex problems (LP or convex "
                "QP). Integer/binary variables must be fixed or relaxed before using this "
                "backend, e.g. via SolverBase.make_sub_problem()."
            )

        self._all_vars = [v['name'] for v in var_defs]
        self._int_vars = []
        self._bin_vars = []
        self._var_index = {name: i for i, name in enumerate(self._all_vars)}
        nx = len(self._all_vars)

        self._obj_coefs = np.array([float(v.get('obj', 0.0)) for v in var_defs])

        # Optional convex quadratic objective term: f(x) = obj'x + sum(coef * x_i * x_j).
        # See the class docstring for the "qobj" structured-dict field, and __qobj_terms for
        # the restriction this places on which variables may be fix_vars()-ed.
        self._qobj = [
            (q['vars'][0], q['vars'][1], float(q['coef'])) for q in self.model.get('qobj', [])
        ]

        self._var_bounds = {
            v['name']: (float(v.get('lb', 0.0)), float(v.get('ub', float('inf'))))
            for v in var_defs
            if float(v.get('lb', 0.0)) != 0.0 or float(v.get('ub', float('inf'))) != float('inf')
        }

        # Canonical row storage: original constraints, then variable bounds turned into
        # explicit rows (same standardization as the Gurobi/COPT/Pyomo backends), so that
        # get_rhs() / get_var_coefs() / get_dual_values() stay index-aligned.
        self._constraints: list[dict] = []
        self._row_names: dict[str, int] = {}
        for c in self.model.get('constraints', []):
            self._row_names[c['name']] = len(self._constraints)
            self._constraints.append({
                'sense': c['sense'],
                'rhs': float(c['rhs']),
                'coefs': dict(c['coefs']),
            })

        self.__bounds_to_constrs(nx)

        self._A = np.array([_row_coefs(c['coefs'], self._var_index, nx) for c in self._constraints]) \
            if self._constraints else np.zeros((0, nx))
        self._row_sense = [c['sense'] for c in self._constraints]
        self._row_rhs0 = np.array([c['rhs'] for c in self._constraints])

        self._fixed: dict[str, float] = {}
        self._x_val: dict[str, float] = {}
        self._duals: list[float] = []
        self._obj_val = float('nan')

        self._rhs = self.get_rhs()
        self._constr_num = len(self._constraints)

        # Bumped by add_cut/remove_cut to invalidate __cache (see __ensure_compiled): changing
        # which rows/columns exist requires a fresh jaxipm trace+compile, but merely fixing a
        # variable to a *different* value (the common case across repeated Benders iterations)
        # does not, and is threaded through as a traced argument instead -- see __ensure_compiled.
        self._version = 0
        self._cache: dict | None = None

        self._jaxipm_params = None  # lazily built on first solve (requires importing jaxipm)
        self.__setup_model(solver_options)

    def __bounds_to_constrs(self, nx: int) -> None:
        if any(lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()):
            raise BendersNotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        for var_name, (lb, ub) in self._var_bounds.items():
            if lb > 0:
                c_name = f"__{var_name}_lb"
                self._row_names[c_name] = len(self._constraints)
                self._constraints.append({'sense': 'G', 'rhs': lb, 'coefs': {var_name: 1.0}})
            if ub < float('inf'):
                c_name = f"__{var_name}_ub"
                self._row_names[c_name] = len(self._constraints)
                self._constraints.append({'sense': 'L', 'rhs': ub, 'coefs': {var_name: 1.0}})

    def __setup_model(self, solver_options: dict = None) -> None:
        from jaxipm import default_params
        p = default_params()
        p.update(self._options.get('JAXIPM_OPTIONS', {}))
        if solver_options:
            p.update(solver_options)
        self._jaxipm_params = p

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            prob = [1.0 / len(estimators)] * len(estimators) if len(estimators) > 1 else [1.0]
        elif len(prob) != len(estimators):
            from ..errors import MismatchedProbabilityError
            raise MismatchedProbabilityError("Length of <prob> must match length of <estimators>.")

        self._version += 1
        nx_old = len(self._all_vars)
        for name, obj_coef in zip(estimators, prob):
            self._var_index[name] = len(self._all_vars)
            self._all_vars.append(name)
            self._obj_coefs = np.append(self._obj_coefs, obj_coef)
            if lb != 0:
                self._var_bounds[name] = (lb, float('inf'))

        # Existing rows gain a zero column for each new estimator variable.
        n_new = len(self._all_vars) - nx_old
        if self._A.shape[0] > 0:
            self._A = np.hstack([self._A, np.zeros((self._A.shape[0], n_new))])
        else:
            self._A = np.zeros((0, len(self._all_vars)))

        if lb != 0:
            for name in estimators:
                c_name = f"__{name}_lb"
                self._row_names[c_name] = len(self._constraints)
                self._constraints.append({'sense': 'G', 'rhs': lb, 'coefs': {name: 1.0}})
                row = np.zeros(len(self._all_vars))
                row[self._var_index[name]] = 1.0
                self._A = np.vstack([self._A, row])
                self._row_sense.append('G')
                self._row_rhs0 = np.append(self._row_rhs0, lb)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for name, value in var_values.items():
            self._fixed[name] = float(value)

    def unfix_vars(self, vars: list[str]) -> None:
        for name in vars:
            self._fixed.pop(name, None)

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {v: self._x_val[v] for v in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        vars_to_get = vars or self._all_vars
        return {v: self._A[:, self._var_index[v]].tolist() for v in vars_to_get}

    def get_rhs(self) -> list[float]:
        return self._row_rhs0.tolist()

    def get_dual_values(self) -> list[float]:
        return list(self._duals)

    def get_extreme_ray(self) -> list[float]:
        """Derive a Farkas-type infeasibility certificate via an elastic phase-1 LP.

        jaxipm does not expose a dual infeasibility certificate directly (on primal
        infeasibility, the underlying interior-point method enters its restoration phase
        and reports :const:`~benderslib.BendersConsts.INFEASIBLE` if that fails to find a
        feasible point). Instead, we solve an auxiliary elastic LP that minimizes the total
        constraint violation, and derive the ray from its optimal dual values, negated to
        match the sign convention of :class:`~benderslib.solvers.Gurobi`'s ``FarkasDual``
        (the convention :class:`~benderslib.ClassicalFC` / :class:`~benderslib.LShapedFC`
        cuts are written against).
        """
        x_L, x_U = self.__effective_bounds()
        n = self._A.shape[0]
        nx = len(self._all_vars)

        # Elastic reformulation: a_i x + s_i (>=)/ - s_i (<=) [+ t_i for '=='] = b_i, s,t >= 0,
        # minimize sum(s) + sum(t). Feasible iff the original problem is feasible.
        n_slack = sum(2 if s == 'E' else 1 for s in self._row_sense)
        A_ext = np.zeros((n, nx + n_slack))
        A_ext[:, :nx] = self._A
        obj_ext = np.zeros(nx + n_slack)
        col = nx
        for i, s in enumerate(self._row_sense):
            if s == 'G':
                A_ext[i, col] = 1.0
                obj_ext[col] = 1.0
                col += 1
            elif s == 'L':
                A_ext[i, col] = -1.0
                obj_ext[col] = 1.0
                col += 1
            else:  # 'E'
                A_ext[i, col] = 1.0
                A_ext[i, col + 1] = -1.0
                obj_ext[col] = 1.0
                obj_ext[col + 1] = 1.0
                col += 2

        x_L_ext = np.concatenate([x_L, np.zeros(n_slack)])
        x_U_ext = np.concatenate([x_U, np.full(n_slack, float('inf'))])

        _, duals, obj_val, status_code = self.__solve_lp(
            A_ext, self._row_sense, self._row_rhs0, obj_ext, x_L_ext, x_U_ext)

        status = self._options['STATUS_CODES']['JAXIPM'].get(status_code, 'UNKNOWN')
        if getattr(CST, status, None) not in (CST.OPTIMAL,):
            raise BendersBackendError(
                f"Phase-1 elastic LP for Farkas ray extraction terminated with status <{status}>."
            )

        return [-d for d in duals]

    def get_obj(self) -> float:
        return self._obj_val

    def to_structured(self) -> dict:
        """Return the solver-agnostic structured representation of the model.

        Since :class:`Jaxipm`'s native model *is* this structured dict, this is a deep copy
        of the model passed to (or reconstructed by) the constructor.
        """
        return copy.deepcopy(self.model)

    @classmethod
    def from_structured(cls, structured: dict) -> dict:
        """Return a native (structured-dict) model built from ``structured``.

        Since :class:`Jaxipm`'s native model format *is* the structured representation, this
        is simply a deep copy of ``structured`` — see :meth:`to_structured`.
        """
        return copy.deepcopy(structured)

    def add_cut(self, cut, name=None) -> None:
        sense = _SENSE_MAP.get(cut.sense)
        if sense is None:
            raise BendersBackendError(f"Unsupported cut sense: {cut.sense}")

        coefs = dict(zip(cut.vars, cut.coefs))
        if name:
            self._row_names[name] = len(self._constraints)
        self._constraints.append({'sense': sense, 'rhs': float(cut.rhs), 'coefs': coefs})

        row = _row_coefs(coefs, self._var_index, len(self._all_vars))
        self._A = np.vstack([self._A, row]) if self._A.shape[0] > 0 else row.reshape(1, -1)
        self._row_sense.append(sense)
        self._row_rhs0 = np.append(self._row_rhs0, float(cut.rhs))
        self._version += 1

    def remove_cut(self, cut_name: str) -> None:
        idx = self._row_names.pop(cut_name, None)
        if idx is None:
            return

        self._constraints.pop(idx)
        self._A = np.delete(self._A, idx, axis=0)
        self._row_sense.pop(idx)
        self._row_rhs0 = np.delete(self._row_rhs0, idx)
        self._version += 1

        for n, i in list(self._row_names.items()):
            if i > idx:
                self._row_names[n] = i - 1

    def __effective_bounds(self) -> tuple:
        nx = len(self._all_vars)
        lb = np.zeros(nx)
        ub = np.full(nx, float('inf'))
        for name, value in self._fixed.items():
            j = self._var_index[name]
            lb[j] = value
            ub[j] = value
        return lb, ub

    @staticmethod
    def __initial_point(x_L: np.ndarray, x_U: np.ndarray) -> np.ndarray:
        return np.where(np.isinf(x_U), x_L, (x_L + x_U) / 2.0)

    def __qobj_terms(self, free_names: tuple) -> list:
        """Resolve the quadratic objective terms to (local_i, local_j, coef) index pairs into
        ``free_names``. Raises if a term involves a currently-fixed variable: quadratic terms
        are only supported among a subproblem's own free (recourse) variables -- the same
        restriction the linear objective already has for complicating variables (see
        :meth:`make_sub_problem`, which zeroes out their linear objective coefficient).
        """
        if not self._qobj:
            return []

        local_idx = {name: i for i, name in enumerate(free_names)}
        terms = []
        for v_i, v_j, coef in self._qobj:
            if v_i in self._fixed or v_j in self._fixed:
                raise BendersNotImplementedError(
                    f"Jaxipm's quadratic objective term ({v_i}, {v_j}) involves a fixed "
                    "variable. Quadratic objective terms are only supported among a "
                    "subproblem's own free variables, not complicating variables."
                )
            terms.append((local_idx[v_i], local_idx[v_j], coef))
        return terms

    @staticmethod
    def __add_quadratic(expr, xf, qobj_idx: list):
        for i, j, coef in qobj_idx:
            expr = expr + coef * xf[i] * xf[j]
        return expr

    def __eval_obj(self, x_full: dict) -> float:
        obj_val = sum(c * x_full[v] for c, v in zip(self._obj_coefs, self._all_vars))
        obj_val += sum(coef * x_full[v_i] * x_full[v_j] for v_i, v_j, coef in self._qobj)
        return float(obj_val)

    def __solve_lp(
            self, A: np.ndarray, row_sense: list, rhs: np.ndarray, obj_coefs: np.ndarray,
            x_L: np.ndarray, x_U: np.ndarray, x0: np.ndarray = None,
    ) -> tuple:
        """Solve a single LP ``min obj_coefs'x  s.t.  A[eq]x = rhs[eq], A[ineq]x (<=/>=) rhs[ineq], x_L<=x<=x_U``
        via jaxipm, returning ``(x, duals, obj_val, status_code)`` with ``duals`` aligned to ``row_sense``.
        """
        import jax
        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp
        from jaxipm.initialization import initialize_common_problem, initialize_problem_regular
        from jaxipm.solver import solve as _jaxipm_solve

        nx = A.shape[1]
        eq_rows = [i for i, s in enumerate(row_sense) if s == 'E']
        ineq_rows = [i for i, s in enumerate(row_sense) if s != 'E']

        A_eq = jnp.asarray(A[eq_rows]) if eq_rows else None
        b_eq = jnp.asarray(rhs[eq_rows]) if eq_rows else None
        A_ineq = jnp.asarray(A[ineq_rows]) if ineq_rows else None
        b_ineq = jnp.asarray(rhs[ineq_rows]) if ineq_rows else None
        ineq_sense = [row_sense[i] for i in ineq_rows]

        c_vec = jnp.asarray(obj_coefs)

        # jaxipm's sparsity-pattern probing calls f/c/d with a flat (nx,) array, while the
        # solver's own iterations call them with a column (nx, 1) array; jnp.ravel handles both.
        def f(x):
            xf = jnp.ravel(x)
            # A tiny quadratic term works around a jaxipm bug (upstream: mismatched empty COO
            # shapes in initialization.calc_lhs_kkt_structure) that is triggered when the
            # objective's Hessian is *exactly* zero everywhere, as it always is for a pure LP.
            # It is negligible relative to any realistic objective and does not change the LP's
            # optimal vertex in any way that matters for Benders cut generation.
            return jnp.dot(c_vec, xf) + _HESS_REGULARIZATION_EPS * jnp.sum(xf * xf)

        def c_fn(x):
            return None if A_eq is None else A_eq @ jnp.ravel(x) - b_eq

        def d_fn(x):
            return None if A_ineq is None else A_ineq @ jnp.ravel(x) - b_ineq

        d_L = jnp.array([0.0 if s == 'G' else -jnp.inf for s in ineq_sense])
        d_U = jnp.array([0.0 if s == 'L' else jnp.inf for s in ineq_sense])

        x0_np = x0 if x0 is not None else self.__initial_point(x_L, x_U)
        x0_j = jnp.asarray(np.nan_to_num(x0_np, nan=0.0, posinf=0.0, neginf=0.0))
        x_L_j = jnp.asarray(x_L)
        x_U_j = jnp.asarray(x_U)

        cp = initialize_common_problem(f, c_fn, d_fn, x_L_j, x_U_j, d_L, d_U, x0_j, self._jaxipm_params)
        state = initialize_problem_regular(cp, x0_j)
        state, term = _jaxipm_solve(cp, state)

        x_sol = np.asarray(state.it.x[:nx]).flatten()
        y_c_sol = np.asarray(state.it.y_c).flatten() if eq_rows else np.zeros(0)
        y_d_sol = np.asarray(state.it.y_d).flatten() if ineq_rows else np.zeros(0)
        status_code = int(np.asarray(term).flatten()[0])

        # jaxipm's y_c/y_d multipliers come out with the opposite sign of the shadow-price
        # convention BendersLib's cut formulas are written against (verified empirically: for
        # a MIN problem with binding '>=' rows, Gurobi's Pi is positive but jaxipm's y_d is
        # negative for the same rows) — negate to match.
        duals = np.zeros(len(row_sense))
        for k, i in enumerate(eq_rows):
            duals[i] = -y_c_sol[k]
        for k, i in enumerate(ineq_rows):
            duals[i] = -y_d_sol[k]

        obj_val = float(np.dot(obj_coefs, x_sol))
        return x_sol, duals.tolist(), obj_val, status_code

    def __ensure_compiled(self) -> dict:
        """Build (or reuse) a compiled, warm solve function for the current variable partition.

        jaxipm's ``x_L``/``x_U`` (and the rest of its ``CommonProblem``) are *static*: they get
        traced and compiled into the problem once and cannot vary between calls (this is also
        why GPU batching in :meth:`batch_solve` has to work this way). So instead of encoding
        :attr:`_fixed` as tight box bounds (which would force a full jaxipm re-trace+recompile
        on every :meth:`solve` call -- prohibitively slow for a Benders loop that re-solves the
        same subproblem tens or hundreds of times), fixed variables are dropped from the decision
        vector entirely and folded into an *effective* right-hand side, which is threaded through
        as a traced function argument. jaxipm only needs to trace+compile once per distinct
        (fixed-variable *set*, constraint structure) pair -- typically once for a subproblem's
        entire lifetime in a Benders run -- and each :meth:`solve` call after that just evaluates
        the already-compiled function with new numeric values.
        """
        free_names = tuple(v for v in self._all_vars if v not in self._fixed)
        fixed_names = tuple(self._fixed.keys())
        cache = self._cache
        if (cache is not None and cache['free_names'] == free_names
                and cache['fixed_names'] == fixed_names and cache['version'] == self._version):
            return cache

        import jax
        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp
        import equinox as eqx
        from jaxipm.initialization import initialize_common_problem, initialize_problem_regular
        from jaxipm.solver import solve as _jaxipm_solve

        free_idx = [self._var_index[v] for v in free_names]
        fixed_idx = [self._var_index[v] for v in fixed_names]
        A_free = self._A[:, free_idx] if free_idx else np.zeros((self._A.shape[0], 0))
        A_fixed = self._A[:, fixed_idx] if fixed_idx else np.zeros((self._A.shape[0], 0))
        obj_free = self._obj_coefs[free_idx] if free_idx else np.zeros(0)

        row_sense = self._row_sense
        eq_rows = [i for i, s in enumerate(row_sense) if s == 'E']
        ineq_rows = [i for i, s in enumerate(row_sense) if s != 'E']
        ineq_sense = [row_sense[i] for i in ineq_rows]

        A_eq_free = jnp.asarray(A_free[eq_rows]) if eq_rows else None
        A_ineq_free = jnp.asarray(A_free[ineq_rows]) if ineq_rows else None
        c_vec = jnp.asarray(obj_free)
        n_free = len(free_names)
        qobj_idx = self.__qobj_terms(free_names)

        def f(x):
            xf = jnp.ravel(x)
            obj = jnp.dot(c_vec, xf) + _HESS_REGULARIZATION_EPS * jnp.sum(xf * xf)
            return self.__add_quadratic(obj, xf, qobj_idx)

        def c_fn(x, b_eq):
            return None if A_eq_free is None else A_eq_free @ jnp.ravel(x) - b_eq

        def d_fn(x, b_ineq):
            return None if A_ineq_free is None else A_ineq_free @ jnp.ravel(x) - b_ineq

        d_L = jnp.array([0.0 if s == 'G' else -jnp.inf for s in ineq_sense])
        d_U = jnp.array([0.0 if s == 'L' else jnp.inf for s in ineq_sense])

        x_L = np.zeros(n_free)
        x_U = np.full(n_free, float('inf'))
        x0 = jnp.asarray(self.__initial_point(x_L, x_U))

        sample_b_eq = jnp.zeros(len(eq_rows))
        sample_b_ineq = jnp.zeros(len(ineq_rows))
        cp = initialize_common_problem(
            f, c_fn, d_fn, jnp.asarray(x_L), jnp.asarray(x_U), d_L, d_U, x0, self._jaxipm_params,
            function_args=[(), (sample_b_eq,), (sample_b_ineq,)],
        )

        def solve_one(b_eq_i, b_ineq_i):
            state = initialize_problem_regular(cp, x0, args=[(), (b_eq_i,), (b_ineq_i,)])
            state, term = _jaxipm_solve(cp, state)
            return state.it.x[:n_free, 0], state.it.y_c[:, 0], state.it.y_d[:, 0], term

        # NOTE: initialize_problem_regular() calls a sparse .sum_duplicates() that is only
        # abstract-eval-safe under vmap, not under plain jit (raises "nse must be specified"
        # otherwise, a jaxipm/jax.experimental.sparse quirk) -- so a size-1 vmap batch is used
        # as a compiled, warm, repeatedly-callable single-instance solve, exactly like
        # batch_solve's batching, just with a batch dimension of 1.
        solve_one_batched = eqx.filter_vmap(solve_one)

        cache = {
            'free_names': free_names, 'fixed_names': fixed_names, 'version': self._version,
            'solve_one': solve_one_batched, 'A_fixed': A_fixed,
            'eq_rows': eq_rows, 'ineq_rows': ineq_rows,
        }
        self._cache = cache
        return cache

    def solve(self) -> None:
        import jax.numpy as jnp

        cache = self.__ensure_compiled()
        free_names, fixed_names = cache['free_names'], cache['fixed_names']

        fixed_vals = np.array([self._fixed[v] for v in fixed_names]) if fixed_names else np.zeros(0)
        shift = cache['A_fixed'] @ fixed_vals if fixed_names else np.zeros(self._A.shape[0])
        eff_rhs = self._row_rhs0 - shift

        b_eq = jnp.asarray(eff_rhs[cache['eq_rows']])[None, :]
        b_ineq = jnp.asarray(eff_rhs[cache['ineq_rows']])[None, :]
        x_free, y_c, y_d, term = cache['solve_one'](b_eq, b_ineq)

        x_free = np.asarray(x_free)[0]
        y_c = np.asarray(y_c)[0]
        y_d = np.asarray(y_d)[0]
        x_full = dict(zip(fixed_names, fixed_vals))
        x_full.update(dict(zip(free_names, x_free)))
        self._x_val = {v: x_full[v] for v in self._all_vars}

        # Sign convention: see __solve_lp.
        duals = np.zeros(len(self._row_sense))
        for k, i in enumerate(cache['eq_rows']):
            duals[i] = -y_c[k]
        for k, i in enumerate(cache['ineq_rows']):
            duals[i] = -y_d[k]
        self._duals = duals.tolist()

        self._obj_val = self.__eval_obj(x_full)
        self._update_status('JAXIPM', int(np.asarray(term).flatten()[0]))

    @classmethod
    def batch_solve(cls, instances: list['Jaxipm'], solver_options: dict = None) -> None:
        """Solve many structurally-identical LP instances in one fused GPU interior-point solve.

        This is jaxipm's headline feature applied to Benders: all instances must share the
        same variables (same names, same order), the same constraint matrix and senses, and
        the same *set* of currently-fixed variables (their fixed *values* may differ) — i.e.,
        they must be the same subproblem template, differing only in which values the
        complicating variables are fixed to and/or their right-hand-side data. This is the
        standard "fixed recourse" assumption already implicit in two-stage stochastic
        programming / the L-shaped method.

        If this precondition is not met, this method transparently falls back to solving each
        instance sequentially via :meth:`solve`.

        Parameters
        ---------------
        instances : list[Jaxipm]
            The Jaxipm solver instances to solve together.
        solver_options : dict, optional
            Overrides applied on top of each instance's jaxipm parameters for this batch.
        """
        if not instances:
            return

        if not cls.__batch_compatible(instances):
            for inst in instances:
                inst.solve()
            return

        import jax
        jax.config.update("jax_enable_x64", True)
        import jax.numpy as jnp
        import equinox as eqx
        from jaxipm.initialization import initialize_common_problem, initialize_problem_regular
        from jaxipm.solver import solve as _jaxipm_solve

        ref = instances[0]
        nx = len(ref._all_vars)
        fixed_names = list(ref._fixed.keys())
        free_names = [v for v in ref._all_vars if v not in ref._fixed]
        free_idx = [ref._var_index[v] for v in free_names]
        fixed_idx = [ref._var_index[v] for v in fixed_names]

        A_free = ref._A[:, free_idx] if free_idx else np.zeros((ref._A.shape[0], 0))
        A_fixed = ref._A[:, fixed_idx] if fixed_idx else np.zeros((ref._A.shape[0], 0))
        obj_free = ref._obj_coefs[free_idx] if free_idx else np.zeros(0)

        eff_rhs = []
        for inst in instances:
            fixed_vals = np.array([inst._fixed[v] for v in fixed_names]) if fixed_names else np.zeros(0)
            shift = A_fixed @ fixed_vals if fixed_idx else np.zeros(ref._A.shape[0])
            eff_rhs.append(inst._row_rhs0 - shift)
        eff_rhs = np.stack(eff_rhs)  # (B, n_rows)

        row_sense = ref._row_sense
        eq_rows = [i for i, s in enumerate(row_sense) if s == 'E']
        ineq_rows = [i for i, s in enumerate(row_sense) if s != 'E']
        ineq_sense = [row_sense[i] for i in ineq_rows]

        A_eq_free = jnp.asarray(A_free[eq_rows]) if eq_rows else None
        A_ineq_free = jnp.asarray(A_free[ineq_rows]) if ineq_rows else None
        c_vec = jnp.asarray(obj_free)
        n_free = len(free_names)
        qobj_idx = ref.__qobj_terms(free_names)

        def f(x):
            xf = jnp.ravel(x)
            # See the identical comment in __ensure_compiled: works around a jaxipm bug
            # triggered by an exactly-zero objective Hessian (always the case for a pure LP).
            obj = jnp.dot(c_vec, xf) + _HESS_REGULARIZATION_EPS * jnp.sum(xf * xf)
            return cls.__add_quadratic(obj, xf, qobj_idx)

        def c_fn(x, b_eq):
            return None if A_eq_free is None else A_eq_free @ jnp.ravel(x) - b_eq

        def d_fn(x, b_ineq):
            return None if A_ineq_free is None else A_ineq_free @ jnp.ravel(x) - b_ineq

        d_L = jnp.array([0.0 if s == 'G' else -jnp.inf for s in ineq_sense])
        d_U = jnp.array([0.0 if s == 'L' else jnp.inf for s in ineq_sense])

        x_L = np.zeros(n_free)
        x_U = np.full(n_free, float('inf'))
        x0 = jnp.asarray(cls.__initial_point(x_L, x_U))
        x_L_j = jnp.asarray(x_L)
        x_U_j = jnp.asarray(x_U)

        b_eq_batch = jnp.asarray(eff_rhs[:, eq_rows]) if eq_rows else jnp.zeros((len(instances), 0))
        b_ineq_batch = jnp.asarray(eff_rhs[:, ineq_rows]) if ineq_rows else jnp.zeros((len(instances), 0))

        sample_b_eq = b_eq_batch[0]
        sample_b_ineq = b_ineq_batch[0]
        cp = initialize_common_problem(
            f, c_fn, d_fn, x_L_j, x_U_j, d_L, d_U, x0, ref._jaxipm_params,
            function_args=[(), (sample_b_eq,), (sample_b_ineq,)],
        )

        def solve_one(b_eq_i, b_ineq_i):
            state = initialize_problem_regular(cp, x0, args=[(), (b_eq_i,), (b_ineq_i,)])
            state, term = _jaxipm_solve(cp, state)
            return state.it.x[:n_free, 0], state.it.y_c[:, 0], state.it.y_d[:, 0], term

        xs, y_cs, y_ds, terms = eqx.filter_vmap(solve_one)(b_eq_batch, b_ineq_batch)

        xs = np.asarray(xs)
        y_cs = np.asarray(y_cs)
        y_ds = np.asarray(y_ds)
        terms = np.asarray(terms).reshape(len(instances))

        for b, inst in enumerate(instances):
            x_full = dict(zip(fixed_names, (inst._fixed[v] for v in fixed_names)))
            x_full.update(dict(zip(free_names, xs[b])))
            inst._x_val = {v: x_full[v] for v in inst._all_vars}

            # Sign convention: see __solve_lp.
            duals = np.zeros(len(row_sense))
            for k, i in enumerate(eq_rows):
                duals[i] = -y_cs[b, k]
            for k, i in enumerate(ineq_rows):
                duals[i] = -y_ds[b, k]
            inst._duals = duals.tolist()

            inst._obj_val = inst.__eval_obj(x_full)
            inst._update_status('JAXIPM', int(terms[b]))

    @classmethod
    def __batch_compatible(cls, instances: list['Jaxipm']) -> bool:
        ref = instances[0]
        for inst in instances[1:]:
            if inst._all_vars != ref._all_vars:
                return False
            if set(inst._fixed.keys()) != set(ref._fixed.keys()):
                return False
            if inst._row_sense != ref._row_sense:
                return False
            if inst._A.shape != ref._A.shape or not np.array_equal(inst._A, ref._A):
                return False
            if inst._qobj != ref._qobj:
                return False
        return True

    def _bnc_solve(self, callback_handler) -> None:
        raise BendersNotImplementedError(
            "Branch-and-check lazy constraint callbacks are not supported by the Jaxipm backend "
            "(jaxipm solves continuous LPs only; it cannot be a master/MIP backend)."
        )

    def _cb_get_obj(self):
        raise BendersNotImplementedError("Callback query is not supported for the Jaxipm backend.")

    def _cb_get_bound(self):
        raise BendersNotImplementedError("Callback query is not supported for the Jaxipm backend.")

    def _cb_get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        raise BendersNotImplementedError("Callback query is not supported for the Jaxipm backend.")

    def _cb_add_cut(self, cut) -> None:
        raise BendersNotImplementedError("Callback cut addition is not supported for the Jaxipm backend.")

    def compute_iis(self) -> set[str]:
        raise BendersNotImplementedError("compute_iis is not supported for the Jaxipm backend.")

    @staticmethod
    def make_master_problem(original_model: dict, master_vars: list[str]) -> dict:
        raise BendersNotImplementedError(
            "The Jaxipm backend only supports continuous LP subproblems, and cannot be used "
            "to build/solve a master problem. Model the overall problem and its master problem "
            "in a MIP-capable backend (e.g. Gurobi, Copt, Scip, Pyomo), and convert only the "
            "subproblem to Jaxipm via cross-backend model exchange, e.g.: "
            "Jaxipm.from_structured(Gurobi(Gurobi.make_sub_problem(original_model, master_vars)).to_structured())."
        )

    @staticmethod
    def make_sub_problem(original_model: dict, master_vars: list[str]) -> dict:
        """Create a subproblem structured-dict model from a native structured-dict model.

        Master variables are kept as continuous variables (to be fixed later via
        :meth:`fix_vars`) with their objective coefficient zeroed out. Constraints that
        involve only master variables are dropped, mirroring the other backends'
        :meth:`~benderslib.solvers.SolverBase.make_sub_problem`.
        """
        sub = copy.deepcopy(original_model)
        master_set = set(master_vars)

        for v in sub['vars']:
            if v['name'] in master_set:
                v['vtype'] = 'C'
                v['obj'] = 0.0

        sub['constraints'] = [
            c for c in sub['constraints']
            if not (c['coefs'] and set(c['coefs'].keys()) <= master_set)
        ]
        sub['qobj'] = [
            q for q in sub.get('qobj', [])
            if q['vars'][0] not in master_set and q['vars'][1] not in master_set
        ]
        return sub

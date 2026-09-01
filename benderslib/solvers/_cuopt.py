# coding:utf-8
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2021-2026 Peng-Hui Guo <m@guo.ph>

import math
import copy
import warnings
from cuopt.linear_programming.problem import (
    Problem,
    LinearExpression,
    CONTINUOUS,
    INTEGER,
    MINIMIZE,
)
from cuopt.linear_programming.solver_settings import SolverSettings

from ..consts import BendersConsts as CST
from ._base import SolverBase
from ..errors import BendersNotImplementedError, MismatchedProbabilityError, BendersBackendError


def _get_var_name(var) -> str:
    if hasattr(var, 'VariableName') and var.VariableName:
        return var.VariableName
    if hasattr(var, 'Name') and var.Name:
        return var.Name
    return f"x{var.index}"


def _get_cons_name(cons) -> str:
    if hasattr(cons, 'ConstraintName') and cons.ConstraintName:
        return cons.ConstraintName
    if hasattr(cons, 'Name') and cons.Name:
        return cons.Name
    return f"c{cons.index}"


def _get_sense_char(cons) -> str:
    """Return the constraint sense as one of 'L', 'G', 'E'."""
    sense = getattr(cons, 'Sense', None)
    if sense is None:
        return 'L'
    value = getattr(sense, 'value', sense)
    return str(value)


def _invalidate(problem) -> None:
    """Force a full DataModel rebuild on the next solve.

    Handles both released (26.08) and development versions of cuOpt.
    """
    # 26.08: update() -> reset_solved_values() clears model, csr cache, warm start
    if hasattr(problem, 'update'):
        try:
            problem.update()
        except Exception:
            pass
    # Development branch: explicit cache invalidation + stale marking
    if hasattr(problem, '_invalidate_problem_cache'):
        try:
            problem._invalidate_problem_cache()
        except Exception:
            pass
    # Belt and braces for any version
    if hasattr(problem, 'constraint_csr_matrix'):
        problem.constraint_csr_matrix = None
    if hasattr(problem, 'model'):
        problem.model = None
    if hasattr(problem, 'warmstart_data'):
        problem.warmstart_data = None
    if hasattr(problem, 'solved'):
        problem.solved = False


class Cuopt(SolverBase):
    """NVIDIA cuOpt solver interface for BendersLib.

    This class provides an interface to the NVIDIA cuOpt GPU-accelerated LP/MILP solver
    for use with BendersLib.

    .. note::
        cuOpt does not expose Farkas infeasibility certificates. When a subproblem is
        infeasible, :meth:`get_extreme_ray` solves an auxiliary elastic (phase-1)
        LP that minimizes the total constraint violation, and derives the ray from
        its optimal dual values. This yields valid Benders feasibility cuts.

    .. admonition:: Recommended usage: hybrid solving (CPU master + GPU batched subs)
        :class: note

        cuOpt's strengths in Benders decomposition are **fast batched LP solving on the
        GPU** (see :attr:`~benderslib.BendersParams.batch_sub`), not repeatedly solving
        the small master MILP. Each cuOpt MIP solve pays a large fixed cost
        (presolve, early heuristics, and post-solve reconstruction) that dwarfs the
        actual branch-and-bound time on master-sized models.

        The recommended pattern is therefore to pair cuOpt **subproblems** with a CPU
        MIP **master** backend such as :class:`~benderslib.solvers.Scip`::

            from benderslib import LShaped, MasterProblem, SubProblem, SubProblems
            from benderslib.solvers import Cuopt, Scip

            L = LShaped(
                master_problem=MasterProblem(Scip(scip_master_model)),
                sub_problem=SubProblems([SubProblem(Cuopt(cuopt_sub_model)) for ...]),
                complicating_vars=[...],
            )
            L.params.batch_sub = True  # dispatch all scenario LPs to cuOpt in one batch

        For single-problem workflows, :class:`~benderslib.AnnotatedBenders` supports this
        directly via its ``master_solver`` parameter. In our benchmarks this hybrid
        pattern reduced the L-shaped solve time by **~8.5x** compared to a pure-cuOpt run,
        with identical results.

    Parameters
    ---------------
    model: cuopt.linear_programming.problem.Problem
        An instance of cuOpt's ``Problem``.
    solver_options: dict, optional
        A dictionary of solver-specific options for ``SolverSettings``.
    """

    def __init__(self, model: Problem, solver_options: dict = None) -> None:
        super().__init__(model)

        self.model = model
        self.status = CST.UNSOLVED

        vars_list = self.model.vars
        self._vars_map = {_get_var_name(v): v for v in vars_list}
        self._cons_map = {_get_cons_name(c): c for c in self.model.constrs}

        # Objective sense
        sense = getattr(self.model, 'ObjSense', MINIMIZE)
        self._sense = CST.MIN if sense == MINIMIZE or sense == 1 else CST.MAX

        self._all_vars = list(self._vars_map.keys())

        # Categorize variable types
        self._bin_vars = []
        self._int_vars = []
        for name, var in self._vars_map.items():
            vtype = var.getVariableType()
            lb = var.getLowerBound()
            ub = var.getUpperBound()
            if vtype == INTEGER:
                if lb == 0.0 and ub == 1.0:
                    self._bin_vars.append(name)
                else:
                    self._int_vars.append(name)

        # Record non-trivial bounds (i.e. lb != 0 or ub != inf)
        self._var_bounds = {}
        for name, var in self._vars_map.items():
            lb = var.getLowerBound()
            ub = var.getUpperBound()
            if lb != 0.0 or (ub != float('inf') and ub < 1e20):
                self._var_bounds[name] = (lb, ub)

        self.__standardize()
        self._rhs = self.get_rhs()
        self._constr_num = len(self.model.constrs)

        self.settings = SolverSettings()
        self.__setup_model(solver_options)

    def __standardize(self):
        self.__sense_to_minimize()
        self.__bounds_to_constrs()

    def __sense_to_minimize(self):
        if self._sense == CST.MAX:
            raise BendersNotImplementedError("BendersLib currently only supports minimization problems.")

    def __bounds_to_constrs(self):
        if any([lb < 0 or ub < 0 for lb, ub in self._var_bounds.values()]):
            raise BendersNotImplementedError("BendersLib currently only supports non-negative variable bounds.")

        # Convert variable bounds to explicit linear constraints
        for var_name, (lb, ub) in self._var_bounds.items():
            var = self._vars_map[var_name]
            if lb > 0:
                c_name = f"__{var_name}_lb"
                c = self.model.addConstraint(var >= lb, name=c_name)
                self._cons_map[c_name] = c
                var.setLowerBound(0.0)
            if ub < float('inf') and ub < 1e20:
                c_name = f"__{var_name}_ub"
                c = self.model.addConstraint(var <= ub, name=c_name)
                self._cons_map[c_name] = c
                var.setUpperBound(float('inf'))

    def __setup_model(self, solver_options: dict = None):
        _options = self._options.get('CUOPT_OPTIONS', {})
        solver_options = solver_options or {}
        _options.update(solver_options)

        for option, value in _options.items():
            try:
                self.settings.set_parameter(option, value)
            except Exception:
                pass

    def add_estimators(self, estimators: list[str], prob: list[float] = None, lb: float = 0) -> None:
        if prob is None:
            if len(estimators) == 1:
                prob = [1.0]
            else:
                prob = [1.0 / len(estimators)] * len(estimators)
        else:
            if len(prob) != len(estimators):
                raise MismatchedProbabilityError("Length of <prob> must match length of <estimators>.")

        for var_name, obj_coef in zip(estimators, prob):
            var = self.model.addVariable(lb=lb, obj=obj_coef, vtype=CONTINUOUS, name=var_name)
            self._vars_map[var_name] = var
            self._all_vars.append(var_name)

        _invalidate(self.model)

    def fix_vars(self, var_values: dict[str, float]) -> None:
        for var_name, var_value in var_values.items():
            var = self._vars_map[var_name]
            var.setLowerBound(float(var_value))
            var.setUpperBound(float(var_value))

    def unfix_vars(self, vars: list[str]) -> None:
        for var_name in vars:
            var = self._vars_map[var_name]
            lb, _ = self._var_bounds.get(var_name, (0.0, float('inf')))
            # Original bounds were converted to explicit constraints during standardization,
            # so the variable itself is restored to [0, +inf) (or its original non-positive lb).
            var.setLowerBound(0.0 if lb > 0 else float(lb))
            var.setUpperBound(float('inf'))

    def get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        vars_to_get = vars or self._all_vars
        return {var_name: float(self._vars_map[var_name].getValue()) for var_name in vars_to_get}

    def get_var_coefs(self, vars: list[str] | None = None) -> dict[str, list]:
        target_vars = vars or self._all_vars
        constrs = self.model.constrs
        res = {v: [] for v in target_vars}

        for cons in constrs:
            for v_name in target_vars:
                var = self._vars_map.get(v_name)
                coef = 0.0
                if var is not None and hasattr(cons, 'vindex_coeff_dict'):
                    coef = cons.vindex_coeff_dict.get(var.index, 0.0)
                res[v_name].append(float(coef))

        return res

    def get_rhs(self) -> list[float]:
        constrs = self.model.constrs
        return [float(c.getRHS()) for c in constrs]

    def get_dual_values(self) -> list[float]:
        constrs = self.model.constrs
        duals = []
        for c in constrs:
            val = getattr(c, 'DualValue', float('nan'))
            if math.isnan(val):
                val = 0.0
            duals.append(float(val))
        return duals

    def get_extreme_ray(self) -> list[float]:
        """Derive a Farkas-type infeasibility certificate via an elastic phase-1 LP.

        cuOpt does not expose dual Farkas rays. Instead, we solve:

            min  sum(s)
            s.t. a_i' x + s_i >= b_i   (for >= rows)
                 a_i' x - s_i <= b_i   (for <= rows)
                 a_i' x + s_i - t_i == b_i  (for == rows)
                 x within variable bounds, s, t >= 0

        The negated optimal duals of this LP form a valid extreme ray
        (matching the Gurobi FarkasDual sign convention used by BendersLib).
        """
        phase1 = Problem(f"{getattr(self.model, 'Name', 'model')}__phase1")

        # Clone variables (continuous, zero objective, same working bounds)
        var_map = {}
        for v in self.model.vars:
            var_map[v.index] = phase1.addVariable(
                lb=float(v.getLowerBound()),
                ub=float(v.getUpperBound()),
                obj=0.0,
                vtype=CONTINUOUS,
                name=_get_var_name(v),
            )

        # Clone constraints with elastic variables
        p1_constrs = []
        for c in self.model.constrs:
            expr_vars = []
            expr_coefs = []
            for v_idx, coef in c.vindex_coeff_dict.items():
                expr_vars.append(var_map[v_idx])
                expr_coefs.append(float(coef))

            sense_char = _get_sense_char(c)
            rhs = float(c.getRHS())
            c_name = f"__p1_{c.index}"

            if sense_char == 'G':
                s = phase1.addVariable(lb=0.0, obj=1.0, vtype=CONTINUOUS)
                expr = LinearExpression(expr_vars + [s], expr_coefs + [1.0], 0.0)
                pc = phase1.addConstraint(expr >= rhs, name=c_name)
            elif sense_char == 'L':
                s = phase1.addVariable(lb=0.0, obj=1.0, vtype=CONTINUOUS)
                expr = LinearExpression(expr_vars + [s], expr_coefs + [-1.0], 0.0)
                pc = phase1.addConstraint(expr <= rhs, name=c_name)
            else:  # 'E'
                sp = phase1.addVariable(lb=0.0, obj=1.0, vtype=CONTINUOUS)
                sn = phase1.addVariable(lb=0.0, obj=1.0, vtype=CONTINUOUS)
                expr = LinearExpression(expr_vars + [sp, sn], expr_coefs + [1.0, -1.0], 0.0)
                pc = phase1.addConstraint(expr == rhs, name=c_name)

            p1_constrs.append(pc)

        # Solve the elastic LP
        p1_settings = SolverSettings()
        for option, value in self._options.get('CUOPT_OPTIONS', {}).items():
            try:
                p1_settings.set_parameter(option, value)
            except Exception:
                pass

        phase1.solve(p1_settings)

        status_name = phase1.Status.name if hasattr(phase1.Status, 'name') else str(phase1.Status)
        if status_name not in ('Optimal', 'PrimalFeasible'):
            raise BendersBackendError(
                f"Phase-1 elastic LP for Farkas ray extraction terminated with status <{status_name}>."
            )

        # Negate duals to match the Gurobi FarkasDual sign convention
        ray = []
        for pc in p1_constrs:
            val = getattr(pc, 'DualValue', float('nan'))
            if math.isnan(val):
                val = 0.0
            ray.append(-float(val))
        return ray

    def get_obj(self) -> float:
        return float(self.model.ObjValue)

    def to_structured(self) -> dict:
        """Serialize the cuOpt model into a solver-agnostic structured representation.

        See :meth:`~benderslib.solvers.SolverBase.to_structured` for the format.
        This makes ``Cuopt`` usable as the **source** of a cross-backend model exchange,
        e.g., to rebuild a cuOpt-built master problem as a SCIP model for the
        recommended hybrid solving pattern (see the class docstring).
        """
        vars_ = []
        for v in self.model.vars:
            name = _get_var_name(v)
            ub = float(v.getUpperBound())
            vars_.append({
                'name': name,
                'lb': float(v.getLowerBound()),
                'ub': ub if ub < 1e20 else float('inf'),
                'vtype': 'I' if v.getVariableType() == INTEGER else 'C',
                'obj': float(v.getObjectiveCoefficient()),
            })

        idx_to_name = {v.index: _get_var_name(v) for v in self.model.vars}
        cons_ = []
        for c in self.model.constrs:
            cons_.append({
                'name': _get_cons_name(c),
                'sense': _get_sense_char(c),
                'rhs': float(c.getRHS()),
                'coefs': {idx_to_name[i]: float(coef) for i, coef in c.vindex_coeff_dict.items()},
            })

        return {'sense': 'min', 'vars': vars_, 'constraints': cons_}

    @classmethod
    def from_structured(cls, structured: dict) -> Problem:
        """Build a cuOpt ``Problem`` from a solver-agnostic structured representation.

        See :meth:`~benderslib.solvers.SolverBase.from_structured`. This makes ``Cuopt``
        usable as a batching **target**: subproblems built in any backend that implements
        :meth:`~benderslib.solvers.SolverBase.to_structured` (e.g., Gurobi, COPT, Pyomo, SCIP)
        can be converted to cuOpt models and solved together via
        :meth:`batch_solve` / :attr:`~benderslib.BendersParams.batch_sub` on the GPU.
        See :meth:`~benderslib.SubProblems.from_models` for a ready-made convenience.

        Parameters
        ---------------
        structured : dict
            The structured representation produced by
            :meth:`~benderslib.solvers.SolverBase.to_structured`.

        Returns
        ---------------
        cuopt.linear_programming.problem.Problem
            A native cuOpt model equivalent to the source model.
        """
        model = Problem(structured.get('name', 'StructuredProblem'))

        var_map = {}
        obj_terms = []
        for v in structured.get('vars', []):
            vtype = INTEGER if v.get('vtype', 'C') == 'I' else CONTINUOUS
            var = model.addVariable(
                lb=v.get('lb', 0.0),
                ub=v.get('ub', float('inf')),
                vtype=vtype,
                name=v['name'],
            )
            var_map[v['name']] = var
            obj_coef = float(v.get('obj', 0.0))
            if obj_coef:
                obj_terms.append(obj_coef * var)

        if obj_terms:
            model.setObjective(sum(obj_terms), sense=MINIMIZE)

        for c in structured.get('constraints', []):
            expr_vars = [var_map[name] for name in c['coefs'].keys()]
            expr_coefs = [float(coef) for coef in c['coefs'].values()]
            expr = LinearExpression(expr_vars, expr_coefs, 0.0)
            rhs = float(c['rhs'])
            sense = c.get('sense', 'G')
            name = c.get('name') or ''
            if sense == 'L':
                model.addConstraint(expr <= rhs, name=name)
            elif sense == 'E':
                model.addConstraint(expr == rhs, name=name)
            else:
                model.addConstraint(expr >= rhs, name=name)

        return model

    def add_cut(self, cut, name=None) -> None:
        expr = sum(coef * self._vars_map[var] for var, coef in zip(cut.vars, cut.coefs))

        if cut.sense == CST.EQ:
            c = self.model.addConstraint(expr == cut.rhs, name=name or "")
        elif cut.sense == CST.LE:
            c = self.model.addConstraint(expr <= cut.rhs, name=name or "")
        elif cut.sense == CST.GE:
            c = self.model.addConstraint(expr >= cut.rhs, name=name or "")
        else:
            raise BendersBackendError(f"Unsupported cut sense: {cut.sense}")

        if name:
            self._cons_map[name] = c

        _invalidate(self.model)

    def remove_cut(self, cut_name: str) -> None:
        if cut_name in self._cons_map:
            c = self._cons_map.pop(cut_name)
            if c in self.model.constrs:
                self.model.constrs.remove(c)
                for idx, constr in enumerate(self.model.constrs):
                    constr.index = idx
                _invalidate(self.model)

    def solve(self) -> None:
        _invalidate(self.model)
        self.model.solve(self.settings)
        status_name = self.model.Status.name if hasattr(self.model.Status, 'name') else str(self.model.Status)
        self._update_status('CUOPT', status_name)

    @classmethod
    def batch_solve(cls, instances: list['Cuopt'], solver_options: dict = None) -> None:
        """Solve a list of Cuopt LP subproblem instances concurrently via cuOpt's ``BatchSolve``.

        .. warning::
            This relies on NVIDIA cuOpt's ``BatchSolve`` API, which
            `NVIDIA has deprecated and scheduled for removal <https://github.com/NVIDIA/cuopt>`_
            in a future release. Per NVIDIA's own documentation, it dispatches concurrent LP
            solves across multiple **C++ threads** (not a single fused GPU kernel), and is
            documented for **LP problems only**. If any instance's model is a MIP, this method
            automatically falls back to sequential :meth:`solve` calls, matching NVIDIA's own
            recommended migration path for when ``BatchSolve`` is removed.

        Parameters
        ---------------
        instances : list[Cuopt]
            List of Cuopt solver instances to solve. All must have LP (non-MIP) models to use
            the batched code path; if any is a MIP, this falls back to sequential solving.
        solver_options : dict, optional
            Solver options to override default settings for the batch.
        """
        if not instances:
            return

        # cuOpt's BatchSolve is documented for LP only; fall back safely for MIP models.
        if any(getattr(inst.model, 'IsMIP', False) for inst in instances):
            for inst in instances:
                inst.solve()
            return

        from cuopt.linear_programming.solver import BatchSolve

        first_inst = instances[0]
        settings = SolverSettings()
        _options = first_inst._options.get('CUOPT_OPTIONS', {}).copy()
        if solver_options:
            _options.update(solver_options)

        for option, value in _options.items():
            try:
                settings.set_parameter(option, value)
            except Exception:
                pass

        data_models = []
        for inst in instances:
            _invalidate(inst.model)
            if inst.model.model is None:
                inst.model._to_data_model()
            data_models.append(inst.model.model)

        # Suppress NVIDIA's known BatchSolve DeprecationWarning; the risk is documented above
        # and in BendersParams.batch_sub, rather than re-emitted on every Benders iteration.
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*BatchSolve.*", category=DeprecationWarning)
            solutions, _ = BatchSolve(data_models, settings)

        for inst, sol in zip(instances, solutions):
            inst.model.populate_solution(sol)
            status_name = inst.model.Status.name if hasattr(inst.model.Status, 'name') else str(inst.model.Status)
            inst._update_status('CUOPT', status_name)

    def _bnc_solve(self, callback_handler) -> None:
        raise BendersNotImplementedError(
            "Branch-and-check lazy constraint callbacks are not currently supported by the cuOpt solver backend. "
            "Please use the standard iterative Benders decomposition algorithm."
        )

    def _cb_get_obj(self):
        raise BendersNotImplementedError("Callback query is not supported for cuOpt backend.")

    def _cb_get_bound(self):
        raise BendersNotImplementedError("Callback query is not supported for cuOpt backend.")

    def _cb_get_var_values(self, vars: list[str] | None = None) -> dict[str, float]:
        raise BendersNotImplementedError("Callback query is not supported for cuOpt backend.")

    def _cb_add_cut(self, cut) -> None:
        raise BendersNotImplementedError("Callback cut addition is not supported for cuOpt backend.")

    def compute_iis(self) -> set[str]:
        raise BendersNotImplementedError("compute_iis is not supported for cuOpt backend.")

    @staticmethod
    def make_master_problem(original_model: Problem, master_vars: list[str]) -> Problem:
        """Create master problem from native cuOpt problem."""
        master = copy.deepcopy(original_model)
        _invalidate(master)

        non_master_vars = [v for v in master.vars if _get_var_name(v) not in master_vars]
        non_master_indices = set(v.index for v in non_master_vars)

        constrs_to_keep = []
        for c in master.constrs:
            has_non_master = any(v_idx in non_master_indices for v_idx in c.vindex_coeff_dict.keys())
            if not has_non_master:
                constrs_to_keep.append(c)

        master.constrs = constrs_to_keep
        for i, c in enumerate(master.constrs):
            c.index = i
            c._problem = master

        vars_to_keep = [v for v in master.vars if v.index not in non_master_indices]
        old_to_new_idx = {v.index: new_idx for new_idx, v in enumerate(vars_to_keep)}
        master.vars = vars_to_keep
        for new_idx, v in enumerate(master.vars):
            v.index = new_idx
            v._problem = master

        for c in master.constrs:
            new_dict = {}
            for old_v_idx, coeff in c.vindex_coeff_dict.items():
                if old_v_idx in old_to_new_idx:
                    new_dict[old_to_new_idx[old_v_idx]] = coeff
            c.vindex_coeff_dict = new_dict
            c.vars = [master.vars[new_idx] for new_idx in new_dict.keys()]

        return master

    @staticmethod
    def make_sub_problem(original_model: Problem, master_vars: list[str]) -> Problem:
        """Create subproblem from native cuOpt problem."""
        sub = copy.deepcopy(original_model)
        _invalidate(sub)

        master_indices = set(v.index for v in sub.vars if _get_var_name(v) in master_vars)

        for v in sub.vars:
            if v.index in master_indices:
                v.setVariableType(CONTINUOUS)
                v.setObjectiveCoefficient(0.0)

        constrs_to_keep = []
        for c in sub.constrs:
            is_only_master = len(c.vindex_coeff_dict) > 0 and all(v_idx in master_indices for v_idx in c.vindex_coeff_dict.keys())
            if not is_only_master:
                constrs_to_keep.append(c)

        sub.constrs = constrs_to_keep
        for i, c in enumerate(sub.constrs):
            c.index = i
            c._problem = sub

        return sub

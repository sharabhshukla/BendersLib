# coding:utf-8

from ..consts import BendersConsts as CST
from ..core import CutGenerator
from .cuts import (
    ClassicalOC,
    ClassicalFC,
    NoGoodFC,
    CombinatorialOC,
    LShapedOC,
    GeneralizedOC,
    GeneralizedFC,
    GeneLShapedOC,
)


class ClassicalOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/classical`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self._complicating_vars)
        self.rhs = sub_problem.get_rhs()

    def generate(self) -> list[ClassicalOC]:
        """
        This method generates :class:`ClassicalOC` optimality cuts based on the current solution
        of the master problem and the dual values obtained from the subproblem.
        """
        dual_values = self._sub_problem.get_dual_values()

        cut = ClassicalOC(self._complicating_vars, self.var_coefs, dual_values, self.rhs)
        return [cut]


class ClassicalFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/classical`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self._complicating_vars)
        self.rhs = sub_problem.get_rhs()

    def generate(self) -> list[ClassicalFC]:
        """
        This method generates :class:`ClassicalFC` feasibility cuts based on the current solution
        of the master problem and the extreme ray obtained from the subproblem.
        """
        extreme_ray = self._sub_problem.get_extreme_ray()

        cut = ClassicalFC(self._complicating_vars, self.var_coefs, extreme_ray, self.rhs)
        return [cut]


class CombinatorialFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/cbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[NoGoodFC]:
        """
        This method generates :class:`NoGoodFC` feasibility cuts based on the current solution
        of the master problem.
        """
        var_values = self._master_problem.get_var_values(self._complicating_vars)

        cut = NoGoodFC(var_values)
        return [cut]


class CombinatorialOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/cbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[CombinatorialOC]:
        """
        This method generates :class:`CombinatorialOC` optimality cuts based on the current solution
        of the master problem and the objective value obtained from the subproblem.
        """
        var_values = self._master_problem.get_var_values(self._complicating_vars)
        sub_obj = self._sub_problem.get_obj()
        estimator = self._master_problem.estimators[0]
        theta_lb = self._master_problem.get_estimator_values()[estimator]

        cut = CombinatorialOC(var_values, sub_obj, big_m=sub_obj - theta_lb)
        return [cut]


class LShapedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/lshape` (linear recourse)."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = dict()
        self.rhs = dict()

        for i, sub in enumerate(self._sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self._complicating_vars)
            self.rhs[i] = sub.get_rhs()

    def _single_cut(self) -> list[LShapedOC]:
        """
        This method generates a single :class:`LShapedOC` optimality cut aggregating all subproblems (scenarios).
        """
        complicating_vars = self._complicating_vars

        all_probs = []
        all_duals = []
        all_rhss = []
        all_var_coefs = []
        for i, sub in enumerate(self._sub_problem):
            all_probs.append(self._sub_problem.prob[i])
            all_duals.append(sub.get_dual_values())
            all_rhss.append(self.rhs[i])
            all_var_coefs.append(self.var_coefs[i])

        cut = LShapedOC(complicating_vars, all_probs, all_duals, all_rhss, all_var_coefs)
        return [cut]

    def _multi_cuts(self) -> list[ClassicalOC]:
        """
        This method generates multiple :class:`ClassicalOC` optimality cuts, one for each subproblem (scenario).
        """
        cuts = []
        for i, sub in enumerate(self._sub_problem):
            _var_coefs = self.var_coefs[i]
            _rhs = self.rhs[i]
            _dual = sub.get_dual_values()

            vars = self._complicating_vars
            estimator = self._master_problem.estimators[i]

            # Add the cut only if it is violated
            if sub.get_obj() - self._master_problem.get_estimator_values()[estimator] > self.params.tol_obj_diff:
                cut = ClassicalOC(vars, _var_coefs, _dual, _rhs, estimator=estimator)
                cuts.append(cut)

        return cuts

    def generate(self) -> list[ClassicalOC] | list[LShapedOC]:
        """
        This method generates optimality cuts based on the current solution
        of the master problem and the dual values obtained from the subproblems.
        If :attr:`BendersParams.multi_opti_cut` is ``True``, :func:`_multi_cuts` is called to generate multiple cuts;
        otherwise, :func:`_single_cut` is called to generate a single aggregated cut.
        """
        return self._multi_cuts() if self.params.multi_opti_cut else self._single_cut()


class LShapedFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/lshape`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = dict()
        self.rhs = dict()

        for i, sub in enumerate(self._sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self._complicating_vars)
            self.rhs[i] = sub.get_rhs()

    def generate(self) -> list[ClassicalFC]:
        """
        This method generates :class:`ClassicalFC` feasibility cuts based on the current solution
        of the master problem and the extreme rays obtained from the subproblems.
        """
        cuts = []

        for i, sub in enumerate(self._sub_problem):
            if sub.status == CST.INFEASIBLE:
                _var_coefs = self.var_coefs[i]
                _rhs = self.rhs[i]
                _extreme_ray = sub.get_extreme_ray()

                cut = ClassicalFC(self._complicating_vars, _var_coefs, _extreme_ray, _rhs)
                cuts.append(cut)
                if not self.params.multi_feas_cut:
                    break

        return cuts


class IntegerLShapedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/ilshape`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def _single_cut(self) -> list[CombinatorialOC]:
        """
        This method generates a single :class:`CombinatorialOC` optimality cut aggregating all subproblems (scenarios).
        """
        bin_var_values = self._master_problem.get_var_values(self._complicating_vars)
        sub_obj = self._sub_problem.get_obj()
        estimator = self._master_problem.estimators[0]
        theta_lb = self._master_problem.get_estimator_values()[estimator]

        cut = CombinatorialOC(bin_var_values, sub_obj, big_m=sub_obj - theta_lb, estimator=estimator)
        return [cut]

    def _multi_cuts(self) -> list[CombinatorialOC]:
        """
        This method generates multiple :class:`CombinatorialOC` optimality cuts, one for each subproblem (scenario).
        """
        cuts = []

        for i, sub in enumerate(self._sub_problem):
            bin_var_values = self._master_problem.get_var_values(self._complicating_vars)
            sub_obj = sub.get_obj()
            estimator = self._master_problem.estimators[i]
            theta = self._master_problem.get_estimator_values()[estimator]

            # Add the cut only if it is violated
            if sub_obj - theta > self.params.tol_obj_diff:
                cut = CombinatorialOC(bin_var_values, sub_obj, big_m=sub_obj - theta, estimator=estimator)
                cuts.append(cut)

        return cuts

    def generate(self):
        """
        This method generates optimality cuts based on the current values of binary complicating variables
        in the master problem and the objective values obtained from the subproblems.
        If :attr:`BendersParams.multi_opti_cut` is ``True``, :func:`_multi_cuts` is called to generate multiple cuts;
        otherwise, :func:`_single_cut` is called to generate a single aggregated cut.
        """
        return self._multi_cuts() if self.params.multi_opti_cut else self._single_cut()


class IntegerLShapedFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/ilshape`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

    def generate(self) -> list[NoGoodFC]:
        """
        This method generates :class:`NoGoodFC` feasibility cuts based on the current values of binary
        complicating variables in the master problem.
        """
        bin_var_values = self._master_problem.get_var_values(self._complicating_vars)
        cut = NoGoodFC(bin_var_values)

        return [cut]


class GeneralizedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/gbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self._complicating_vars)

    def generate(self) -> list[GeneralizedOC]:
        """This method generates :class:`GeneralizedOC` optimality cuts."""
        sub_obj = self._sub_problem.get_obj()
        lagrange_multipliers = self._sub_problem.get_dual_values()
        master_vars_values = self._master_problem.get_var_values(self._complicating_vars)

        cut = GeneralizedOC(
            self._complicating_vars,
            master_vars_values,
            self.var_coefs,
            sub_obj,
            lagrange_multipliers,
        )
        return [cut]


class GeneralizedFCGen(CutGenerator):
    """The feasibility cut generator for :doc:`../tutorials/gbd`."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = sub_problem.get_var_coefs(self._complicating_vars)
        self.rhs = sub_problem.get_rhs()

    def generate(self) -> list[ClassicalFC]:
        """This method generates :class:`GeneralizedFC` feasibility cuts."""
        extreme_ray = self._sub_problem.get_extreme_ray()

        cut = GeneralizedFC(self._complicating_vars, self.var_coefs, extreme_ray, self.rhs)
        return [cut]


class GeneLShapedOCGen(CutGenerator):
    """The optimality cut generator for :doc:`../tutorials/lshape` (convex recourse)."""

    def __init__(self, master_problem, sub_problem, params):
        super().__init__(master_problem, sub_problem, params)

        self.var_coefs = dict()
        for i, sub in enumerate(self._sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self._complicating_vars)

    def _single_cut(self) -> list[GeneLShapedOC]:
        """Generates a single aggregated :class:`GeneLShapedOC` from all scenarios."""
        complicating_vars = self._complicating_vars
        var_values = self._master_problem.get_var_values(complicating_vars)

        all_probs = []
        all_sub_objs = []
        all_multipliers = []
        all_var_coefs = []

        for i, sub in enumerate(self._sub_problem):
            all_probs.append(self._sub_problem.prob[i])
            all_sub_objs.append(sub.get_obj())
            all_multipliers.append(sub.get_dual_values())
            all_var_coefs.append(self.var_coefs[i])

        cut = GeneLShapedOC(
            complicating_vars,
            all_probs,
            var_values,
            all_var_coefs,
            all_sub_objs,
            all_multipliers,
        )
        return [cut]

    def _multi_cuts(self) -> list[GeneralizedOC]:
        """Generates multiple :class:`GeneralizedOC` cuts, one for each subproblem (scenario)."""
        cuts = []
        var_values = self._master_problem.get_var_values(self._complicating_vars)

        for i, sub in enumerate(self._sub_problem):
            estimator = self._master_problem.estimators[i]
            theta = self._master_problem.get_estimator_values()[estimator]
            sub_obj = sub.get_obj()

            # Add the cut only if it is violated
            if sub_obj - theta > self.params.tol_obj_diff:
                cut = GeneralizedOC(
                    vars=self._complicating_vars,
                    var_values=var_values,
                    var_coefs=self.var_coefs[i],
                    sub_obj=sub_obj,
                    multipliers=sub.get_dual_values(),
                    estimator=estimator
                )
                cuts.append(cut)

        return cuts

    def generate(self) -> list[GeneLShapedOC] | list[GeneralizedOC]:
        """Generates optimality cuts for the generalized L-shaped method.

        If :attr:`BendersParams.multi_opti_cut` is ``True``, this method calls :func:`_multi_cuts`
        to generate multiple :class:`GeneralizedOC`, one for each violated scenario;
        If ``False``, it calls :func:`_single_cut` to generate one aggregated
        :class:`GeneLShapedOC` for all scenarios.
        """
        return self._multi_cuts() if self.params.multi_opti_cut else self._single_cut()


if __name__ == '__main__':
    pass

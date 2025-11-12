# coding:utf-8

from .core import OptimalityCut, FeasibilityCut, CutGenerator, CST


class ClassicalOC(OptimalityCut):
    """
    The classical optimality cut for Benders decomposition. Please refer to :doc:`../tutorials/classical`.
    The cut uses the optimal dual solution to form a valid lower bound on the subproblem's cost,
    represented by the variable :math:`\\eta` in the master problem.

    .. math::
        \\eta \\geq \\bar{\\pi}^T (b - A x)

    where :math:`\\eta` is the variable representing the subproblem's cost, :math:`\\bar{\\pi}` is the optimal solution
    to the dual subproblem (dual values of primal constraints), :math:`A` and :math:`b` are the matrices that define
    the subproblem constraints, and :math:`x` are the master problem variables.
    This cut can be interpreted as a first-order Taylor approximation or a supporting hyperplane for the value
    function of the subproblem.

    Parameters
    ----------
    vars : list[str]
        A list of variable names of the complicating variables.
    var_coefs : dict
        A dictionary mapping variable names to their coefficients in the subproblem constraints.
    dual_values : list
        A list of dual variable values obtained from solving the subproblem.
    rhs : list
        A list of right-hand side values of the subproblem constraints.
    """

    def __init__(self, vars: list[str], var_coefs: dict, dual_values: list, rhs: list, estimator=CST.ESTIMATOR_NAME):
        coefs = [sum(a * b for a, b in zip(dual_values, var_coefs)) for var, var_coefs in var_coefs.items()]
        cut_rhs = sum(a * b for a, b in zip(dual_values, rhs))

        super().__init__(vars=vars + [estimator], coefs=coefs + [1.0], rhs=cut_rhs, sense='>=', name="ClassicalOC")


class ClassicalOCGen(CutGenerator):

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


class ClassicalFC(FeasibilityCut):
    """
    The classical feasibility cut for Benders decomposition. Please refer to :doc:`../tutorials/classical`.
    The cut is derived from an extreme ray of the subproblem, which acts as a certificate of infeasibility.
    It is defined as follows to cut off the region of master solutions that leads to this infeasibility.

    .. math::
        0 \\geq \\bar{r}^T (b - A x)

    where :math:`\\bar{r}` is an extreme ray of the dual subproblem, :math:`A` and :math:`b` are the matrices
    that define the subproblem constraints, and :math:`x` are the master problem variables.
    This cut is a direct application of Farkas' Lemma. The extreme ray :math:`\\bar{r}` is typically
    provided by the LP solver when it determines the primal subproblem is infeasible
    (and thus the dual is unbounded). It informs the master problem that any future choice of :math:`x`
    violating this constraint will also result in an infeasible subproblem.

    Parameters
    ----------
    vars : list[str]
        A list of variable names of the complicating variables.
    var_coefs : dict
        A dictionary mapping variable names to their coefficients in the subproblem constraints.
    extreme_ray : list
        A list representing an extreme ray of the subproblem's feasible region.
    rhs : list
        A list of right-hand side values of the subproblem constraints.
    """

    def __init__(self, vars: list[str], var_coefs: dict, extreme_ray: list, rhs: list):
        extreme_ray = [-e for e in extreme_ray]
        coefs = [sum(a * b for a, b in zip(extreme_ray, var_coefs)) for var, var_coefs in var_coefs.items()]
        cut_rhs = sum(a * b for a, b in zip(extreme_ray, rhs))

        # # Even slower when data is small
        # extreme_ray_v = -np.array(extreme_ray)
        # rhs_v = np.array(rhs)
        # coefs_m = np.array(list(var_coefs.values()))
        # coefs = list(coefs_m @ extreme_ray_v)
        # cut_rhs = float(extreme_ray_v @ rhs_v)

        super().__init__(vars=vars, coefs=coefs, rhs=cut_rhs, sense='>=', name="ClassicalFC")


class ClassicalFCGen(CutGenerator):

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


class NoGoodFC(FeasibilityCut):
    """
    The no-good cut (feasibility cut) for Combinatorial Benders Decomposition. Please refer to :doc:`../tutorials/cbd`.
    It is defined as follows to ensure at least one binary variable changes its value in the next iteration,

    .. math::
        \\sum_{i \\in I_1} (1 - x_i) + \\sum_{i \\in I_0} x_i \\geq 1

    where :math:`I_1` is the set of indices of binary variables that are 1 in the current solution,
    and :math:`I_0` is the set of indices of binary variables that are 0 in the current solution.
    It can be rewritten as follows.

    .. math::
        \\sum_{i \\in I_1} x_i - \\sum_{i \\in I_0} x_i \\leq |I_1| - 1

    These two forms can both be found in the literature.
    To make sure the cut is strong, :math:`|I_1 \\cup I_0|` should be **as small as possible**,
    i.e., only including the binary variables that are relevant to the infeasibility of the subproblem,
    which is usually a small subset of all binary variables in the master problem.

    Parameters
    ----------
    bin_var_values : dict
        A dictionary mapping binary variable names to their values in the current master problem solution.
    """

    def __init__(self, bin_var_values: dict):
        var_zeros = [var for var, val in bin_var_values.items() if val <= 0.5]
        var_ones = [var for var, val in bin_var_values.items() if val > 0.5]

        vars = var_ones + var_zeros
        coefs = [1.0] * len(var_ones) + [-1.0] * len(var_zeros)
        rhs = len(var_ones) - 1

        super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='<=', name="NoGoodFC")


class CombinatorialFCGen(CutGenerator):

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


class CombinatorialOC(OptimalityCut):
    """
    The combinatorial optimality cut for Combinatorial Benders Decomposition. Please refer to :doc:`../tutorials/cbd`.
    It is defined as follows to lower bound the estimator :math:`\\theta` for subproblem in the master problem.

    .. math::

        \\theta \\geq z^* - M \\left( \\sum_{i \\in I_1} (1 - x_i) + \\sum_{i \\in I_0} x_i \\right)

    where :math:`z^*` is the objective value of the subproblem given the current master problem solution,
    :math:`I_1` is the set of indices of binary variables that are 1 in the current solution,
    and :math:`I_0` is the set of indices of binary variables that are 0 in the current solution,
    and :math:`M` is a large constant.
    It can be rewritten as follows.

    .. math::
        \\theta - M \\sum_{i \\in I_1} x_i + M \\sum_{i \\in I_0} x_i \\geq z^* - M |I_1|

    To ensure validity, :math:`M` should be larger than the maximum possible objective value of the subproblem.
    If it is not specified, BendersLib set :math:`M = z^* - L` in each iteration,
    where :math:`L = \\bar{\\theta}` is a known lower bound on :math:`\\theta`,
    retrieved from the master problem in the current iteration.
    The cut is rewritten as follows.

    .. math::
        \\frac{\\theta}{z^* - L} - \\sum_{i \\in I_1} x_i + \\sum_{i \\in I_0} x_i \\geq \\frac{z^*}{z^* - L} - |I_1|

    This form is used when :math:`z^* - L \\neq 0` to improve the numerical stability.

    Parameters
    ----------
    bin_var_values : dict
        A dictionary mapping binary variable names to their values in the current master problem solution.
    sub_obj : float
        The objective value of the subproblem given the current master problem solution.
    big_m : float, optional, default=sub_obj
        A large constant used in the cut formulation.
    estimator : str, optional
        The name of the master problem variable representing the future cost.
    """

    def __init__(
            self,
            bin_var_values: dict,
            sub_obj: float,
            big_m: float = None,
            estimator: str = CST.ESTIMATOR_NAME
    ):
        var_zeros = [var for var, val in bin_var_values.items() if val <= 0.5]
        var_ones = [var for var, val in bin_var_values.items() if val > 0.5]
        big_m = sub_obj if big_m is None else big_m

        if big_m == 0:
            # Form 1
            vars = [estimator] + var_ones + var_zeros
            coefs = [1.0] + [-big_m] * len(var_ones) + [big_m] * len(var_zeros)
            rhs = sub_obj - big_m * len(var_ones)
        else:
            # Form 2: same number of cuts, but faster to solve the master problem
            vars = [estimator] + var_ones + var_zeros
            coefs = [1.0 / big_m] + [-1.0] * len(var_ones) + [1.0] * len(var_zeros)
            rhs = sub_obj / big_m - len(var_ones)

        super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='>=', name="CombinatorialCut")


class CombinatorialOCGen(CutGenerator):

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


class LShapedOC(OptimalityCut):
    """
    An aggregated optimality cut for the :doc:`../tutorials/lshape` (single-cut version).
    This class encapsulates the aggregation logic. It takes raw data from all
    scenarios (probabilities, duals, matrices) and computes the final cut.
    The cut represents the following inequality.

    .. math::
        \\theta \\geq \\sum_{\\omega} p_\\omega [\\pi_\\omega^T (h_\\omega - T_\\omega x)]

    Parameters
    ----------
    vars : list[str]
        A list of variable names for the complicating variables :math:`x`.
    probs : list[float]
        A list of probabilities for each scenario :math:`p_\\omega`.
    duals : list[list[float]]
        A list of lists, where each inner list contains the dual variable values :math:`\\pi_\\omega^T` for a scenario.
    rhss : list[list[float]]
        A list of lists, where each inner list is the right-hand side :math:`h_ω` for a scenario.
    var_coefs_list : list[dict]
        A list of dictionaries. Each dictionary maps variable names to their
        coefficient lists :math:`T_ω` for a scenario.
    estimator : str
        The name of the master problem variable representing the future cost.
    """

    def __init__(
            self,
            vars: list[str],
            probs: list[float],
            duals: list[list[float]],
            rhss: list[list[float]],
            var_coefs_list: list[dict],
            estimator=CST.ESTIMATOR_NAME
    ):

        aggregated_rhs = 0.0
        aggregated_x_coefs_dict = {var: 0.0 for var in vars}

        for i in range(len(probs)):
            prob = probs[i]
            dual_values = duals[i]
            rhs_values = rhss[i]
            scenario_var_coefs = var_coefs_list[i]

            # Right-hand side
            scenario_rhs = sum(d * r for d, r in zip(dual_values, rhs_values))
            aggregated_rhs += prob * scenario_rhs

            # Complicating variable coefficients
            for var_name in vars:
                coef_sum = sum(d * c for d, c in zip(dual_values, scenario_var_coefs[var_name]))
                aggregated_x_coefs_dict[var_name] += prob * coef_sum

        final_aggregated_x_coefs = [aggregated_x_coefs_dict[var] for var in vars]
        final_vars = vars + [estimator]
        final_coefs = final_aggregated_x_coefs + [1.0]
        super().__init__(vars=final_vars, coefs=final_coefs, rhs=aggregated_rhs, sense='>=', name="LShapedOC")


class LShapedOCGen(CutGenerator):

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
            cut = ClassicalOC(vars, _var_coefs, _dual, _rhs, estimator=estimator)

            # Add the cut only if it is violated
            if sub.get_obj() > self._master_problem.get_estimator_values()[estimator]:
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
            theta_lb = self._master_problem.get_estimator_values()[estimator]

            cut = CombinatorialOC(bin_var_values, sub_obj, big_m=sub_obj - theta_lb, estimator=estimator)

            # Add the cut only if it is violated
            if sub.get_obj() > self._master_problem.get_estimator_values()[estimator]:
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


if __name__ == '__main__':
    pass

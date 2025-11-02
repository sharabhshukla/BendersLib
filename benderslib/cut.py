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
    This cut can be interpreted as a first-order Taylor approximation or a supporting hyperplane for the value function of the subproblem.

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

    def __init__(self, vars: list[str], var_coefs: dict, dual_values: list, rhs: list):
        vars = vars + ['theta']

        coefs = [sum(a * b for a, b in zip(dual_values, var_coefs)) for var, var_coefs in var_coefs.items()] + [1.0]
        cut_rhs = sum(a * b for a, b in zip(dual_values, rhs))

        # # Even slower when data is small
        # dual_v = np.array(dual_values)
        # rhs_v = np.array(rhs)
        # coefs_m = np.array(list(var_coefs.values()))
        # coefs = list(coefs_m @ dual_v) + [1.0]
        # cut_rhs = float(dual_v @ rhs_v)

        super().__init__(vars=vars, coefs=coefs, rhs=cut_rhs, sense='>=', name="ClassicalOC")


class ClassicalOCGen(CutGenerator):

    def __init__(self, master_problem, sub_problem):
        super().__init__(master_problem, sub_problem)

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

    def __init__(self, master_problem, sub_problem):
        super().__init__(master_problem, sub_problem)

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


class NoGoodCut(FeasibilityCut):
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

        super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='<=', name="NoGoodCut")


class CombinatorialFCGen(CutGenerator):

    def __init__(self, master_problem, sub_problem):
        super().__init__(master_problem, sub_problem)

    def generate(self) -> list[NoGoodCut]:
        """
        This method generates :class:`NoGoodCut` feasibility cuts based on the current solution
        of the master problem.
        """
        var_values = self._master_problem.get_var_values(self._complicating_vars)

        cut = NoGoodCut(var_values)
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
    If it is not specified, BendersLib set :math:`M = z^*` in each iteration.
    The cut is rewritten as follows.

    .. math::

        \\frac{\\theta}{z*} - \\sum_{i \\in I_1} x_i + \\sum_{i \\in I_0} x_i \\geq 1 - |I_1|

    Parameters
    ----------
    bin_var_values : dict
        A dictionary mapping binary variable names to their values in the current master problem solution.
    sub_obj : float
        The objective value of the subproblem given the current master problem solution.
    big_m : float
        A large constant used in the cut formulation.
    """

    def __init__(self, bin_var_values: dict, sub_obj: float, big_m: float = None):
        var_zeros = [var for var, val in bin_var_values.items() if val <= 0.5]
        var_ones = [var for var, val in bin_var_values.items() if val > 0.5]
        big_m = sub_obj if big_m is None else big_m

        # Form 1
        # vars = ['theta'] + var_ones + var_zeros
        # coefs = [1.0] + [-big_m] * len(var_ones) + [big_m] * len(var_zeros)
        # rhs = sub_obj - big_m * len(var_ones)

        # Form 2: same number of cuts, but faster to solve the master problem
        vars = ['theta'] + var_ones + var_zeros
        coefs = [1.0 / big_m] + [-1.0] * len(var_ones) + [1.0] * len(var_zeros)
        rhs = 1 - len(var_ones)

        super().__init__(vars=vars, coefs=coefs, rhs=rhs, sense='>=', name="CombinatorialCut")


class CombinatorialOCGen(CutGenerator):

    def __init__(self, master_problem, sub_problem, big_m: float = None):
        super().__init__(master_problem, sub_problem)
        self.big_m = big_m

    def generate(self) -> list[CombinatorialOC]:
        """
        This method generates :class:`CombinatorialOC` optimality cuts based on the current solution
        of the master problem and the objective value obtained from the subproblem.
        """
        var_values = self._master_problem.get_var_values(self._complicating_vars)
        sub_obj = self._sub_problem.get_obj()
        big_m = sub_obj if self.big_m is None else self.big_m

        cut = CombinatorialOC(var_values, sub_obj, big_m)
        return [cut]


class LShapedOCGen(CutGenerator):

    def __init__(self, master_problem, sub_problem):
        super().__init__(master_problem, sub_problem)

        self.var_coefs = dict()
        self.rhs = dict()

        for i, sub in enumerate(self._sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self._complicating_vars)
            self.rhs[i] = sub.get_rhs()

    def _single_cut(self) -> list[ClassicalOC]:
        """
        This method generates a single :class:`ClassicalOC` optimality cut aggregating all subproblems (scenarios).
        """
        avg_var_coefs = None
        avg_rhs = None
        avg_dual = None

        for i, sub in enumerate(self._sub_problem):
            _var_coefs = self.var_coefs[i]
            _rhs = self.rhs[i]
            _dual = sub.get_dual_values()

            prob = self._sub_problem.prob[i]
            if avg_var_coefs is None:
                avg_var_coefs = {var: [coef * prob for coef in coefs] for var, coefs in _var_coefs.items()}
                avg_rhs = [r * prob for r in _rhs]
                avg_dual = [d * prob for d in _dual]
            else:
                for var, coefs in _var_coefs.items():
                    avg_var_coefs[var] = [a + c * prob for a, c in zip(avg_var_coefs[var], coefs)]
                avg_rhs = [a + r * prob for a, r in zip(avg_rhs, _rhs)]
                avg_dual = [a + d * prob for a, d in zip(avg_dual, _dual)]

        vars = self._complicating_vars + ['theta']
        cut = ClassicalOC(vars, avg_var_coefs, avg_dual, avg_rhs)
        return [cut]

    def _multi_cuts(self) -> list[ClassicalOC]:
        """
        This method generates multiple :class:`ClassicalOC` optimality cuts, one for each subproblem (scenario).
        :return:
        """
        cuts = []
        for i, sub in enumerate(self._sub_problem):
            _var_coefs = self.var_coefs[i]
            _rhs = self.rhs[i]
            _dual = sub.get_dual_values()

            vars = self._complicating_vars + [self._sub_problem.estimators[i]]
            cut = ClassicalOC(vars, _var_coefs, _dual, _rhs)
            cuts.append(cut)

        return cuts

    def generate(self) -> list[ClassicalOC]:
        """
        This method generates :class:`ClassicalOC` optimality cuts based on the current solution
        of the master problem and the dual values obtained from the subproblems.
        """
        return self._multi_cuts() if self._sub_problem.multi_opti_cut else self._single_cut()


class LShapedFCGen(CutGenerator):

    def __init__(self, master_problem, sub_problem):
        super().__init__(master_problem, sub_problem)

        self.var_coefs = dict()
        self.rhs = dict()

        for i, sub in enumerate(self._sub_problem):
            self.var_coefs[i] = sub.get_var_coefs(self._complicating_vars)
            self.rhs[i] = sub.get_rhs()

    def generate(self):
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
                if not self._sub_problem.multi_feas_cut:
                    break

        return cuts


if __name__ == '__main__':
    pass

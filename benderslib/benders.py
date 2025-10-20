# coding:utf-8

from .core import BendersParams, MasterProblem, SubProblem, BendersBase
from .cut import ClassicalOC, ClassicalFC, NoGoodCut, CombinatorialCut, LShapedCut


class ClassicalBenders(BendersBase):
    """
    A built-in implementation of the classical Benders decomposition method.
    It builds a Benders decomposition framework using the provided master problem,
    subproblem, and complicating variables.
    The optimality cut is defined by :class:`ClassicalOC` and the feasibility cut is defined by :class:`ClassicalFC`.

    .. caution::
        The class :class:`ClassicalBenders` requires the **subproblem be pure LP**.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : SubProblem
        An instance of :class:`SubProblem` representing the subproblem.
    complicating_vars : list[str]
        A list of names of the complicating variables in the master problem.
    params : BendersParams, optional
        An instance of :class:`BendersParams` containing parameters for the Benders decomposition process.
        If not provided, default parameters will be used.
    """

    def __init__(
            self,
            master_problem: MasterProblem,
            sub_problem: SubProblem,
            complicating_vars: list,
            params: BendersParams = BendersParams()
    ):
        self.optimality_cut = ClassicalOC
        self.feasibility_cut = ClassicalFC
        super().__init__(
            master_problem, sub_problem, complicating_vars, self.optimality_cut, self.feasibility_cut, params)

        self.master_problem.complicating_vars = complicating_vars
        self.sub_problem.complicating_vars = complicating_vars

        # Attributes
        self._var_coefs = self.sub_problem.get_var_coefs(complicating_vars)
        self._rhs = self.sub_problem.get_rhs()

    def add_optimality_cut(self, complicating_var_values: dict):
        dual_values = self.sub_problem.get_dual_values()
        cut = self.optimality_cut(complicating_var_values, self._var_coefs, dual_values, self._rhs)
        self.master_problem.add_cut(cut)

    def add_feasibility_cut(self, complicating_var_values: dict):
        extreme_ray = self.sub_problem.get_extreme_ray()
        cut = self.feasibility_cut(complicating_var_values, self._var_coefs, extreme_ray, self._rhs)
        self.master_problem.add_cut(cut)


class CombinatorialBenders(BendersBase):
    """
    A built-in implementation of the Combinatorial Benders Decomposition method.
    It builds a Benders decomposition framework using the provided master problem,
    subproblem, and complicating variables.
    The optimality cut is defined by :class:`CombinatorialCut` and the feasibility cut is defined by :class:`NoGoodCut`.

    .. caution::
        The class :class:`CombinatorialBenders` requires the **complicating variables be pure binary (0-1)**.

    Parameters
    ----------
    master_problem : MasterProblem
        An instance of :class:`MasterProblem` representing the master problem.
    sub_problem : SubProblem
        An instance of :class:`SubProblem` representing the subproblem.
    complicating_vars : list[str]
        A list of names of the complicating variables in the master problem.
    opt_cut_generator : callable, optional
        A callable function to generate optimality cuts.
        If not provided, the default :class:`CombinatorialCut` will be used.
    feas_cut_generator : callable, optional
        A callable function to generate feasibility cuts.
        If not provided, the default :class:`NoGoodCut` will be used.
    params : BendersParams, optional
        An instance of :class:`BendersParams` containing parameters for the Benders decomposition process.
        If not provided, default parameters will be used.
    """

    def __init__(
            self,
            master_problem: MasterProblem,
            sub_problem: SubProblem,
            complicating_vars: list,
            opt_cut_generator=None,
            feas_cut_generator=None,
            params: BendersParams = BendersParams()
    ):
        self.feasibility_cut = NoGoodCut
        self.optimality_cut = CombinatorialCut
        super().__init__(
            master_problem, sub_problem, complicating_vars, self.optimality_cut, self.feasibility_cut, params)

        self.master_problem.complicating_vars = complicating_vars
        self.sub_problem.complicating_vars = complicating_vars

        self.opt_cut_generator = opt_cut_generator
        self.feas_cut_generator = feas_cut_generator

    def add_feasibility_cut(self, complicating_var_values: dict[str, float | int]):
        if self.feas_cut_generator is not None:
            cut = self.feas_cut_generator(complicating_var_values, self.master_problem, self.sub_problem)
        else:
            cut = self.feasibility_cut(complicating_var_values)
        self.master_problem.add_cut(cut)

    def add_optimality_cut(self, complicating_var_values: dict[str, float | int]):
        if self.opt_cut_generator is not None:
            cut = self.opt_cut_generator(complicating_var_values, self.master_problem, self.sub_problem)
        else:
            sub_obj = self.sub_problem.get_obj()
            cut = self.optimality_cut(complicating_var_values, sub_obj)
        self.master_problem.add_cut(cut)


class LShaped(BendersBase):

    def __init__(
            self,
            master_problem: MasterProblem,
            sub_problems: SubProblem,
            complicating_vars: list,
            multi_cut: bool = False,
            params: BendersParams = BendersParams()
    ):
        self.optimality_cut = ClassicalOC if not multi_cut else LShapedCut
        self.feasibility_cut = ClassicalFC

        super().__init__(
            master_problem, sub_problems, complicating_vars, None, None, params)

        self.master_problem.complicating_vars = complicating_vars
        self.sub_problem.complicating_vars = complicating_vars

    #     # Attributes
    #     self._var_coefs = self.sub_problem.get_var_coefs(complicating_vars)
    #     self._rhs = self.sub_problem.get_rhs()
    #
    # def add_optimality_cut(self, complicating_var_values: dict):
    #     dual_values = self.sub_problem.get_dual_values()
    #     cut = self.optimality_cut(complicating_var_values, self._var_coefs, dual_values, self._rhs)
    #     self.master_problem.add_cut(cut)
    #
    # def add_feasibility_cut(self, complicating_var_values: dict):
    #     extreme_ray = self.sub_problem.get_extreme_ray()
    #     cut = self.feasibility_cut(complicating_var_values, self._var_coefs, extreme_ray, self._rhs)
    #     self.master_problem.add_cut(cut)


class IntegerLShaped(BendersBase):
    pass


class AnnotatedLShaped(BendersBase):
    pass


class GeneralizedBenders(BendersBase):
    pass


class LogicBasedBenders(BendersBase):
    pass


if __name__ == '__main__':
    # TODO: Benders Dual Decomposition
    # TODO: Benchmarking, BD is faster on what kind of problems?
    pass

# coding:utf-8

import pytest
from numpy.ma.testutils import approx

from benderslib import BendersConsts as CST


class BaseTestSolver:
    """Base test class for solver interfaces.

    Since assertions are consistent across different solver interfaces,
    it can be ensured that all solvers have consistent behavior.
    """

    @pytest.fixture
    def solver_instance(self, *args):
        raise NotImplementedError("solver_instance fixture must be implemented in subclass.")

    def test_initial_status(self, solver_instance):
        assert solver_instance.status == CST.UNSOLVED

    def test_solve(self, solver_instance):
        solver_instance.solve()
        assert solver_instance.status == CST.OPTIMAL

    def test_get_obj(self, solver_instance):
        solver_instance.solve()
        obj = solver_instance.get_obj()
        assert approx(obj, 12.0, atol=1e-6)

    def test_get_var_values(self, solver_instance):
        solver_instance.solve()
        values = solver_instance.get_var_values()
        assert approx(values["x1"], 2.0, atol=1e-6)
        assert approx(values["x2"], 2.0, atol=1e-6)

        x1_value = solver_instance.get_var_values(["x1"])["x1"]
        x2_value = solver_instance.get_var_values(["x2"])["x2"]
        assert approx(x1_value, 2.0, atol=1e-6)
        assert approx(x2_value, 2.0, atol=1e-6)

    @pytest.mark.skipif_cp_solver
    def test_add_estimators(self, solver_instance):
        solver_instance.add_estimators(["theta"], prob=[1.0], lb=0.0)
        solver_instance.add_estimators(["theta1", "theta2"], prob=[0.5, 0.5], lb=0.0)

    def test_fix_unfix_vars(self, solver_instance):
        # Fix x1 to 1 and solve
        solver_instance.fix_vars({"x1": 1.0})
        solver_instance.solve()
        x1_value = solver_instance.get_var_values(["x1"])["x1"]
        assert approx(x1_value, 1.0, atol=1e-6)

        # Unfix x1 and solve
        solver_instance.unfix_vars(["x1"])
        solver_instance.solve()
        x1_value = solver_instance.get_var_values(["x1"])["x1"]
        assert approx(x1_value, 2.0, atol=1e-6)
        assert approx(solver_instance.get_obj(), 12.0, atol=1e-6)

    @pytest.mark.skipif_cp_solver
    def test_add_remove_cut(self, solver_instance):
        from benderslib import OptimalityCut, FeasibilityCut

        # LHS >= 10 and LHS <= 5 makes the model infeasible
        opti_cut = OptimalityCut(vars=['x1', 'x2'], coefs=[1.0, 2.0], rhs=10.0, sense=CST.GE, name='test_opti_cut')
        solver_instance.add_cut(opti_cut, name='test_opti_cut')
        feas_cut = FeasibilityCut(vars=['x1', 'x2'], coefs=[1.0, 2.0], rhs=5.0, sense=CST.LE, name='test_feas_cut')
        solver_instance.add_cut(feas_cut, name='test_feas_cut')

        # Solve the intentionally infeasible model
        solver_instance.solve()
        # assert solver_instance.status == CST.INFEASIBLE

        # Remove the feas_cut
        solver_instance.remove_cut('test_feas_cut')
        solver_instance.solve()
        assert solver_instance.status == CST.OPTIMAL

        # Remove the opti_cut
        solver_instance.remove_cut('test_opti_cut')
        solver_instance.solve()
        assert approx(solver_instance.get_obj(), 12.0, atol=1e-6)

    @pytest.mark.skipif_cp_solver
    def test_get_var_coefs(self, solver_instance):
        coefs = solver_instance.get_var_coefs()
        assert coefs == {'x1': [1.0, 2.0, 1.0, 0.0], 'x2': [2.0, 1.0, 0.0, 1.0]}

    @pytest.mark.skipif_cp_solver
    def test_get_rhs(self, solver_instance):
        rhs = solver_instance.get_rhs()
        assert rhs == [6.0, 6.0, 100.0, 100.0]

    @pytest.mark.skipif_cp_solver
    def test_get_dual_values(self, solver_instance):
        solver_instance.solve()
        duals = solver_instance.get_dual_values()
        # Variable bounds are also counted as constraints
        expected_duals = [1.0, 1.0, 0.0, 0.0]
        assert len(duals) == len(expected_duals)
        assert all(approx(duals[i], expected_duals[i], atol=1e-6) for i in range(len(duals)))

    @pytest.mark.skipif_cp_solver
    def test_get_extreme_ray(self, infeasible_solver_instance):
        infeasible_solver_instance.solve()
        assert infeasible_solver_instance.status == CST.INFEASIBLE
        ray = infeasible_solver_instance.get_extreme_ray()
        assert isinstance(ray, list)
        # Variable bounds are also counted as constraints
        expected_ray = [-0.333333, -0.333333, 1.0, 0.0, 0.0]
        assert len(ray) == len(expected_ray)
        assert all(approx(ray[i], expected_ray[i], atol=1e-6) for i in range(len(ray)))

    def test_compute_iis_for_infeasible(self, infeasible_solver_instance):
        infeasible_solver_instance.solve()
        assert infeasible_solver_instance.status == CST.INFEASIBLE
        iis = infeasible_solver_instance.compute_iis()
        assert iis == {'x1', 'x2'}

    @pytest.mark.skipif_cp_solver
    def test_make_master_problem(self, solver_instance):
        master_problem = solver_instance.make_master_problem(solver_instance.model, ["x1"])
        # TODO: Placeholder assertion; implement specific checks as needed
        assert type(master_problem) == type(solver_instance.model)

    @pytest.mark.skipif_cp_solver
    def test_make_sub_problem(self, solver_instance):
        # Placeholder assertion; implement specific checks as needed
        sub_problem = solver_instance.make_sub_problem(solver_instance.model, ["x1"])
        # TODO: Placeholder assertion; implement specific checks as needed
        assert type(sub_problem) == type(solver_instance.model)


class BaseTestCPSolver(BaseTestSolver):
    """Base test class for Constraint Programming (CP) solver interfaces.

    The tests that are not applicable to CP solvers are skipped.
    """

    @pytest.mark.skip(reason="CP solvers do not support estimators.")
    def test_add_estimators(self, solver_instance):
        pass

    @pytest.mark.skip(reason="CP solvers do not support adding/removing cuts in the same way.")
    def test_add_remove_cut(self, solver_instance):
        pass

    @pytest.mark.skip(reason="CP solvers may not provide constraint coefficients in this format.")
    def test_get_var_coefs(self, solver_instance):
        pass

    @pytest.mark.skip(reason="CP solvers may not provide RHS of constraints in this format.")
    def test_get_rhs(self, solver_instance):
        pass

    @pytest.mark.skip(reason="CP solvers do not provide dual values.")
    def test_get_dual_values(self, solver_instance):
        pass

    @pytest.mark.skip(reason="CP solvers do not provide extreme rays.")
    def test_get_extreme_ray(self, infeasible_solver_instance):
        pass

    @pytest.mark.skip(reason="make_master_problem is not applicable to CP solvers in this context.")
    def test_make_master_problem(self, solver_instance):
        pass

    @pytest.mark.skip(reason="make_sub_problem is not applicable to CP solvers in this context.")
    def test_make_sub_problem(self, solver_instance):
        pass

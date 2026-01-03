# coding:utf-8

import pytest

from benderslib.solvers.gurobi import Gurobi
from benderslib.solvers.base import SolverBase
from benderslib.consts import BendersConsts as CST
from benderslib.core import Cut

import gurobipy as gp
from gurobipy import GRB


class SolverTestBase:
    """
    Base class for solver tests.
    Subclasses must implement the setup_solver method.
    """
    solver: SolverBase
    model: gp.Model

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        Create a simple LP model for testing.
        min x + y
        s.t.
        c1: x + 2y >= 2
        c2: 2x + y >= 2
        x, y >= 0
        """
        self.model = gp.Model("test")
        x = self.model.addVar(name="x", lb=0.0)
        y = self.model.addVar(name="y", lb=0.0)
        self.model.setObjective(x + y, GRB.MINIMIZE)
        self.model.addConstr(x + 2 * y >= 2, "c1")
        self.model.addConstr(2 * x + y >= 2, "c2")
        self.model.update()
        self.setup_solver()

    def setup_solver(self):
        """
        This method should be implemented by subclasses to instantiate the solver.
        """
        raise NotImplementedError

    def test_initial_properties(self):
        """Unit test for solver properties."""
        assert self.solver._sense == CST.MIN
        assert set(self.solver._all_vars) == {"x", "y"}
        assert not self.solver._int_vars
        assert not self.solver._bin_vars
        assert self.solver.status == CST.UNSOLVED

    def test_solve_optimal(self):
        """Integration test for solving an optimal model."""
        self.solver.solve()
        assert self.solver.status == CST.OPTIMAL
        assert pytest.approx(self.solver.get_obj(), 1e-6) == 4 / 3

        var_values = self.solver.get_var_values()
        assert pytest.approx(var_values["x"], 1e-6) == 2 / 3
        assert pytest.approx(var_values["y"], 1e-6) == 2 / 3

    def test_solve_infeasible(self):
        """Integration test for solving an infeasible model."""
        # Add a conflicting constraint to make the model infeasible
        self.model.addConstr(self.model.getVarByName("x") <= -1)
        self.solver.model.addConstr(self.solver.model.getVarByName("x") <= -1)

        self.solver.solve()
        assert self.solver.status == CST.INFEASIBLE

    def test_fix_unfix_vars(self):
        """Unit test for fixing and unfixing variables."""

        # Fix x to 1.0
        self.solver.fix_vars({"x": 1.0})
        self.solver.solve()
        assert self.solver.status == CST.OPTIMAL
        var_values = self.solver.get_var_values()
        assert pytest.approx(var_values["x"]) == 1.0
        assert pytest.approx(var_values["y"]) == 0.5
        assert pytest.approx(self.solver.get_obj()) == 1.5

        # Unfix x
        self.solver.unfix_vars(["x"])
        self.solver.solve()
        assert self.solver.status == CST.OPTIMAL
        var_values = self.solver.get_var_values()
        assert pytest.approx(var_values["x"], 1e-6) == 2 / 3

    def test_get_var_values(self):
        """Unit test for getting variable values."""
        self.solver.solve()

        # Test getting all variables
        var_values = self.solver.get_var_values()
        assert len(var_values) == 2
        assert "x" in var_values
        assert "y" in var_values

        # Test getting a subset of variables
        var_values_subset = self.solver.get_var_values(["x"])
        assert len(var_values_subset) == 1
        assert "x" in var_values_subset
        assert "y" not in var_values_subset

    def test_get_duals(self):
        """Unit test for getting dual values."""
        self.solver.solve()
        duals = self.solver.get_dual_values()

        # The number of duals should match the number of constraints
        assert len(duals) == len(self.solver.model.getConstrs())

        # For this problem, duals are expected to be non-zero
        # The exact values are [1/3, 1/3]
        assert all(pytest.approx(d, 1e-6) == 1 / 3 for d in duals)

    def test_get_extreme_ray(self):
        """Unit test for getting extreme rays."""
        # Make the model infeasible
        self.model.addConstr(self.model.getVarByName("x") <= -1)
        self.solver.model.addConstr(self.solver.model.getVarByName("x") <= -1)

        self.solver.solve()
        assert self.solver.status == CST.INFEASIBLE
        ray = self.solver.get_extreme_ray()
        assert ray is not None
        assert len(ray) == len(self.solver._rhs) + 2
        # The exact values depend on the solver's internal handling of infeasibility
        # Here we just check that at least one value is non-zero
        assert any(abs(v) > 1e-6 for v in ray)

    def test_add_remove_cut(self):
        """Unit test for adding a constraint."""

        # Add constraint x <= 0.5
        cut = Cut(vars=["x"], coefs=[1.0], rhs=0.5, sense=CST.LE, ctype=CST.OPTIMALITY, name="cut1")
        self.solver.add_cut(cut, name="cut1")

        self.solver.solve()
        assert self.solver.status == CST.OPTIMAL
        var_values = self.solver.get_var_values()
        assert pytest.approx(var_values["x"]) == 0.5
        assert pytest.approx(var_values["y"]) == 1
        assert pytest.approx(self.solver.get_obj()) == 1.5

        # Remove the added constraint
        self.solver.remove_cut("cut1")
        self.solver.solve()
        assert self.solver.status == CST.OPTIMAL
        var_values = self.solver.get_var_values()
        assert pytest.approx(var_values["x"], 1e-6) == 2 / 3
        assert pytest.approx(var_values["y"], 1e-6) == 2 / 3
        assert pytest.approx(self.solver.get_obj(), 1e-6) == 4 / 3


class TestGurobiSolver(SolverTestBase):
    """
    Test suite for the Gurobi solver interface.
    """

    def setup_solver(self):
        self.solver = Gurobi(self.model)


if __name__ == "__main__":
    pytest.main([__file__])

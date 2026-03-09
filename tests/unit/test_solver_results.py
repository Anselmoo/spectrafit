"""Unit tests for SolverResults (v2 — direct FitResult construction)."""

from __future__ import annotations

import pytest

from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.types import DataSplitDict


class TestSolverResultsConstruction:
    """Tests for SolverResults construction."""

    @pytest.mark.unit
    def test_from_empty_fit_result(self) -> None:
        solver = SolverResults(result=FitResult())
        assert isinstance(solver, SolverResults)
        assert isinstance(solver.result, FitResult)

    @pytest.mark.unit
    def test_from_global_fit_result(self) -> None:
        solver = SolverResults(result=FitResult(global_fitting=1))
        assert solver.settings_global_fitting == 1

    @pytest.mark.unit
    def test_from_fit_result_direct(self) -> None:
        result = FitResult()
        solver = SolverResults(result=result)
        assert solver.result is result

    @pytest.mark.unit
    def test_frozen_model(self) -> None:
        solver = SolverResults(result=FitResult())
        with pytest.raises(Exception):
            solver.result = FitResult()  # type: ignore[misc]


class TestSolverResultsProperties:
    """Tests for all SolverResults property delegates."""

    @pytest.fixture()
    def solver_with_data(self) -> SolverResults:
        result = FitResult(
            global_fitting=0,
            fit_insights=FitInsights(
                configurations=FitConfigurations(
                    method="leastsq", max_nfev=500, nan_policy="raise"
                ),
                statistics={"chisqr": 0.02, "redchi": 0.002},
                variables={
                    "p1_amplitude": VariableFitResult(
                        init_value=1.0, model_value=1.05, best_value=1.1, stderr=0.05
                    )
                },
                errorbars={"p1_amplitude": "yes"},
                correlations={"p1_amplitude": {"p1_center": 0.1}},
                covariance_matrix={"p1_amplitude": {"p1_amplitude": 0.0025}},
                computational={"nfev": 100},
            ),
            data_summary=DataSummary(
                regression_metrics=DataSplitDict(
                    data=[[0.99]], index=[0], columns=["r2"]
                ),
                descriptive_statistic=DataSplitDict(
                    data=[[1.0]], index=[0], columns=["mean"]
                ),
                linear_correlation=DataSplitDict(
                    data=[[0.98]], index=[0], columns=["pearson"]
                ),
            ),
            confidence=ConfidenceResults(settings=False),
        )
        return SolverResults(result=result)

    @pytest.mark.unit
    def test_settings_global_fitting(self, solver_with_data: SolverResults) -> None:
        assert solver_with_data.settings_global_fitting == 0

    @pytest.mark.unit
    def test_settings_configurations(self, solver_with_data: SolverResults) -> None:
        cfg = solver_with_data.settings_configurations
        assert cfg["method"] == "leastsq"
        assert cfg["max_nfev"] == 500

    @pytest.mark.unit
    def test_settings_conf_interval(self, solver_with_data: SolverResults) -> None:
        assert solver_with_data.settings_conf_interval is False

    @pytest.mark.unit
    def test_get_gof(self, solver_with_data: SolverResults) -> None:
        gof = solver_with_data.get_gof
        assert "chisqr" in gof
        assert gof["chisqr"] == pytest.approx(0.02)

    @pytest.mark.unit
    def test_get_variables(self, solver_with_data: SolverResults) -> None:
        variables = solver_with_data.get_variables
        assert "p1_amplitude" in variables
        assert variables["p1_amplitude"].best_value == pytest.approx(1.1)

    @pytest.mark.unit
    def test_get_errorbars(self, solver_with_data: SolverResults) -> None:
        errorbars = solver_with_data.get_errorbars
        assert errorbars["p1_amplitude"] == "yes"

    @pytest.mark.unit
    def test_get_component_correlation(self, solver_with_data: SolverResults) -> None:
        corr = solver_with_data.get_component_correlation
        assert "p1_amplitude" in corr

    @pytest.mark.unit
    def test_get_covariance_matrix(self, solver_with_data: SolverResults) -> None:
        cov = solver_with_data.get_covariance_matrix
        assert "p1_amplitude" in cov

    @pytest.mark.unit
    def test_get_computational(self, solver_with_data: SolverResults) -> None:
        comp = solver_with_data.get_computational
        assert comp.get("nfev") == 100

    @pytest.mark.unit
    def test_get_regression_metrics(self, solver_with_data: SolverResults) -> None:
        metrics = solver_with_data.get_regression_metrics
        assert metrics["columns"] == ["r2"]
        assert metrics["data"] == [[0.99]]

    @pytest.mark.unit
    def test_get_descriptive_statistic(self, solver_with_data: SolverResults) -> None:
        desc = solver_with_data.get_descriptive_statistic
        assert desc["columns"] == ["mean"]
        assert desc["data"] == [[1.0]]

    @pytest.mark.unit
    def test_get_linear_correlation(self, solver_with_data: SolverResults) -> None:
        lc = solver_with_data.get_linear_correlation
        assert lc["columns"] == ["pearson"]
        assert lc["data"] == [[0.98]]

    @pytest.mark.unit
    def test_get_confidence_interval_empty(self, solver_with_data: SolverResults) -> None:
        ci = solver_with_data.get_confidence_interval
        assert ci == {}

    @pytest.mark.unit
    def test_get_current_metric_returns_dataframe(
        self, solver_with_data: SolverResults
    ) -> None:
        import pandas as pd

        df = solver_with_data.get_current_metric
        assert isinstance(df, pd.DataFrame)

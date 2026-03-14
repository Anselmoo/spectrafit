"""Unit tests for SolverResults (v2 — direct FitResult construction)."""

from __future__ import annotations

import pytest

from pydantic import ValidationError
from spectrafit.jupyter.result_projection import NotebookMetricProjection
from spectrafit.jupyter.result_projection import NotebookPeaksProjection
from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ComputationalMeta
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.split_frame import SplitFrame
from spectrafit.reporting.service import CanonicalReportSchema
from spectrafit.reporting.service import SolverReportProjection


class TestSolverResultsConstruction:
    """Tests for SolverResults construction."""

    @pytest.mark.unit
    def test_from_empty_fit_result(self) -> None:
        solver = SolverResults(result=FitResult())
        assert isinstance(solver, SolverResults)
        assert isinstance(solver.result, FitResult)

    @pytest.mark.unit
    def test_from_global_fit_result(self) -> None:
        solver = SolverResults(result=FitResult(global_fitting=FittingMode.GLOBAL))
        assert solver.fitting_mode == FittingMode.GLOBAL
        assert solver.is_global is True

    @pytest.mark.unit
    def test_from_fit_result_direct(self) -> None:
        result = FitResult()
        solver = SolverResults(result=result)
        assert solver.result is result

    @pytest.mark.unit
    def test_frozen_model(self) -> None:
        solver = SolverResults(result=FitResult())
        with pytest.raises(ValidationError):
            solver.result = FitResult()  # type: ignore[misc]


class TestSolverResultsProperties:
    """Tests for all SolverResults property delegates."""

    @pytest.fixture
    def solver_with_data(self) -> SolverResults:
        result = FitResult(
            global_fitting=FittingMode.STANDARD,
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
                regression_metrics=SplitFrame(data=[[0.99]], index=[0], columns=["r2"]),
                descriptive_statistic=SplitFrame(
                    data=[[1.0]], index=[0], columns=["mean"]
                ),
                linear_correlation=SplitFrame(
                    data=[[0.98]], index=[0], columns=["pearson"]
                ),
            ),
            confidence=ConfidenceResults(settings=False),
        )
        return SolverResults(result=result)

    @pytest.mark.unit
    def test_fitting_mode_and_global_flag(
        self,
        solver_with_data: SolverResults,
    ) -> None:
        assert solver_with_data.fitting_mode == FittingMode.STANDARD
        assert solver_with_data.is_global is False

    @pytest.mark.unit
    def test_fit_configurations_model(self, solver_with_data: SolverResults) -> None:
        cfg = solver_with_data.fit_configurations_model
        assert isinstance(cfg, FitConfigurations)
        assert cfg.method == "leastsq"
        assert cfg.max_nfev == 500

    @pytest.mark.unit
    def test_canonical_report(self, solver_with_data: SolverResults) -> None:
        canonical_report = solver_with_data.canonical_report
        assert isinstance(canonical_report, CanonicalReportSchema)
        assert canonical_report.solver == solver_with_data.report_projection
        assert canonical_report.configurations == solver_with_data.fit_configurations_model

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "attribute_name",
        [
            "settings_global_fitting",
            "settings_configurations",
            "settings_conf_interval",
        ],
    )
    def test_deprecated_settings_shims_removed(
        self,
        solver_with_data: SolverResults,
        attribute_name: str,
    ) -> None:
        assert not hasattr(solver_with_data, attribute_name)

    @pytest.mark.unit
    def test_goodness_of_fit(self, solver_with_data: SolverResults) -> None:
        gof = solver_with_data.goodness_of_fit
        assert "chisqr" in gof
        assert gof["chisqr"] == pytest.approx(0.02)

    @pytest.mark.unit
    def test_variables(self, solver_with_data: SolverResults) -> None:
        variables = solver_with_data.variables
        assert "p1_amplitude" in variables
        assert variables["p1_amplitude"].best_value == pytest.approx(1.1)

    @pytest.mark.unit
    def test_errorbars(self, solver_with_data: SolverResults) -> None:
        errorbars = solver_with_data.errorbars
        assert errorbars["p1_amplitude"] == "yes"

    @pytest.mark.unit
    def test_component_correlation(self, solver_with_data: SolverResults) -> None:
        corr = solver_with_data.component_correlation
        assert "p1_amplitude" in corr

    @pytest.mark.unit
    def test_covariance_matrix(self, solver_with_data: SolverResults) -> None:
        cov = solver_with_data.covariance_matrix
        assert "p1_amplitude" in cov

    @pytest.mark.unit
    def test_computational(self, solver_with_data: SolverResults) -> None:
        comp = solver_with_data.computational
        assert comp.nfev == 100

    @pytest.mark.unit
    def test_computational_metadata(self, solver_with_data: SolverResults) -> None:
        comp = solver_with_data.computational_metadata
        assert isinstance(comp, ComputationalMeta)
        assert comp.nfev == 100

    @pytest.mark.unit
    def test_regression_metrics(self, solver_with_data: SolverResults) -> None:
        metrics = solver_with_data.regression_metrics
        assert metrics["columns"] == ["r2"]
        assert metrics["data"] == [[0.99]]

    @pytest.mark.unit
    def test_descriptive_statistic(self, solver_with_data: SolverResults) -> None:
        desc = solver_with_data.descriptive_statistic
        assert desc["columns"] == ["mean"]
        assert desc["data"] == [[1.0]]

    @pytest.mark.unit
    def test_linear_correlation(self, solver_with_data: SolverResults) -> None:
        lc = solver_with_data.linear_correlation
        assert lc["columns"] == ["pearson"]
        assert lc["data"] == [[0.98]]

    @pytest.mark.unit
    def test_confidence_interval_empty(
        self, solver_with_data: SolverResults
    ) -> None:
        ci = solver_with_data.confidence_interval
        assert ci == {}

    @pytest.mark.unit
    def test_current_metric_returns_dataframe(
        self, solver_with_data: SolverResults
    ) -> None:
        import pandas as pd

        df = solver_with_data.current_metric
        assert isinstance(df, pd.DataFrame)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("legacy_name", "canonical_name", "serialize_canonical"),
        [
            ("get_gof", "goodness_of_fit", False),
            ("get_variables", "variables", False),
            ("get_errorbars", "errorbars", False),
            ("get_component_correlation", "component_correlation", False),
            ("get_covariance_matrix", "covariance_matrix", False),
            ("get_computational", "computational", True),
            ("get_regression_metrics", "regression_metrics", False),
            ("get_descriptive_statistic", "descriptive_statistic", False),
            ("get_linear_correlation", "linear_correlation", False),
            ("get_confidence_interval", "confidence_interval", False),
        ],
    )
    def test_legacy_projection_shims_warn_and_delegate(
        self,
        solver_with_data: SolverResults,
        legacy_name: str,
        canonical_name: str,
        serialize_canonical: bool,
    ) -> None:
        with pytest.warns(FutureWarning, match=rf"SolverResults\.{legacy_name}"):
            legacy_value = getattr(solver_with_data, legacy_name)
        canonical_value = getattr(solver_with_data, canonical_name)
        if serialize_canonical:
            canonical_value = canonical_value.model_dump()
        assert legacy_value == canonical_value

    @pytest.mark.unit
    def test_get_current_metric_shim_warns_and_delegates(
        self, solver_with_data: SolverResults
    ) -> None:
        import pandas as pd

        with pytest.warns(FutureWarning, match=r"SolverResults\.get_current_metric"):
            legacy_metric = solver_with_data.get_current_metric
        canonical_metric = solver_with_data.current_metric
        pd.testing.assert_frame_equal(legacy_metric, canonical_metric)

    @pytest.mark.unit
    def test_metric_projection_returns_typed_projection(
        self, solver_with_data: SolverResults
    ) -> None:
        projection = solver_with_data.metric_projection
        assert isinstance(projection, NotebookMetricProjection)
        dataframe = projection.to_dataframe()
        assert dataframe.loc[0, "chisqr"] == pytest.approx(0.02)
        assert dataframe.loc[0, "redchi"] == pytest.approx(0.002)
        assert dataframe.loc[0, "0"] == pytest.approx(0.99)

    @pytest.mark.unit
    def test_peaks_projection_returns_typed_projection(
        self, solver_with_data: SolverResults
    ) -> None:
        projection = solver_with_data.peaks_projection
        assert isinstance(projection, NotebookPeaksProjection)
        dataframe = projection.to_dataframe()
        assert dataframe.loc[0, ("p1_amplitude", "init_value")] == pytest.approx(1.0)
        assert dataframe.loc[0, ("p1_amplitude", "best_value")] == pytest.approx(1.1)

    @pytest.mark.unit
    def test_report_projection_returns_typed_projection(
        self, solver_with_data: SolverResults
    ) -> None:
        projection = solver_with_data.report_projection
        assert isinstance(projection, SolverReportProjection)
        assert projection.goodness_of_fit == solver_with_data.goodness_of_fit
        assert projection.variables == solver_with_data.variables
        assert projection.regression_metrics == solver_with_data.regression_metrics

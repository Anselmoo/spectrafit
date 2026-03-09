"""Unit tests for extended FitResult sub-models (Phase 1a)."""

from __future__ import annotations

import pytest

from pydantic import ValidationError

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.types import DataSplitDict
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult


class TestFitConfigurations:
    """Tests for FitConfigurations."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        cfg = FitConfigurations()
        assert cfg.method == ""
        assert cfg.max_nfev == 0
        assert cfg.nan_policy == "raise"

    @pytest.mark.unit
    def test_explicit_values(self) -> None:
        cfg = FitConfigurations(method="leastsq", max_nfev=500, nan_policy="propagate")
        assert cfg.method == "leastsq"
        assert cfg.max_nfev == 500
        assert cfg.nan_policy == "propagate"

    @pytest.mark.unit
    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            FitConfigurations(unknown_field="x")  # type: ignore[call-arg]


class TestVariableFitResult:
    """Tests for VariableFitResult."""

    @pytest.mark.unit
    def test_all_none_defaults(self) -> None:
        v = VariableFitResult()
        assert v.init_value is None
        assert v.best_value is None
        assert v.stderr is None

    @pytest.mark.unit
    def test_explicit_values(self) -> None:
        v = VariableFitResult(init_value=1.0, model_value=1.1, best_value=1.05, stderr=0.01)
        assert v.best_value == pytest.approx(1.05)
        assert v.stderr == pytest.approx(0.01)

    @pytest.mark.unit
    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            VariableFitResult(bad=99)  # type: ignore[call-arg]


class TestFitInsights:
    """Tests for FitInsights."""

    @pytest.mark.unit
    def test_defaults_empty(self) -> None:
        fi = FitInsights()
        assert fi.statistics == {}
        assert fi.variables == {}
        assert fi.errorbars == {}
        assert isinstance(fi.configurations, FitConfigurations)

    @pytest.mark.unit
    def test_full_construction(self) -> None:
        fi = FitInsights(
            configurations=FitConfigurations(
                method="leastsq", max_nfev=1000, nan_policy="raise"
            ),
            statistics={"chisqr": 0.01, "redchi": 0.001},
            variables={
                "p1_amplitude": VariableFitResult(
                    init_value=1.0, best_value=1.1, stderr=0.05
                )
            },
            errorbars={"p1_amplitude": "yes"},
        )
        assert fi.configurations.method == "leastsq"
        assert fi.statistics["chisqr"] == pytest.approx(0.01)
        assert fi.variables["p1_amplitude"].best_value == pytest.approx(1.1)
        assert fi.errorbars["p1_amplitude"] == "yes"

    @pytest.mark.unit
    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            FitInsights(unknown=True)  # type: ignore[call-arg]


class TestDataSummary:
    """Tests for DataSummary."""

    @pytest.mark.unit
    def test_defaults_empty(self) -> None:
        ds = DataSummary()
        assert ds.regression_metrics["data"] == []
        assert ds.descriptive_statistic["data"] == []
        assert ds.linear_correlation["data"] == []

    @pytest.mark.unit
    def test_direct_construction(self) -> None:
        ds = DataSummary(
            regression_metrics=DataSplitDict(data=[[0.99]], index=[0], columns=["r2"]),
            descriptive_statistic=DataSplitDict(data=[[1.0]], index=[0], columns=["mean"]),
            linear_correlation=DataSplitDict(data=[[0.98]], index=[0], columns=["pearson"]),
        )
        assert ds.regression_metrics["columns"] == ["r2"]
        assert ds.descriptive_statistic["columns"] == ["mean"]
        assert ds.linear_correlation["columns"] == ["pearson"]

    @pytest.mark.unit
    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            DataSummary(unknown=True)  # type: ignore[call-arg]


class TestConfidenceResults:
    """Tests for ConfidenceResults."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        cr = ConfidenceResults()
        assert cr.settings is False
        assert cr.results == {}

    @pytest.mark.unit
    def test_enabled_with_results(self) -> None:
        cr = ConfidenceResults(
            settings={"p=0.95": {}},
            results={"p1_amplitude": [(0.9, 1.0), (1.0, 1.1)]},
        )
        assert isinstance(cr.settings, dict)
        assert "p1_amplitude" in cr.results

    @pytest.mark.unit
    def test_extra_forbid(self) -> None:
        with pytest.raises(ValidationError):
            ConfidenceResults(bad_field=1)  # type: ignore[call-arg]


class TestFitResultConstruction:
    """Tests for FitResult direct construction."""

    @pytest.mark.unit
    def test_empty_defaults(self) -> None:
        result = FitResult()
        assert isinstance(result.fit_insights, FitInsights)
        assert isinstance(result.data_summary, DataSummary)
        assert isinstance(result.confidence, ConfidenceResults)

    @pytest.mark.unit
    def test_global_fitting_flag(self) -> None:
        result = FitResult(global_fitting=1)
        assert result.global_fitting == FittingMode.GLOBAL

    @pytest.mark.unit
    def test_fit_insights_propagated(self) -> None:
        result = FitResult(
            fit_insights=FitInsights(
                statistics={"chisqr": 0.05},
                errorbars={"p1_amp": "yes"},
            )
        )
        assert result.fit_insights.statistics["chisqr"] == pytest.approx(0.05)

    @pytest.mark.unit
    def test_data_summary_propagated(self) -> None:
        result = FitResult(
            data_summary=DataSummary(
                regression_metrics=DataSplitDict(data=[[0.99]], index=[0], columns=["r2"])
            )
        )
        assert result.data_summary.regression_metrics["columns"] == ["r2"]

    @pytest.mark.unit
    def test_sub_models_have_extra_forbid(self) -> None:
        """Verify all new sub-models reject unknown fields."""
        for cls in (FitInsights, DataSummary, ConfidenceResults, FitConfigurations):
            with pytest.raises(ValidationError):
                cls(unknown_field=True)  # type: ignore[call-arg]

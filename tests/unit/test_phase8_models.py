"""Tests for Phase 8 models: FitResult, MCMCConfig, BatchFittingConfig.

Sub-models: FitInsights, DataSummary, ConfidenceResults,
VariableFitResult, FitConfigurations.
"""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from spectrafit.models.batch_config import BatchFittingConfig
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ComponentResult
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.types import DataSplitDict
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import FitStatistics
from spectrafit.models.results.fit_result import ParameterResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.mcmc_config import MCMCConfig


# ---------------------------------------------------------------------------
# FitResult
# ---------------------------------------------------------------------------


class TestFitResult:
    """FitResult is a full JSON Schema-validated export container."""

    def _make_result(self) -> FitResult:
        return FitResult(
            input_snapshot={"optimizer": {"method": "leastsq"}},
            statistics=FitStatistics(
                method="leastsq",
                nfev=50,
                ndata=100,
                nvarys=3,
                nfree=97,
                chisqr=0.05,
                redchi=0.000515,
                aic=-450.0,
                bic=-440.0,
                success=True,
                message="Fit succeeded.",
            ),
            parameters=[
                ParameterResult(
                    name="p1_amplitude",
                    init_value=1.0,
                    best_value=0.98,
                    stderr=0.02,
                    vary=True,
                )
            ],
            components=[
                ComponentResult(id="p1", model="gaussian", curve=[0.1, 0.5, 0.1])
            ],
            x=[0.0, 0.5, 1.0],
            y_data=[0.1, 0.5, 0.1],
            y_fit=[0.1, 0.5, 0.1],
        )

    def test_construction(self) -> None:
        r = self._make_result()
        assert r.statistics.success is True
        assert r.parameters[0].name == "p1_amplitude"
        assert r.components[0].id == "p1"

    def test_json_round_trip(self) -> None:
        r = self._make_result()
        dumped = r.model_dump(mode="json")
        r2 = FitResult.from_dict(dumped)
        assert r2.statistics.chisqr == pytest.approx(r.statistics.chisqr)
        assert r2.parameters[0].best_value == pytest.approx(0.98)

    def test_save_load(self, tmp_path: Path) -> None:
        r = self._make_result()
        out = tmp_path / "result.json"
        r.save(out)
        assert out.exists()
        r2 = FitResult.load(out)
        assert r2.statistics.nfev == 50

    def test_save_is_valid_json(self, tmp_path: Path) -> None:
        r = self._make_result()
        out = tmp_path / "result.json"
        r.save(out)
        parsed = json.loads(out.read_text())
        assert "statistics" in parsed
        assert "parameters" in parsed

    def test_json_schema_has_all_fields(self) -> None:
        schema = FitResult.model_json_schema()
        for field in ("statistics", "parameters", "components", "x", "y_data", "y_fit"):
            assert field in schema["properties"]

    def test_empty_defaults(self) -> None:
        r = FitResult()
        assert r.parameters == []
        assert r.components == []
        assert r.x == []

    def test_parameter_result_optional_stderr(self) -> None:
        p = ParameterResult(name="p1_amp", init_value=1.0, best_value=0.95)
        assert p.stderr is None
        assert p.expr is None

    def test_fit_statistics_defaults(self) -> None:
        s = FitStatistics()
        assert s.success is False
        assert s.chisqr == 0.0


# ---------------------------------------------------------------------------
# MCMCConfig
# ---------------------------------------------------------------------------


class TestMCMCConfig:
    """MCMCConfig validates emcee kwargs."""

    def test_defaults(self) -> None:
        cfg = MCMCConfig()
        assert cfg.nwalkers == 100
        assert cfg.steps == 1000
        assert cfg.burn == 0
        assert cfg.thin == 1
        assert cfg.progress is True
        assert cfg.seed is None

    def test_custom_values(self) -> None:
        cfg = MCMCConfig(nwalkers=50, steps=500, burn=100, thin=2, seed=42)
        assert cfg.nwalkers == 50
        assert cfg.seed == 42

    def test_nwalkers_ge_2(self) -> None:
        with pytest.raises(Exception):
            MCMCConfig(nwalkers=1)

    def test_steps_ge_1(self) -> None:
        with pytest.raises(Exception):
            MCMCConfig(steps=0)

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            MCMCConfig(unknown_field=99)  # type: ignore[call-arg]

    def test_json_schema_complete(self) -> None:
        schema = MCMCConfig.model_json_schema()
        for key in ("nwalkers", "steps", "burn", "thin", "is_weighted", "seed"):
            assert key in schema["properties"]


# ---------------------------------------------------------------------------
# BatchFittingConfig
# ---------------------------------------------------------------------------

_COMPONENT = {
    "id": "p1",
    "model": "gaussian",
    "parameters": {
        "amplitude": {"value": 1.0, "bounds": [0.0, 3.0], "vary": True},
        "center": {"value": 0.0, "bounds": [-1.0, 1.0], "vary": True},
        "fwhmg": {"value": 0.3, "bounds": [0.05, 1.0], "vary": True},
    },
}
_SPECTRUM_CFG = {"infile": "s1.csv", "components": [_COMPONENT]}


class TestBatchFittingConfig:
    """BatchFittingConfig validates multi-spectrum batch input."""

    def test_minimal(self) -> None:
        b = BatchFittingConfig(configs=[_SPECTRUM_CFG])
        assert b.n_spectra == 1
        assert b.workers == 1

    def test_multiple_spectra(self) -> None:
        b = BatchFittingConfig(
            configs=[_SPECTRUM_CFG, {**_SPECTRUM_CFG, "infile": "s2.csv"}],
            workers=2,
        )
        assert b.n_spectra == 2
        assert b.workers == 2

    def test_workers_capped_at_64(self) -> None:
        with pytest.raises(Exception):
            BatchFittingConfig(configs=[_SPECTRUM_CFG], workers=65)

    def test_empty_configs_rejected(self) -> None:
        with pytest.raises(Exception):
            BatchFittingConfig(configs=[])

    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            BatchFittingConfig(configs=[_SPECTRUM_CFG], unknown=True)  # type: ignore[call-arg]

    def test_fail_fast_default_false(self) -> None:
        b = BatchFittingConfig(configs=[_SPECTRUM_CFG])
        assert b.fail_fast is False

    def test_timeout_default_none(self) -> None:
        b = BatchFittingConfig(configs=[_SPECTRUM_CFG])
        assert b.timeout is None

    def test_timeout_custom(self) -> None:
        b = BatchFittingConfig(configs=[_SPECTRUM_CFG], timeout=30.0)
        assert b.timeout == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# UnifiedFittingConfig + MCMCConfig integration
# ---------------------------------------------------------------------------


class TestUnifiedFittingConfigMCMC:
    """MCMCConfig is accepted as optional field in UnifiedFittingConfig."""

    def test_mcmc_none_by_default(self) -> None:
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        cfg = UnifiedFittingConfig.model_validate(
            {
                "components": [
                    {
                        "id": "p1",
                        "model": "gaussian",
                        "parameters": {
                            "amplitude": {"value": 1.0, "bounds": [0.0, 3.0]},
                            "center": {"value": 0.0, "bounds": [-1.0, 1.0]},
                            "fwhmg": {"value": 0.3, "bounds": [0.05, 1.0]},
                        },
                    }
                ]
            }
        )
        assert cfg.mcmc is None

    def test_mcmc_accepted_with_emcee_method(self) -> None:
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        cfg = UnifiedFittingConfig.model_validate(
            {
                "optimizer": {"method": "emcee"},
                "mcmc": {"nwalkers": 50, "steps": 200, "burn": 50, "progress": False},
                "components": [
                    {
                        "id": "p1",
                        "model": "gaussian",
                        "parameters": {
                            "amplitude": {"value": 1.0, "bounds": [0.0, 3.0]},
                            "center": {"value": 0.0, "bounds": [-1.0, 1.0]},
                            "fwhmg": {"value": 0.3, "bounds": [0.05, 1.0]},
                        },
                    }
                ],
            }
        )
        assert cfg.optimizer.method == "emcee"
        assert cfg.mcmc is not None
        assert cfg.mcmc.nwalkers == 50
        assert cfg.mcmc.steps == 200


# ---------------------------------------------------------------------------
# Phase 1a: FitInsights sub-models
# ---------------------------------------------------------------------------


class TestVariableFitResult:
    """VariableFitResult holds per-parameter fitted values."""

    @pytest.mark.unit
    def test_all_none_defaults(self) -> None:
        v = VariableFitResult()
        assert v.init_value is None
        assert v.model_value is None
        assert v.best_value is None
        assert v.stderr is None

    @pytest.mark.unit
    def test_with_values(self) -> None:
        v = VariableFitResult(init_value=1.0, best_value=0.98, stderr=0.02)
        assert v.best_value == pytest.approx(0.98)
        assert v.stderr == pytest.approx(0.02)

    @pytest.mark.unit
    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            VariableFitResult(unknown=99)  # type: ignore[call-arg]

    @pytest.mark.unit
    def test_json_round_trip(self) -> None:
        v = VariableFitResult(init_value=1.0, best_value=0.98, stderr=0.02)
        v2 = VariableFitResult.model_validate(v.model_dump())
        assert v2.best_value == v.best_value


class TestFitConfigurations:
    """FitConfigurations captures the solver config at fit time."""

    @pytest.mark.unit
    def test_defaults(self) -> None:
        c = FitConfigurations()
        assert c.method == ""
        assert c.max_nfev == 0
        assert c.nan_policy == "raise"

    @pytest.mark.unit
    def test_custom(self) -> None:
        c = FitConfigurations(method="leastsq", max_nfev=1000, nan_policy="propagate")
        assert c.method == "leastsq"
        assert c.max_nfev == 1000

    @pytest.mark.unit
    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            FitConfigurations(unknown="x")  # type: ignore[call-arg]


class TestFitInsights:
    """FitInsights replaces the raw fit_insights dict."""

    _LEGACY: dict[str, object] = {
        "configurations": {"method": "leastsq", "max_nfev": 0, "nan_policy": "raise"},
        "statistics": {"chisqr": 0.05, "redchi": 0.0005},
        "variables": {
            "p1_amplitude": {
                "init_value": 1.0,
                "model_value": 0.99,
                "best_value": 0.98,
                "stderr": 0.02,
            }
        },
        "errorbars": {"p1_amplitude": "True"},
        "correlations": {"p1_amplitude": {"p1_center": 0.1}},
        "covariance_matrix": {"p1_amplitude": {"p1_amplitude": 0.0004}},
        "computational": {"runtime_s": 0.12},
    }

    @pytest.mark.unit
    def test_empty_defaults(self) -> None:
        fi = FitInsights()
        assert fi.statistics == {}
        assert fi.variables == {}
        assert fi.errorbars == {}

    @pytest.mark.unit
    def test_full_construction(self) -> None:
        fi = FitInsights.model_validate(self._LEGACY)
        assert fi.statistics["chisqr"] == pytest.approx(0.05)
        assert "p1_amplitude" in fi.variables
        assert fi.variables["p1_amplitude"].best_value == pytest.approx(0.98)
        assert fi.errorbars["p1_amplitude"] == "True"
        assert fi.correlations["p1_amplitude"]["p1_center"] == pytest.approx(0.1)
        assert fi.configurations.method == "leastsq"

    @pytest.mark.unit
    def test_json_round_trip(self) -> None:
        fi = FitInsights.model_validate(self._LEGACY)
        fi2 = FitInsights.model_validate(fi.model_dump())
        assert fi2.statistics == fi.statistics

    @pytest.mark.unit
    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            FitInsights(unknown_field=99)  # type: ignore[call-arg]


class TestDataSummary:
    """DataSummary wraps regression metrics and descriptive stats."""

    _LEGACY: dict[str, object] = {
        "regression_metrics": {"index": [0, 1], "columns": ["r2", "rmse"], "data": [[0.99], [0.01]]},
        "descriptive_statistic": {"index": [0, 1], "columns": ["mean", "std"], "data": [[0.5], [0.1]]},
        "linear_correlation": {"index": [0], "columns": ["pearson_r"], "data": [[0.98]]},
    }

    @pytest.mark.unit
    def test_empty_defaults(self) -> None:
        ds = DataSummary()
        assert ds.regression_metrics["data"] == []
        assert ds.descriptive_statistic["data"] == []
        assert ds.linear_correlation["data"] == []

    @pytest.mark.unit
    def test_direct_construction(self) -> None:
        ds = DataSummary(
            regression_metrics=self._LEGACY["regression_metrics"],
            descriptive_statistic=self._LEGACY["descriptive_statistic"],
            linear_correlation=self._LEGACY["linear_correlation"],
        )
        assert ds.regression_metrics["columns"] == ["r2", "rmse"]
        assert ds.descriptive_statistic["columns"] == ["mean", "std"]
        assert ds.linear_correlation["columns"] == ["pearson_r"]

    @pytest.mark.unit
    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            DataSummary(unknown_field=99)  # type: ignore[call-arg]

    @pytest.mark.unit
    def test_json_round_trip(self) -> None:
        ds = DataSummary(
            regression_metrics=self._LEGACY["regression_metrics"],
            descriptive_statistic=self._LEGACY["descriptive_statistic"],
            linear_correlation=self._LEGACY["linear_correlation"],
        )
        ds2 = DataSummary.model_validate(ds.model_dump())
        assert ds2.regression_metrics == ds.regression_metrics


class TestConfidenceResults:
    """ConfidenceResults captures conf_interval settings and results."""

    @pytest.mark.unit
    def test_disabled_by_default(self) -> None:
        cr = ConfidenceResults()
        assert cr.settings is False
        assert cr.results == {}

    @pytest.mark.unit
    def test_enabled_with_settings(self) -> None:
        cr = ConfidenceResults(
            settings={"sigmas": [1, 2, 3], "verbose": True},
            results={"p1_amplitude": [(0.95, 0.99)]},
        )
        assert isinstance(cr.settings, dict)
        assert cr.results["p1_amplitude"] == [(0.95, 0.99)]

    @pytest.mark.unit
    def test_extra_fields_forbidden(self) -> None:
        with pytest.raises(Exception):
            ConfidenceResults(unknown=True)  # type: ignore[call-arg]

    @pytest.mark.unit
    def test_json_round_trip(self) -> None:
        cr = ConfidenceResults(settings={"sigmas": [1, 2]}, results={"p1": [(0.95, 0.05)]})
        cr2 = ConfidenceResults.model_validate(cr.model_dump())
        assert cr2.results == cr.results


class TestFitResultExtended:
    """Phase 1a — FitResult extended fields: global_fitting, fit_insights, etc."""

    @pytest.mark.unit
    def test_new_fields_have_defaults(self) -> None:
        r = FitResult()
        assert r.global_fitting == FittingMode.STANDARD
        assert isinstance(r.fit_insights, FitInsights)
        assert isinstance(r.data_summary, DataSummary)
        assert isinstance(r.confidence, ConfidenceResults)

    @pytest.mark.unit
    def test_global_fitting_coerced_from_int(self) -> None:
        # int 1 → GLOBAL; 0 → STANDARD
        assert FitResult(global_fitting=1).global_fitting == FittingMode.GLOBAL
        assert FitResult(global_fitting=0).global_fitting == FittingMode.STANDARD

    @pytest.mark.unit
    def test_direct_construction_minimal(self) -> None:
        r = FitResult(global_fitting=0)
        assert r.global_fitting == FittingMode.STANDARD
        assert r.fit_insights.statistics == {}

    @pytest.mark.unit
    def test_direct_construction_full(self) -> None:
        r = FitResult(
            global_fitting=0,
            fit_insights=FitInsights(
                statistics={"chisqr": 0.05},
                errorbars={"p1_amplitude": "True"},
            ),
            data_summary=DataSummary(
                regression_metrics=DataSplitDict(data=[[0.99]], index=[0], columns=["r2"]),
            ),
            confidence=ConfidenceResults(settings=False),
        )
        assert r.fit_insights.statistics["chisqr"] == pytest.approx(0.05)
        assert r.fit_insights.errorbars["p1_amplitude"] == "True"
        assert r.data_summary.regression_metrics["columns"] == ["r2"]
        assert r.confidence.settings is False

    @pytest.mark.unit
    def test_json_schema_includes_new_fields(self) -> None:
        schema = FitResult.model_json_schema()
        props = schema["properties"]
        for field in ("global_fitting", "fit_insights", "data_summary", "confidence"):
            assert field in props, f"Missing field: {field}"

    @pytest.mark.unit
    def test_save_load_with_insights(self, tmp_path: Path) -> None:
        r = FitResult(
            global_fitting=False,
            fit_insights=FitInsights(statistics={"chisqr": 0.05}),
        )
        path = tmp_path / "extended.json"
        r.save(path)
        r2 = FitResult.load(path)
        assert r2.fit_insights.statistics["chisqr"] == pytest.approx(0.05)

    @pytest.mark.unit
    def test_full_json_round_trip(self) -> None:
        r = FitResult(
            global_fitting=1,
            fit_insights=FitInsights(
                statistics={"redchi": 0.0005},
                errorbars={"p1_amp": "True"},
            ),
            data_summary=DataSummary(regression_metrics=DataSplitDict(data=[[0.99]], index=[0], columns=["r2"])),
            confidence=ConfidenceResults(settings=False),
        )
        dumped = r.model_dump(mode="json")
        r2 = FitResult.from_dict(dumped)
        assert r2.global_fitting == FittingMode.GLOBAL
        assert r2.fit_insights.errorbars["p1_amp"] == "True"
        assert r2.data_summary.regression_metrics["columns"] == ["r2"]

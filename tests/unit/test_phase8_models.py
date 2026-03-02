"""Tests for Phase 8 models: FitResult, MCMCConfig, BatchFittingConfig."""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from spectrafit.models.batch_config import BatchFittingConfig
from spectrafit.models.fit_result import ComponentResult
from spectrafit.models.fit_result import FitResult
from spectrafit.models.fit_result import FitStatistics
from spectrafit.models.fit_result import ParameterResult
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

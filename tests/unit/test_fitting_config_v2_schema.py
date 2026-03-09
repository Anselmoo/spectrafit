"""Tests for v2 [[components]] input schema in UnifiedFittingConfig.

Validates that the prototype TOML schema (flat [[components]] array with
bounds=[min,max] shorthand, [data] block, and [solver] block) is accepted
natively by UnifiedFittingConfig and produces a correct CompositeModelBundle.
"""

from __future__ import annotations

import math

from pathlib import Path

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.peak_models import FitParameter


# ---------------------------------------------------------------------------
# FitParameter — bounds shorthand
# ---------------------------------------------------------------------------


class TestFitParameterBounds:
    """bounds=[min, max] shorthand expands to min/max fields."""

    def test_bounds_expands_to_min_max(self) -> None:
        p = FitParameter.model_validate(
            {"value": 1.0, "bounds": [0.0, 3.0], "vary": True}
        )
        assert p.min == 0.0
        assert p.max == 3.0
        assert p.value == 1.0
        assert p.vary is True

    def test_bounds_does_not_override_explicit_min_max(self) -> None:
        # setdefault semantics: explicit min/max win over bounds
        p = FitParameter.model_validate(
            {"value": 1.0, "bounds": [0.0, 3.0], "min": -1.0, "max": 5.0}
        )
        assert p.min == -1.0
        assert p.max == 5.0

    def test_no_bounds_uses_inf_defaults(self) -> None:
        p = FitParameter.model_validate({"value": 0.5})
        assert p.min == -math.inf
        assert p.max == math.inf

    def test_expr_dot_notation_translated(self) -> None:
        p = FitParameter.model_validate(
            {
                "value": 0.5,
                "bounds": [0.0, 1.0],
                "vary": False,
                "expr": "p1.center + 1.0",
            }
        )
        assert p.expr == "p1_center + 1.0"


# ---------------------------------------------------------------------------
# UnifiedFittingConfig — v2 [[components]] format
# ---------------------------------------------------------------------------

_V2_DICT: dict = {
    "schema_version": "1.0",
    "config_type": "peak_fit",
    "meta": {"description": "test"},
    "data": {"infile": "synth.csv", "x_col": "energy", "y_col": "intensity"},
    "solver": {
        "method": "leastsq",
        "max_nfev": 500,
        "nan_policy": "omit",
        "calc_covar": False,
    },
    "components": [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"value": 1.0, "bounds": [0.0, 3.0], "vary": True},
                "center": {"value": -0.5, "bounds": [-2.0, 0.0], "vary": True},
                "fwhmg": {"value": 0.3, "bounds": [0.05, 1.0], "vary": True},
            },
        },
        {
            "id": "bg",
            "model": "linear",
            "parameters": {
                "slope": {"value": 0.0, "bounds": [-0.5, 0.5], "vary": False},
                "intercept": {"value": 0.02, "bounds": [0.0, 0.2], "vary": True},
            },
        },
    ],
}


class TestUnifiedFittingConfigV2Schema:
    """V2 [[components]] dict is accepted and produces the correct model."""

    def test_accepts_v2_dict(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert cfg is not None

    def test_components_list_length(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert len(cfg.components) == 2

    def test_component_ids(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        ids = [c.id for c in cfg.components]
        assert ids == ["p1", "bg"]

    def test_component_models(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert cfg.components[0].model == "gaussian"
        assert cfg.components[1].model == "linear"

    def test_data_block_maps_to_column(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert cfg.column.x == "energy"
        assert cfg.column.y == "intensity"

    def test_data_block_maps_infile(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert cfg.infile == Path("synth.csv")

    def test_solver_block_maps_to_optimizer(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert cfg.optimizer.method == "leastsq"
        assert cfg.optimizer.max_nfev == 500

    def test_solver_block_maps_to_minimizer(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        assert cfg.minimizer.nan_policy == "omit"
        assert cfg.minimizer.calc_covar is False

    def test_prototype_metadata_stripped(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        # With extra="forbid", model_extra is None — unknown keys are rejected at parse time.
        assert cfg.model_extra is None

    def test_bounds_shorthand_in_parameters(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        p1 = cfg.components[0]
        amp = p1.parameters["amplitude"]
        assert amp.min == 0.0
        assert amp.max == 3.0

    def test_build_composite_model_produces_bundle(self) -> None:
        cfg = UnifiedFittingConfig.model_validate(_V2_DICT)
        bundle = cfg.build_composite_model()
        assert "p1_amplitude" in bundle.params
        assert "p1_center" in bundle.params
        assert "bg_slope" in bundle.params

    def test_expr_constraint_via_v2_schema(self) -> None:
        data = {
            "components": [
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "bounds": [0.0, 3.0]},
                        "center": {"value": 0.0, "bounds": [-1.0, 1.0]},
                        "fwhmg": {"value": 0.3, "bounds": [0.05, 1.0]},
                    },
                },
                {
                    "id": "p2",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 0.8, "bounds": [0.0, 3.0]},
                        "center": {
                            "value": 0.5,
                            "bounds": [0.0, 2.0],
                            "vary": False,
                            "expr": "p1.center + 1.0",
                        },
                        "fwhmg": {"value": 0.25, "bounds": [0.05, 1.0]},
                    },
                },
            ]
        }
        cfg = UnifiedFittingConfig.model_validate(data)
        center_p2 = cfg.components[1].parameters["center"]
        assert center_p2.expr == "p1_center + 1.0"

    def test_v2_from_file(self, tmp_path: Path) -> None:
        toml_content = """\
schema_version = "1.0"
config_type    = "peak_fit"

[data]
infile = "synth.csv"
x_col  = "energy"
y_col  = "intensity"

[solver]
method     = "leastsq"
max_nfev   = 1000
nan_policy = "propagate"
calc_covar = true

[[components]]
id    = "p1"
model = "gaussian"

[components.parameters]
amplitude = { value = 1.0, bounds = [0.0, 3.0], vary = true }
center    = { value = 0.0, bounds = [-1.0, 1.0], vary = true }
fwhmg     = { value = 0.3, bounds = [0.05, 1.0], vary = true }
"""
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(toml_content)
        cfg = UnifiedFittingConfig.from_file(toml_file)
        assert len(cfg.components) == 1
        assert cfg.components[0].model == "gaussian"


# ---------------------------------------------------------------------------
# Error: components required
# ---------------------------------------------------------------------------


class TestValidateComponentsNonEmpty:
    def test_empty_config_raises(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            UnifiedFittingConfig.model_validate({})

    def test_v1_peaks_rejected(self) -> None:
        with pytest.raises(Exception):  # noqa: B017
            UnifiedFittingConfig.model_validate(
                {
                    "peaks": {
                        "1": {
                            "gaussian": {
                                "amplitude": {"value": 1.0},
                            }
                        }
                    }
                }
            )

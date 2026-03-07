"""Phase 6.5 tests: computed fields (components, context) and build_composite_model.

These tests verify the new Pydantic-first path added to UnifiedFittingConfig:
- ``components`` computed field: auto-migration from legacy ``peaks`` dict
- ``context`` computed field: FittingContext derived from ``global_`` flag
- ``build_composite_model()``: delegates to build_composite_bundle
"""

from __future__ import annotations

import numpy as np
import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_PEAKS: dict = {
    "1": {
        "gaussian": {
            "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
            "center": {"min": -1, "max": 1, "value": 0.0, "vary": True},
            "fwhmg": {"min": 0.1, "max": 2.0, "value": 0.7, "vary": True},
        }
    }
}

TWO_PEAK_PEAKS: dict = {
    "1": {
        "gaussian": {
            "amplitude": {"value": 1.0, "min": 0, "max": 2, "vary": True},
            "center": {"value": -0.5, "min": -2, "max": 0, "vary": True},
            "fwhmg": {"value": 0.5, "min": 0.1, "max": 2.0, "vary": True},
        }
    },
    "2": {
        "lorentzian": {
            "amplitude": {"value": 0.8, "min": 0, "max": 2, "vary": True},
            "center": {"value": 0.5, "min": 0, "max": 2, "vary": True},
            "fwhml": {"value": 0.4, "min": 0.1, "max": 2.0, "vary": True},
        }
    },
}


@pytest.fixture
def cfg_single() -> UnifiedFittingConfig:
    """Single gaussian peak config."""
    return UnifiedFittingConfig(peaks=MINIMAL_PEAKS)


@pytest.fixture
def cfg_two() -> UnifiedFittingConfig:
    """Two-peak config: gaussian + lorentzian."""
    return UnifiedFittingConfig(peaks=TWO_PEAK_PEAKS)


# ---------------------------------------------------------------------------
# components computed field
# ---------------------------------------------------------------------------


class TestComponentsComputedField:
    def test_single_peak_yields_one_component(
        self, cfg_single: UnifiedFittingConfig
    ) -> None:
        assert len(cfg_single.components) == 1

    def test_two_peaks_yield_two_components(
        self, cfg_two: UnifiedFittingConfig
    ) -> None:
        assert len(cfg_two.components) == 2

    def test_component_type(self, cfg_single: UnifiedFittingConfig) -> None:
        assert isinstance(cfg_single.components[0], Component)

    def test_id_sanitized(self, cfg_single: UnifiedFittingConfig) -> None:
        # peak id "1" → sanitized to "p1"
        assert cfg_single.components[0].id == "p1"

    def test_model_name(self, cfg_single: UnifiedFittingConfig) -> None:
        assert cfg_single.components[0].model == "gaussian"

    def test_parameters_are_fit_parameter(
        self, cfg_single: UnifiedFittingConfig
    ) -> None:
        for param in cfg_single.components[0].parameters.values():
            assert isinstance(param, FitParameter)

    def test_amplitude_value(self, cfg_single: UnifiedFittingConfig) -> None:
        assert cfg_single.components[0].parameters["amplitude"].value == 1.0

    def test_amplitude_min(self, cfg_single: UnifiedFittingConfig) -> None:
        assert cfg_single.components[0].parameters["amplitude"].min == 0.0

    def test_amplitude_max(self, cfg_single: UnifiedFittingConfig) -> None:
        assert cfg_single.components[0].parameters["amplitude"].max == 2.0

    def test_amplitude_vary(self, cfg_single: UnifiedFittingConfig) -> None:
        assert cfg_single.components[0].parameters["amplitude"].vary is True

    def test_two_components_ids(self, cfg_two: UnifiedFittingConfig) -> None:
        ids = {c.id for c in cfg_two.components}
        assert ids == {"p1", "p2"}

    def test_two_components_models(self, cfg_two: UnifiedFittingConfig) -> None:
        models = {c.model for c in cfg_two.components}
        assert models == {"gaussian", "lorentzian"}

    def test_components_is_fresh_each_call(
        self, cfg_single: UnifiedFittingConfig
    ) -> None:
        # computed_field: each access returns a new list (by value, not cached)
        c1 = cfg_single.components
        c2 = cfg_single.components
        assert c1 == c2

    def test_expr_field_translated(self) -> None:
        """dot-notation expr in peaks is translated when migrated."""
        peaks = {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True},
                    "center": {
                        "value": 0.0,
                        "vary": False,
                        "expr": "p1.amplitude * 0.5",
                    },
                    "fwhmg": {"value": 0.5, "vary": True},
                }
            }
        }
        cfg = UnifiedFittingConfig(peaks=peaks)
        expr = cfg.components[0].parameters["center"].expr
        # dot-notation should be translated to underscore
        assert expr == "p1_amplitude * 0.5"


# ---------------------------------------------------------------------------
# context computed field
# ---------------------------------------------------------------------------


class TestContextComputedField:
    def test_default_global_gives_standard_mode(
        self, cfg_single: UnifiedFittingConfig
    ) -> None:
        assert cfg_single.context.mode == FittingMode.STANDARD

    def test_standard_n_datasets_is_1(self, cfg_single: UnifiedFittingConfig) -> None:
        assert cfg_single.context.n_datasets == 1

    def test_global_1_gives_global_mode(self) -> None:
        cfg = UnifiedFittingConfig(peaks=MINIMAL_PEAKS, **{"global": 1})
        assert cfg.context.mode == FittingMode.GLOBAL

    def test_global_2_gives_global_mode(self) -> None:
        cfg = UnifiedFittingConfig(peaks=MINIMAL_PEAKS, **{"global": 2})
        assert cfg.context.mode == FittingMode.GLOBAL

    def test_global_int_roundtrip(self, cfg_single: UnifiedFittingConfig) -> None:
        # global_int is 0 for STANDARD, 1 for GLOBAL — no longer an IntEnum
        from spectrafit.models.fitting_context import FittingMode

        expected = 0 if cfg_single.global_ == FittingMode.STANDARD else 1
        assert cfg_single.context.global_int == expected


# ---------------------------------------------------------------------------
# build_composite_model
# ---------------------------------------------------------------------------


class TestBuildCompositeModel:
    def test_returns_bundle(self, cfg_single: UnifiedFittingConfig) -> None:
        from spectrafit.models.bundle import CompositeModelBundle

        bundle = cfg_single.build_composite_model()
        assert isinstance(bundle, CompositeModelBundle)

    def test_params_contain_p1_amplitude(
        self, cfg_single: UnifiedFittingConfig
    ) -> None:
        bundle = cfg_single.build_composite_model()
        assert "p1_amplitude" in bundle.params

    def test_params_contain_p1_center(self, cfg_single: UnifiedFittingConfig) -> None:
        bundle = cfg_single.build_composite_model()
        assert "p1_center" in bundle.params

    def test_two_peak_bundle_has_both_prefixes(
        self, cfg_two: UnifiedFittingConfig
    ) -> None:
        bundle = cfg_two.build_composite_model()
        assert "p1_amplitude" in bundle.params
        assert "p2_amplitude" in bundle.params

    def test_parts_count_matches_components(
        self, cfg_two: UnifiedFittingConfig
    ) -> None:
        bundle = cfg_two.build_composite_model()
        assert len(bundle.parts) == 2

    def test_decompose_curves_sum_to_composite(
        self, cfg_two: UnifiedFittingConfig
    ) -> None:
        bundle = cfg_two.build_composite_model()
        x = np.linspace(-3, 3, 50)
        result = bundle.composite.fit(
            np.zeros(50),
            bundle.params,
            x=x,
        )
        component_curves = bundle.decompose(result.params, x)
        total = sum(component_curves.values())
        expected = bundle.composite.eval(result.params, x=x)
        np.testing.assert_allclose(total, expected, rtol=1e-10)

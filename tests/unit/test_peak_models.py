"""Tests for Phase 6.1/6.2 — ModelInfo.make_lmfit_model and Component pipeline.

Verifies:
- REGISTRY.get(name).make_lmfit_model(prefix) produces correct parameter keys
- Component.id is auto-sanitized
- Component.to_lmfit_model() delegates to registry
- Component.apply_parameters() overrides defaults correctly
- FitParameter.expr dot-notation is translated at parse time
- Unknown model raises ValueError
"""

from __future__ import annotations

import math

import pytest

from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.registry import REGISTRY


class TestMakeLmfitModel:
    """ModelInfo.make_lmfit_model — registry integration."""

    @pytest.mark.parametrize(
        ("model_name", "prefix", "expected_keys"),
        [
            ("gaussian", "p1_", ["p1_amplitude", "p1_center", "p1_fwhmg"]),
            ("lorentzian", "main_", ["main_amplitude", "main_center", "main_fwhml"]),
            (
                "pseudovoigt",
                "bg_",
                ["bg_amplitude", "bg_center", "bg_fwhmg", "bg_fwhml"],
            ),
            ("linear", "lin_", ["lin_intercept", "lin_slope"]),
            ("constant", "c_", ["c_amplitude"]),
        ],
    )
    def test_param_keys(
        self, model_name: str, prefix: str, expected_keys: list[str]
    ) -> None:
        """make_lmfit_model produces the expected parameter key set."""
        m = REGISTRY.get(model_name).make_lmfit_model(prefix)
        assert sorted(m.make_params().keys()) == sorted(expected_keys)

    def test_all_registry_models_wrap_without_error(self) -> None:
        """Every model in the registry can be wrapped in lmfit.Model."""
        for name in REGISTRY.names():
            m = REGISTRY.get(name).make_lmfit_model("t_")
            params = m.make_params()
            assert len(params) > 0, f"Model '{name}' produced no parameters"


class TestFitParameter:
    """FitParameter validation and expr translation."""

    def test_defaults(self) -> None:
        p = FitParameter()
        assert p.value == 0.0
        assert p.min == -math.inf
        assert p.max == math.inf
        assert p.vary is True
        assert p.expr is None

    def test_expr_dot_notation_translated(self) -> None:
        p = FitParameter(value=0.5, expr="main.amplitude * 0.5")
        assert p.expr == "main_amplitude * 0.5"

    def test_expr_already_underscore_unchanged(self) -> None:
        p = FitParameter(value=0.5, expr="main_amplitude * 0.5")
        assert p.expr == "main_amplitude * 0.5"

    def test_expr_none_accepted(self) -> None:
        p = FitParameter(value=1.0, expr=None)
        assert p.expr is None

    def test_apply_to_overrides_defaults(self) -> None:

        info = REGISTRY.get("gaussian")
        m = info.make_lmfit_model("p1_")
        params = m.make_params()

        fp = FitParameter(value=1.5, min=0.5, max=3.0, vary=True)
        fp.apply_to(params, "p1_amplitude")

        assert params["p1_amplitude"].value == pytest.approx(1.5)
        assert params["p1_amplitude"].min == pytest.approx(0.5)
        assert params["p1_amplitude"].max == pytest.approx(3.0)
        assert params["p1_amplitude"].vary is True

    def test_apply_to_vary_false(self) -> None:

        info = REGISTRY.get("gaussian")
        m = info.make_lmfit_model("p1_")
        params = m.make_params()

        fp = FitParameter(value=0.0, vary=False)
        fp.apply_to(params, "p1_center")
        assert params["p1_center"].vary is False


class TestComponent:
    """Component — id sanitization, model lookup, parameter application."""

    def test_numeric_id_sanitized(self) -> None:
        comp = Component(id="1", model="gaussian", parameters={})
        assert comp.id == "p1"

    def test_alpha_id_unchanged(self) -> None:
        comp = Component(id="main", model="gaussian", parameters={})
        assert comp.id == "main"

    def test_unknown_model_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown model"):
            Component(id="1", model="nonexistent_model_xyz", parameters={})

    def test_to_lmfit_model_returns_correct_params(self) -> None:
        comp = Component(id="1", model="gaussian", parameters={})
        lm = comp.to_lmfit_model()
        keys = sorted(lm.make_params().keys())
        assert keys == ["p1_amplitude", "p1_center", "p1_fwhmg"]

    def test_apply_parameters_overrides(self) -> None:
        comp = Component(
            id="main",
            model="gaussian",
            parameters={
                "amplitude": FitParameter(value=2.0, min=0.1, max=5.0),
                "center": FitParameter(value=0.5, min=-1.0, max=1.0, vary=False),
            },
        )
        lm = comp.to_lmfit_model()
        params = lm.make_params()
        comp.apply_parameters(params)

        assert params["main_amplitude"].value == pytest.approx(2.0)
        assert params["main_amplitude"].min == pytest.approx(0.1)
        assert params["main_center"].value == pytest.approx(0.5)
        assert params["main_center"].vary is False

    def test_apply_parameters_ignores_unknown_fields(self) -> None:
        """apply_parameters should not crash for unknown field names."""
        comp = Component(
            id="1",
            model="gaussian",
            parameters={
                "amplitude": FitParameter(value=1.0),
                "nonexistent_field": FitParameter(value=99.0),
            },
        )
        lm = comp.to_lmfit_model()
        params = lm.make_params()
        comp.apply_parameters(params)  # must not raise
        # amplitude was overridden
        assert params["p1_amplitude"].value == pytest.approx(1.0)

    def test_component_lmfit_name_via_naming(self) -> None:
        """lmfit_param_name(comp.id, field) gives the expected key."""
        from spectrafit.models.naming import lmfit_param_name

        comp = Component(id="bg", model="linear", parameters={})
        assert lmfit_param_name(comp.id, "slope") == "bg_slope"

    def test_component_model_validates_all_registry_names(self) -> None:
        """Every registered model name can be used as component model."""
        for name in REGISTRY.names():
            comp = Component(id="test", model=name, parameters={})
            assert comp.model == name

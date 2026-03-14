"""Golden-table unit tests for new-config v2 scaffolding (Phase 11a)."""

from __future__ import annotations

import pytest

from spectrafit.cli.commands.scaffolding import _build_component
from spectrafit.cli.commands.scaffolding import _build_config
from spectrafit.cli.commands.scaffolding import _build_config_model
from spectrafit.cli.commands.scaffolding import _default_for_param
from spectrafit.cli.main import app
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from typer.testing import CliRunner


runner = CliRunner()


class TestDefaultForParam:
    """Tests for _default_for_param() return types."""

    @pytest.mark.unit
    def test_returns_fit_parameter(self) -> None:
        p = _default_for_param("amplitude")
        assert isinstance(p, FitParameter)

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("name", "expected_value", "expected_min", "expected_max"),
        [
            ("amplitude", 1.0, 0.0, 2.0),
            ("center", 0.0, -2.0, 2.0),
            ("fwhmg", 0.1, 0.02, 0.5),
            ("fwhml", 0.1, 0.01, 0.5),
            ("fwhmv", 0.1, 0.02, 0.5),
            ("gamma", 0.5, 0.0, 1.0),
        ],
    )
    def test_known_param_values(
        self,
        name: str,
        expected_value: float,
        expected_min: float,
        expected_max: float,
    ) -> None:
        p = _default_for_param(name)
        assert p.value == expected_value
        assert p.min == expected_min
        assert p.max == expected_max
        assert p.vary is True

    @pytest.mark.unit
    def test_unknown_param_fallback(self) -> None:
        p = _default_for_param("nonexistent_param_xyz")
        assert isinstance(p, FitParameter)
        assert p.value == 0.0
        assert p.min == -1.0
        assert p.max == 1.0


class TestBuildComponent:
    """Tests for _build_component() — produces Component instances."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("model", "num", "expected_params"),
        [
            ("gaussian", 1, ["amplitude", "center", "fwhmg"]),
            ("lorentzian", 2, ["amplitude", "center", "fwhml"]),
            ("voigt", 3, ["center", "fwhmv", "gamma"]),
            ("pseudovoigt", 1, ["amplitude", "center", "fwhmg", "fwhml"]),
        ],
    )
    def test_returns_component(
        self,
        model: str,
        num: int,
        expected_params: list[str],
    ) -> None:
        comp = _build_component(model, num)
        assert isinstance(comp, Component)
        assert comp.id == f"p{num}"
        assert comp.model == model
        for p in expected_params:
            assert p in comp.parameters, f"expected param '{p}' in {list(comp.parameters)}"
        assert all(isinstance(v, FitParameter) for v in comp.parameters.values())


class TestBuildConfig:
    """Golden-table tests for _build_config() v2 output format."""

    @pytest.mark.unit
    def test_build_config_model_returns_typed_config(self) -> None:
        config = _build_config_model([(1, "gaussian"), (2, "voigt")])

        assert isinstance(config, UnifiedFittingConfig)
        assert [component.id for component in config.components] == ["p1", "p2"]
        assert config.optimizer.method == "leastsq"
        assert config.minimizer.nan_policy == "propagate"

    @pytest.mark.unit
    def test_v2_format_components_key(self) -> None:
        """Output must have 'components' key — never 'fitting' (v1 banned)."""
        cfg = _build_config([(1, "gaussian")])
        assert "components" in cfg
        assert "fitting" not in cfg

    @pytest.mark.unit
    def test_has_minimizer_and_optimizer(self) -> None:
        cfg = _build_config([(1, "gaussian")])
        assert "minimizer" in cfg
        assert "optimizer" in cfg

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("model", "n", "expected_params"),
        [
            ("gaussian", 1, ["amplitude", "center", "fwhmg"]),
            ("voigt", 2, ["center", "fwhmv", "gamma"]),
            ("lorentzian", 3, ["amplitude", "center", "fwhml"]),
        ],
    )
    def test_golden_table(
        self,
        model: str,
        n: int,
        expected_params: list[str],
    ) -> None:
        cfg = _build_config([(i + 1, model) for i in range(n)])
        assert "components" in cfg
        assert "fitting" not in cfg
        comps = cfg["components"]
        assert isinstance(comps, list)
        assert len(comps) == n
        first = comps[0]
        assert isinstance(first, dict)
        assert first["id"] == "p1"
        assert first["model"] == model
        for p in expected_params:
            assert p in first["parameters"], f"missing param '{p}'"

    @pytest.mark.unit
    def test_component_ids_sequential(self) -> None:
        cfg = _build_config([(i + 1, "gaussian") for i in range(5)])
        ids = [c["id"] for c in cfg["components"]]
        assert ids == ["p1", "p2", "p3", "p4", "p5"]

    @pytest.mark.unit
    def test_round_trip_unified_fitting_config(self) -> None:
        """Config produced by _build_config must validate through UnifiedFittingConfig."""
        cfg = _build_config([(1, "voigt"), (2, "gaussian")])
        unified = UnifiedFittingConfig.model_validate(cfg)
        assert len(unified.components) == 2
        assert unified.components[0].model == "voigt"
        assert unified.components[1].model == "gaussian"

    @pytest.mark.unit
    def test_serialized_build_config_matches_typed_model_dump(self) -> None:
        typed = _build_config_model([(1, "voigt"), (2, "gaussian")])

        assert _build_config([(1, "voigt"), (2, "gaussian")]) == typed.model_dump(
            mode="json",
            exclude_none=True,
        )

    @pytest.mark.unit
    def test_no_none_values_in_component_dump(self) -> None:
        """model_dump(exclude_none=True) must produce TOML-safe dicts (no None)."""
        cfg = _build_config([(1, "voigt")])
        comp = cfg["components"][0]
        assert isinstance(comp, dict)
        for param_dict in comp["parameters"].values():
            assert isinstance(param_dict, dict)
            assert None not in param_dict.values()

    @pytest.mark.unit
    def test_toml_serialisation(self) -> None:
        """Config must be serialisable to TOML without errors."""
        import tomli_w

        cfg = _build_config([(1, "voigt"), (2, "lorentzian")])
        toml_str = tomli_w.dumps(cfg)
        assert "[[components]]" in toml_str
        assert "[minimizer]" in toml_str
        assert "[optimizer]" in toml_str
        assert "fitting" not in toml_str


class TestNewConfigDefaultFormat:
    """Test that new_config defaults to TOML, not JSON."""

    @pytest.mark.unit
    def test_default_fmt_is_toml(self) -> None:
        import inspect

        from spectrafit.cli._types import OutputFormatEnum
        from spectrafit.cli.commands.scaffolding import new_config

        sig = inspect.signature(new_config)
        fmt_default = sig.parameters["fmt"].default
        assert fmt_default == OutputFormatEnum.TOML

    @pytest.mark.unit
    def test_cli_new_config_emits_toml_by_default(self) -> None:
        result = runner.invoke(app, ["new-config"])

        assert result.exit_code == 0
        assert "[[components]]" in result.output

"""Unit tests for :mod:`scripts.migrate_v1_to_v2`.

These tests verify that the migration script correctly converts v1.x input
dicts to the v2 ``[[components]]`` format and that the round-trip through
:class:`~spectrafit.core.fitting_config.UnifiedFittingConfig` succeeds.
"""

from __future__ import annotations

import json
import sys

from pathlib import Path

import pytest


# Add scripts/ to import path so we can import the migration script directly
_SCRIPTS_DIR = Path(__file__).parents[2] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from migrate_v1_to_v2 import (  # noqa: E402
    _build_v2_dict,
    _convert_param_spec,
    _peaks_to_components,
    _read_input,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_V1_PEAKS: dict[str, object] = {
    "1": {
        "gaussian": {
            "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
            "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
            "fwhmg": {"min": 0.01, "max": 1.0, "value": 0.5, "vary": True},
        }
    },
    "bg": {
        "linear": {
            "slope": {"value": 0.0, "vary": False},
            "intercept": {"min": 0.0, "max": 0.5, "value": 0.02, "vary": True},
        }
    },
}

_V1_FULL: dict[str, object] = {
    "fitting": {
        "parameters": {
            "minimizer": {"nan_policy": "propagate", "calc_covar": True},
            "optimizer": {"max_nfev": 1000, "method": "leastsq"},
        },
        "peaks": _V1_PEAKS,
    }
}


# ---------------------------------------------------------------------------
# _convert_param_spec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestConvertParamSpec:
    """Tests for v1 min/max → v2 bounds consolidation."""

    def test_min_max_merged_to_bounds(self) -> None:
        spec = {"min": 0.0, "max": 2.0, "value": 1.0, "vary": True}
        result = _convert_param_spec(spec)
        assert result["bounds"] == [0.0, 2.0]
        assert "min" not in result
        assert "max" not in result

    def test_value_and_vary_preserved(self) -> None:
        spec = {"min": 0.0, "max": 2.0, "value": 1.5, "vary": False}
        result = _convert_param_spec(spec)
        assert result["value"] == 1.5
        assert result["vary"] is False

    def test_no_min_max_unchanged(self) -> None:
        spec = {"value": 0.0, "vary": False}
        result = _convert_param_spec(spec)
        assert result == {"value": 0.0, "vary": False}

    def test_expr_preserved(self) -> None:
        spec = {"value": 0.5, "vary": False, "expr": "p1.center + 1.0"}
        result = _convert_param_spec(spec)
        assert result["expr"] == "p1.center + 1.0"


# ---------------------------------------------------------------------------
# _peaks_to_components
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPeaksToComponents:
    """Tests for v1 peaks dict → v2 components list conversion."""

    @pytest.fixture
    def components(self) -> list[dict[str, object]]:
        return _peaks_to_components(_V1_PEAKS)

    def test_component_count(self, components: list[dict[str, object]]) -> None:
        assert len(components) == 2  # gaussian + linear

    def test_numeric_key_prefixed(self, components: list[dict[str, object]]) -> None:
        ids = [c["id"] for c in components]
        assert "p1" in ids

    def test_named_key_preserved(self, components: list[dict[str, object]]) -> None:
        ids = [c["id"] for c in components]
        assert "bg" in ids

    def test_model_name_preserved(self, components: list[dict[str, object]]) -> None:
        gaussian = next(c for c in components if c["id"] == "p1")
        assert gaussian["model"] == "gaussian"

    def test_parameters_have_bounds(self, components: list[dict[str, object]]) -> None:
        gaussian = next(c for c in components if c["id"] == "p1")
        amp = gaussian["parameters"]["amplitude"]  # type: ignore[index]
        assert "bounds" in amp
        assert "min" not in amp
        assert "max" not in amp


# ---------------------------------------------------------------------------
# _build_v2_dict
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestBuildV2Dict:
    """Tests for final v2 dict construction from migrated v1 dict."""

    @pytest.fixture
    def migrated(self) -> dict[str, object]:
        from spectrafit.models.migration import migrate_v1_format

        return migrate_v1_format(dict(_V1_FULL))

    def test_schema_version_set(self, migrated: dict[str, object]) -> None:
        v2 = _build_v2_dict(migrated)
        assert v2["schema_version"] == "2.0"

    def test_components_present(self, migrated: dict[str, object]) -> None:
        v2 = _build_v2_dict(migrated)
        assert "components" in v2
        assert len(v2["components"]) == 2  # type: ignore[arg-type]

    def test_minimizer_preserved(self, migrated: dict[str, object]) -> None:
        v2 = _build_v2_dict(migrated)
        assert "minimizer" in v2

    def test_no_peaks_key(self, migrated: dict[str, object]) -> None:
        v2 = _build_v2_dict(migrated)
        assert "peaks" not in v2


# ---------------------------------------------------------------------------
# Round-trip: UnifiedFittingConfig accepts the migrated TOML
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestRoundTrip:
    """Generated TOML must load cleanly via UnifiedFittingConfig."""

    def test_round_trip_to_file_and_back(self, tmp_path: Path) -> None:
        """Write migrated TOML and load it with UnifiedFittingConfig."""
        import tomli_w

        from spectrafit.core.fitting_config import UnifiedFittingConfig
        from spectrafit.models.migration import migrate_v1_format

        migrated = migrate_v1_format(dict(_V1_FULL))
        v2_dict = _build_v2_dict(migrated)
        toml_bytes = tomli_w.dumps(v2_dict)

        out_path = tmp_path / "migrated.toml"
        out_path.write_text(toml_bytes, encoding="utf-8")

        cfg = UnifiedFittingConfig.from_file(out_path)
        assert len(cfg.components) == 2
        comp_ids = [c.id for c in cfg.components]
        assert "p1" in comp_ids
        assert "bg" in comp_ids

    def test_read_input_json(self, tmp_path: Path) -> None:
        """_read_input handles JSON files correctly."""
        data = {"key": "value", "number": 42}
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")
        result = _read_input(json_file)
        assert result["key"] == "value"

    def test_read_input_toml(self, tmp_path: Path) -> None:
        """_read_input handles TOML files correctly."""
        import tomli_w

        data = {"key": "value"}
        toml_file = tmp_path / "test.toml"
        toml_file.write_bytes(tomli_w.dumps(data).encode())
        result = _read_input(toml_file)
        assert result["key"] == "value"

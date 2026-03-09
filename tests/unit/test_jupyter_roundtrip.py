"""Unit tests for SpectraFitNotebook round-trip methods (Phase 11c).

Covers:
- ``export_config_toml`` — serialize current notebook state to v2 TOML
- ``load_cli_config`` — load a v2 TOML/JSON back into UnifiedFittingConfig
"""

from __future__ import annotations

import json

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.core import SpectraFitNotebook


_SIMPLE_COMPONENTS: list[dict[str, object]] = [
    {
        "id": "p1",
        "model": "gaussian",
        "parameters": {
            "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
            "fwhmg": {"value": 0.1, "vary": True, "min": 0.02, "max": 0.5},
        },
    },
    {
        "id": "p2",
        "model": "lorentzian",
        "parameters": {
            "amplitude": {"value": 0.5, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": -1.0, "vary": True, "min": -2.0, "max": 2.0},
            "fwhml": {"value": 0.1, "vary": True, "min": 0.01, "max": 0.5},
        },
    },
]


def _mock_notebook(components: list[dict[str, object]] = _SIMPLE_COMPONENTS) -> MagicMock:
    """Return a MagicMock that behaves like a SpectraFitNotebook for export tests."""
    nb = MagicMock(spec=SpectraFitNotebook)
    nb.args_to_config.return_value = UnifiedFittingConfig(components=components)
    return nb


class TestExportConfigToml:
    """Tests for SpectraFitNotebook.export_config_toml."""

    @pytest.mark.unit
    def test_creates_toml_file(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        assert dest.exists()

    @pytest.mark.unit
    def test_toml_is_valid_v2_format(self, tmp_path: Path) -> None:
        try:
            import tomllib  # noqa: PLC0415
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]  # noqa: PLC0415

        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        with dest.open("rb") as fh:
            data = tomllib.load(fh)
        assert "components" in data, "Must use v2 'components' key"
        assert "fitting" not in data, "v1 'fitting' key must not be present"

    @pytest.mark.unit
    def test_toml_validates_through_unified_config(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        cfg = SpectraFitNotebook.load_cli_config(dest)
        assert isinstance(cfg, UnifiedFittingConfig)

    @pytest.mark.unit
    def test_components_count_matches_peaks(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        SpectraFitNotebook.export_config_toml(nb, dest)
        cfg = SpectraFitNotebook.load_cli_config(dest)
        assert len(cfg.components) == 2

    @pytest.mark.unit
    def test_raises_if_file_exists_without_force(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        dest.write_text("existing content")
        with pytest.raises(FileExistsError, match="already exists"):
            SpectraFitNotebook.export_config_toml(nb, dest)

    @pytest.mark.unit
    def test_force_true_overwrites(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = tmp_path / "fit.toml"
        dest.write_text("old content")
        SpectraFitNotebook.export_config_toml(nb, dest, force=True)
        assert dest.stat().st_size > 0

    @pytest.mark.unit
    def test_accepts_string_path(self, tmp_path: Path) -> None:
        nb = _mock_notebook()
        dest = str(tmp_path / "fit.toml")
        SpectraFitNotebook.export_config_toml(nb, dest)
        assert Path(dest).exists()


class TestLoadCliConfig:
    """Tests for SpectraFitNotebook.load_cli_config (classmethod)."""

    @pytest.mark.unit
    def test_raises_on_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError, match="not found"):
            SpectraFitNotebook.load_cli_config(tmp_path / "nonexistent.toml")

    @pytest.mark.unit
    def test_raises_on_unsupported_extension(self, tmp_path: Path) -> None:
        bad = tmp_path / "config.yaml"
        bad.write_text("key: value")
        with pytest.raises(ValueError, match="Unsupported"):
            SpectraFitNotebook.load_cli_config(bad)

    @pytest.mark.unit
    def test_loads_valid_toml(self, tmp_path: Path) -> None:
        from spectrafit.cli.commands.scaffolding import _build_config  # noqa: PLC0415
        from spectrafit.cli.commands.scaffolding import _write_config  # noqa: PLC0415
        from spectrafit.cli._types import OutputFormatEnum  # noqa: PLC0415

        toml_path = tmp_path / "config.toml"
        _write_config(_build_config([(1, "voigt")]), toml_path, OutputFormatEnum.TOML)
        cfg = SpectraFitNotebook.load_cli_config(toml_path)
        assert isinstance(cfg, UnifiedFittingConfig)
        assert len(cfg.components) == 1
        assert cfg.components[0].model == "voigt"

    @pytest.mark.unit
    def test_loads_valid_json(self, tmp_path: Path) -> None:
        from spectrafit.cli.commands.scaffolding import _build_config  # noqa: PLC0415
        from spectrafit.cli.commands.scaffolding import _write_config  # noqa: PLC0415
        from spectrafit.cli._types import OutputFormatEnum  # noqa: PLC0415

        json_path = tmp_path / "config.json"
        _write_config(_build_config([(1, "gaussian")]), json_path, OutputFormatEnum.JSON)
        cfg = SpectraFitNotebook.load_cli_config(json_path)
        assert isinstance(cfg, UnifiedFittingConfig)
        assert len(cfg.components) == 1

    @pytest.mark.unit
    def test_accepts_path_object_and_string(self, tmp_path: Path) -> None:
        from spectrafit.cli.commands.scaffolding import _build_config  # noqa: PLC0415
        from spectrafit.cli.commands.scaffolding import _write_config  # noqa: PLC0415
        from spectrafit.cli._types import OutputFormatEnum  # noqa: PLC0415

        toml_path = tmp_path / "cfg.toml"
        _write_config(_build_config([(1, "gaussian")]), toml_path, OutputFormatEnum.TOML)
        # Path object
        cfg1 = SpectraFitNotebook.load_cli_config(toml_path)
        # String path
        cfg2 = SpectraFitNotebook.load_cli_config(str(toml_path))
        assert len(cfg1.components) == len(cfg2.components)

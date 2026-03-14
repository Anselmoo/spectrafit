"""Unit tests for CLI runtime configuration loading."""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from pydantic import ValidationError


def _write_config(path: Path, data_file: Path) -> Path:
    config = {
        "data": {
            "infile": str(data_file),
            "x_col": "energy",
            "y_col": "intensity",
            "separator": ",",
            "header": 0,
        },
        "minimizer": {"nan_policy": "propagate", "calc_covar": True},
        "optimizer": {"max_nfev": 50, "method": "leastsq"},
        "components": [
            {
                "id": "p1",
                "model": "gaussian",
                "parameters": {
                    "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                    "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
                    "fwhmg": {"min": 0.01, "max": 2.0, "value": 0.5, "vary": True},
                },
            }
        ],
    }
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


@pytest.mark.unit
class TestCliRuntimeSettings:
    def test_from_environment_validates_blank_default_config_name(self) -> None:
        from spectrafit.cli.runtime import CliRuntimeSettings

        with pytest.raises(ValidationError):
            CliRuntimeSettings.from_environment(
                environ={"SPECTRAFIT_DEFAULT_CONFIG_NAME": "   "},
            )


@pytest.mark.unit
class TestCliRuntimeLoader:
    def test_load_fitting_config_prefers_explicit_path(
        self,
        tmp_path: Path,
    ) -> None:
        from spectrafit.cli.runtime import build_cli_runtime

        data_file = tmp_path / "spectrum.csv"
        data_file.write_text("energy,intensity\n0,1\n", encoding="utf-8")
        explicit_config = _write_config(tmp_path / "explicit.json", data_file)

        runtime = build_cli_runtime(
            environ={"SPECTRAFIT_CONFIG": str(tmp_path / "missing.json")},
        )

        cfg = runtime.load_fitting_config(explicit_config)

        assert cfg.data is not None
        assert cfg.data.infile == explicit_config.parent / data_file.name

    def test_load_fitting_config_uses_environment_path(self, tmp_path: Path) -> None:
        from spectrafit.cli.runtime import build_cli_runtime

        data_file = tmp_path / "spectrum.csv"
        data_file.write_text("energy,intensity\n0,1\n", encoding="utf-8")
        env_config = _write_config(tmp_path / "env.json", data_file)

        runtime = build_cli_runtime(environ={"SPECTRAFIT_CONFIG": str(env_config)})

        cfg = runtime.load_fitting_config(None)

        assert cfg.data is not None
        assert cfg.data.infile == env_config.parent / data_file.name

    def test_load_fitting_config_uses_app_dir_default(self, tmp_path: Path) -> None:
        from spectrafit.cli.runtime import build_cli_runtime

        app_dir = tmp_path / "appdir"
        app_dir.mkdir()
        data_file = app_dir / "spectrum.csv"
        data_file.write_text("energy,intensity\n0,1\n", encoding="utf-8")
        default_config = _write_config(app_dir / "config.json", data_file)

        runtime = build_cli_runtime(
            environ={
                "SPECTRAFIT_APP_DIR": str(app_dir),
                "SPECTRAFIT_DEFAULT_CONFIG_NAME": "config.json",
            },
        )

        cfg = runtime.load_fitting_config(None)

        assert cfg.data is not None
        assert cfg.data.infile == default_config.parent / data_file.name

    def test_load_fitting_config_raises_helpful_error(self, tmp_path: Path) -> None:
        from spectrafit.cli.runtime import build_cli_runtime

        runtime = build_cli_runtime(
            environ={
                "SPECTRAFIT_APP_DIR": str(tmp_path / "missing-app-dir"),
            },
        )

        with pytest.raises(FileNotFoundError, match="SPECTRAFIT_CONFIG"):
            runtime.load_fitting_config(None)

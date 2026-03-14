"""Integration tests for CLI runtime-backed config loading."""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


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


@pytest.mark.integration
def test_validate_uses_environment_config_when_argument_omitted(tmp_path: Path) -> None:
    data_file = tmp_path / "spectrum.csv"
    data_file.write_text("energy,intensity\n0,1\n", encoding="utf-8")
    config_file = _write_config(tmp_path / "fit_config.json", data_file)

    result = runner.invoke(
        app,
        ["validate"],
        env={"SPECTRAFIT_CONFIG": str(config_file)},
    )

    assert result.exit_code == 0, result.output
    assert "is valid" in result.output


@pytest.mark.integration
def test_validate_argument_overrides_environment_config(tmp_path: Path) -> None:
    data_file = tmp_path / "spectrum.csv"
    data_file.write_text("energy,intensity\n0,1\n", encoding="utf-8")
    explicit_config = _write_config(tmp_path / "explicit_config.json", data_file)
    missing_env_config = tmp_path / "missing_from_env.json"

    result = runner.invoke(
        app,
        ["validate", str(explicit_config)],
        env={"SPECTRAFIT_CONFIG": str(missing_env_config)},
    )

    assert result.exit_code == 0, result.output
    assert "is valid" in result.output


@pytest.mark.integration
def test_validate_rejects_missing_referenced_data_file(tmp_path: Path) -> None:
    missing_data_file = tmp_path / "missing.csv"
    config_file = _write_config(tmp_path / "fit_config.json", missing_data_file)

    result = runner.invoke(app, ["validate", str(config_file)])

    assert result.exit_code == 1
    assert "data file not found" in result.output.lower()


@pytest.mark.integration
def test_validate_rejects_missing_configured_columns(tmp_path: Path) -> None:
    data_file = tmp_path / "spectrum.csv"
    data_file.write_text("binding_energy,counts\n0,1\n", encoding="utf-8")
    config_file = _write_config(tmp_path / "fit_config.json", data_file)

    result = runner.invoke(app, ["validate", str(config_file)])

    assert result.exit_code == 1
    combined = (result.output + (result.stderr or "")).lower()
    assert "configured columns" in combined
    assert "energy" in combined
    assert "intensity" in combined

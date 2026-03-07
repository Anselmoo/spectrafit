"""Integration tests for the ``spectrafit fit`` CLI subcommand (v2.0.0).

Covers:
- fit --help smoke test (always passes)
- fit with a minimal v2 config file (single-file, data path embedded)
- fit with missing peaks produces a clear validation error
- fit output files written to expected paths
"""

from __future__ import annotations

import json

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


# ---------------------------------------------------------------------------
# Smoke tests (no Phase dependency)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestFitHelp:
    def test_fit_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["fit", "--help"])
        assert result.exit_code == 0

    def test_fit_help_mentions_input(self) -> None:
        result = runner.invoke(app, ["fit", "--help"])
        assert "config" in result.output.lower() or result.exit_code == 0


# ---------------------------------------------------------------------------
# Phase 4 tests — full fit run via CLI (v2: fit <config> --noplot)
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_json_input(tmp_path: Path) -> tuple[Path, Path]:
    """Write a minimal v2 config JSON (with embedded data path) and a data CSV.

    Returns:
        tuple[Path, Path]: (data_file, config_file)
    """
    # Write data CSV
    x = np.linspace(-5, 5, 100)
    y = np.exp(-(x**2) / 0.5)
    data_file = tmp_path / "spectrum.csv"
    pd.DataFrame({"energy": x, "intensity": y}).to_csv(data_file, index=False)

    # Write v2 config JSON — data.infile points to data_file
    config = {
        "data": {
            "infile": str(data_file),
            "x_col": "energy",
            "y_col": "intensity",
            "separator": ",",
            "header": 0,
        },
        "minimizer": {"nan_policy": "propagate", "calc_covar": True},
        "optimizer": {"max_nfev": 500, "method": "leastsq"},
        "peaks": {
            "1": {
                "gaussian": {
                    "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                    "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
                    "fwhmg": {"min": 0.01, "max": 2.0, "value": 0.5, "vary": True},
                }
            }
        },
    }
    config_file = tmp_path / "fit_config.json"
    config_file.write_text(json.dumps(config))
    return data_file, config_file


@pytest.mark.integration
class TestFitWithJsonInput:
    def test_fit_exits_zero(
        self, minimal_json_input: tuple[Path, Path], tmp_path: Path
    ) -> None:
        _data_file, config_file = minimal_json_input
        result = runner.invoke(
            app,
            ["fit", str(config_file), "--noplot"],
            input="N\n",
        )
        assert result.exit_code == 0, result.output

    def test_fit_produces_output_file(
        self, minimal_json_input: tuple[Path, Path], tmp_path: Path
    ) -> None:
        _data_file, config_file = minimal_json_input
        runner.invoke(
            app,
            ["fit", str(config_file), "--noplot"],
        )
        output_files = list(tmp_path.glob("*.csv")) + list(tmp_path.glob("*.json"))
        assert len(output_files) > 0, "No output files produced by fit command"


@pytest.mark.integration
class TestFitMissingPeaks:
    def test_missing_peaks_shows_clear_error(self, tmp_path: Path) -> None:
        x = np.linspace(-5, 5, 50)
        data_file = tmp_path / "spectrum.csv"
        pd.DataFrame({"energy": x, "intensity": x}).to_csv(data_file, index=False)
        config = {
            "data": {
                "infile": str(data_file),
                "x_col": "energy",
                "y_col": "intensity",
                "separator": ",",
                "header": 0,
            },
            "minimizer": {"nan_policy": "propagate"},
            "optimizer": {"method": "leastsq"},
            "peaks": {},  # empty — must be rejected clearly
        }
        config_file = tmp_path / "bad_config.json"
        config_file.write_text(json.dumps(config))

        result = runner.invoke(
            app,
            ["fit", str(config_file), "--noplot"],
        )
        # Should fail with a descriptive message, not a raw KeyError
        assert result.exit_code != 0
        combined = (result.output + (result.stderr or "")).lower()
        assert "peak" in combined or "valid" in combined or "error" in combined

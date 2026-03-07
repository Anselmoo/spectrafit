"""Integration smoke tests for examples/*/input.toml via FittingPipeline."""

from __future__ import annotations

import math

from pathlib import Path

import pandas as pd
import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline


EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"
EXAMPLE_INPUTS = sorted(EXAMPLES_DIR.glob("*/input.toml"))


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_loads_and_converges(input_toml: Path, tmp_path: Path) -> None:
    """Each example must load, fit, and converge with residuals < 0.1 RMS."""
    data_csv = input_toml.parent / "data.csv"
    assert data_csv.exists(), f"Missing data.csv for {input_toml.parent.name}"

    df = pd.read_csv(data_csv)
    assert df.shape[1] == 2, f"Expected 2 columns, got {df.shape[1]}"

    # Load config and override infile to the absolute path so the pipeline can
    # resolve the data file regardless of the working directory.
    raw = UnifiedFittingConfig.from_file(input_toml).model_dump()
    raw["data"]["infile"] = str(data_csv.resolve())
    cfg = UnifiedFittingConfig.model_validate(raw)
    assert len(cfg.components) >= 1

    fit = FittingPipeline(config=cfg).run()

    assert fit.success, (
        f"Fit did not converge for {input_toml.parent.name}: {fit.result.message}"
    )

    x_col, y_col = df.columns[0], df.columns[1]
    # The pipeline stores the best-fit values in fit.df["fit"]
    residuals = fit.df["fit"].values - fit.df[y_col].values
    rms = math.sqrt(float((residuals**2).mean()))
    assert rms < 0.1, (
        f"RMS residual {rms:.4f} >= 0.1 for {input_toml.parent.name} — fit quality too poor"
    )

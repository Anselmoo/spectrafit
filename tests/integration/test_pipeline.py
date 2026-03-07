"""Integration tests for FittingPipeline (v2.0.0).

Covers:
- FittingPipeline(config: UnifiedFittingConfig) constructor
- UnifiedFittingConfig.from_dict() coercion then FittingPipeline
- Pipeline end-to-end with file-based data
- Pipeline idempotency: second run must produce identical output
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.models.output_config import OutputConfig


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

MINIMAL_PEAKS: dict[str, object] = {
    "peaks": {
        "1": {
            "gaussian": {
                "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                "center": {"min": -1, "max": 1, "value": 0.0, "vary": True},
                "fwhmg": {"min": 0.1, "max": 2.0, "value": 0.7, "vary": True},
            }
        }
    },
    "column": {"x": "energy", "y": "intensity"},
    "minimizer": {"nan_policy": "propagate", "calc_covar": True},
    "optimizer": {"max_nfev": 1000, "method": "leastsq"},
    "global_": 0,
}


# ---------------------------------------------------------------------------
# Phase 1 — constructor
# ---------------------------------------------------------------------------


class TestFittingPipelineConstructor:
    """FittingPipeline.__init__ accepts UnifiedFittingConfig only."""

    def test_dict_coerced_to_unified_config(self) -> None:
        """from_dict() + FittingPipeline stores a UnifiedFittingConfig."""
        config = UnifiedFittingConfig.from_dict(MINIMAL_PEAKS)
        pipeline = FittingPipeline(config=config)
        assert isinstance(pipeline.config, UnifiedFittingConfig)

    def test_unified_config_stored_directly(self) -> None:
        """UnifiedFittingConfig input must be stored without re-wrapping."""
        config = UnifiedFittingConfig.from_dict(MINIMAL_PEAKS)
        pipeline = FittingPipeline(config=config)
        assert isinstance(pipeline.config, UnifiedFittingConfig)
        assert pipeline.config is config

    def test_peaks_accessible_via_config(self) -> None:
        """Pipeline config must expose peaks after from_dict coercion."""
        config = UnifiedFittingConfig.from_dict(MINIMAL_PEAKS)
        pipeline = FittingPipeline(config=config)
        assert "1" in pipeline.config.peaks
        assert "gaussian" in pipeline.config.peaks["1"]


# ---------------------------------------------------------------------------
# Phase 2 — end-to-end run
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.integration
class TestFittingPipelineRun:
    """FittingPipeline.run() must execute the full pipeline end-to-end."""

    def test_pipeline_runs_without_error(self, tmp_path: object) -> None:
        from spectrafit.core.pipeline import fitting_routine_pipeline

        assert isinstance(tmp_path, __import__("pathlib").Path)

        # Write a CSV that the pipeline can load
        x = np.linspace(-5, 5, 200)
        y = np.exp(-(x**2) / 0.5)
        df = pd.DataFrame({"energy": x, "intensity": y})
        csv = tmp_path / "spec.csv"  # type: ignore[operator]
        df.to_csv(csv, index=False)

        cfg = UnifiedFittingConfig.from_dict(
            {
                **MINIMAL_PEAKS,
                "data": {
                    "infile": str(csv),
                    "x_col": "energy",
                    "y_col": "intensity",
                    "separator": ",",
                    "header": 0,
                    "decimal": ".",
                },
                "preprocessing": {
                    "energy_start": None,
                    "energy_stop": None,
                    "shift": 0,
                    "oversampling": False,
                    "smooth": 0,
                },
                "conf_interval": False,
            }
        )
        output = OutputConfig(outfile=str(tmp_path / "out"), noplot=True)  # type: ignore[operator]
        result_df, result_args = fitting_routine_pipeline(cfg, output=output)
        assert result_df is not None
        assert "p1_amplitude" in result_args.get("fit_insights", {}).get(
            "variables", {}
        )


# ---------------------------------------------------------------------------
# Phase 3 — idempotency
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPipelineIdempotency:
    """Running the pipeline twice with identical input must produce identical output."""

    def test_second_run_same_as_first(self, tmp_path: object) -> None:
        assert isinstance(tmp_path, __import__("pathlib").Path)

        x = np.linspace(-5, 5, 200)
        y = np.exp(-(x**2) / 0.5)
        df = pd.DataFrame({"energy": x, "intensity": y})
        csv = tmp_path / "spec.csv"  # type: ignore[operator]
        df.to_csv(csv, index=False)

        cfg_dict: dict[str, object] = {
            **MINIMAL_PEAKS,
            "data": {
                "infile": str(csv),
                "x_col": "energy",
                "y_col": "intensity",
                "separator": ",",
                "header": 0,
                "decimal": ".",
            },
            "preprocessing": {
                "energy_start": None,
                "energy_stop": None,
                "shift": 0.0,
                "oversampling": False,
                "smooth": 0,
            },
            "conf_interval": False,
        }
        pipeline_1 = FittingPipeline(config=UnifiedFittingConfig.from_dict(cfg_dict))
        pipeline_2 = FittingPipeline(config=UnifiedFittingConfig.from_dict(cfg_dict))
        result_1 = pipeline_1.run()
        result_2 = pipeline_2.run()
        assert result_1.df.equals(result_2.df)

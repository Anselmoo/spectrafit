"""Integration tests for FittingPipeline (v2.0.0).

Covers:
- FittingPipeline(config: UnifiedFittingConfig) constructor (Phase 1 ✅)
- FittingPipeline(config: dict) backward-compat dict coercion (Phase 1 ✅)
- Pipeline end-to-end with file-based data (Phase 2 — blocked on CLI convergence)
- Pipeline idempotency: second run must produce identical output (Phase 3)
"""

from __future__ import annotations

from typing import Any

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline


# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

MINIMAL_PEAKS: dict[str, Any] = {
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
# Phase 1 — constructor coercion (now implemented)
# ---------------------------------------------------------------------------


class TestFittingPipelineConstructor:
    """FittingPipeline.__init__ must accept both dict and UnifiedFittingConfig."""

    def test_dict_coerced_to_unified_config(self) -> None:
        """Plain dict input must be coerced to UnifiedFittingConfig."""
        pipeline = FittingPipeline(config=MINIMAL_PEAKS)
        assert isinstance(pipeline.config, UnifiedFittingConfig)

    def test_unified_config_stored_directly(self) -> None:
        """UnifiedFittingConfig input must be stored without re-wrapping."""
        config = UnifiedFittingConfig.from_dict(MINIMAL_PEAKS)
        pipeline = FittingPipeline(config=config)
        assert isinstance(pipeline.config, UnifiedFittingConfig)
        assert pipeline.config is config

    def test_peaks_accessible_via_config(self) -> None:
        """Pipeline config must expose peaks after dict coercion."""
        pipeline = FittingPipeline(config=MINIMAL_PEAKS)
        assert "1" in pipeline.config.peaks
        assert "gaussian" in pipeline.config.peaks["1"]


# ---------------------------------------------------------------------------
# Phase 2 — end-to-end run (blocked: needs file-based data or df injection)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.integration
class TestFittingPipelineRun:
    """FittingPipeline.run() must execute the full pipeline end-to-end."""

    def test_pipeline_runs_without_error(self, tmp_path: Any) -> None:
        import numpy as np
        import pandas as pd

        from spectrafit.core.pipeline import fitting_routine_pipeline

        # Write a CSV that the pipeline can load
        x = np.linspace(-5, 5, 200)
        y = np.exp(-(x**2) / 0.5)
        df = pd.DataFrame({"energy": x, "intensity": y})
        csv = tmp_path / "spec.csv"
        df.to_csv(csv, index=False)

        args = {
            **MINIMAL_PEAKS,
            "infile": str(csv),
            "separator": ",",
            "header": 0,
            "decimal": ".",
            "comment": None,
            "outfile": str(tmp_path / "out"),
            "energy_start": None,
            "energy_stop": None,
            "shift": 0,
            "oversampling": False,
            "smooth": 0,
            "conf_interval": False,
        }
        result_df, result_args = fitting_routine_pipeline(args)
        assert result_df is not None
        assert "p1_amplitude" in result_args.get("fit_insights", {}).get(
            "variables", {}
        )


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Phase 3 — idempotency (S5 complete: conf_interval .pop() mutation fixed)
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPipelineIdempotency:
    """Running the pipeline twice with identical input must produce identical output."""

    def test_second_run_same_as_first(self, tmp_path: Any) -> None:
        import numpy as np
        import pandas as pd

        x = np.linspace(-5, 5, 200)
        y = np.exp(-(x**2) / 0.5)
        df = pd.DataFrame({"energy": x, "intensity": y})
        csv = tmp_path / "spec.csv"
        df.to_csv(csv, index=False)

        args = {
            **MINIMAL_PEAKS,
            "column": ["energy", "intensity"],  # list form required by load_data
            "infile": str(csv),
            "separator": ",",
            "header": 0,
            "decimal": ".",
            "comment": None,
            # Required preprocessing keys (None/False = no-op)
            "energy_start": None,
            "energy_stop": None,
            "shift": 0.0,
            "oversampling": False,
            "smooth": 0,
            "conf_interval": False,
        }
        # Pass the raw dict so _raw_args includes infile/separator/etc.
        pipeline_1 = FittingPipeline(config=dict(args))
        pipeline_2 = FittingPipeline(config=dict(args))
        result_1 = pipeline_1.run()
        result_2 = pipeline_2.run()
        assert result_1.df.equals(result_2.df)

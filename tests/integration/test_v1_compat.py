"""Backward-compatibility smoke tests for v1.x input files.

Validates that rixs/config.json (canonical v1.x format with nested
``parameters`` wrapper and string-integer peak keys) can be loaded via
``UnifiedFittingConfig.from_file()`` without validation errors.

These tests are the merge gate for Phase 2 — no Phase 2 PR merges until
all tests here are green.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig


# Path to the canonical v1.x input file shipped in the repo
RIXS_CONFIG = Path(__file__).parents[2] / "rixs" / "config.json"


@pytest.mark.integration
@pytest.mark.skipif(not RIXS_CONFIG.exists(), reason="rixs/config.json not found")
class TestV1CompatFromFile:
    """UnifiedFittingConfig.from_file() must load rixs/config.json cleanly."""

    def test_no_validation_error(self) -> None:
        """Loading must not raise a Pydantic ValidationError."""
        config = UnifiedFittingConfig.from_file(RIXS_CONFIG)
        assert config is not None

    def test_peaks_accessible_by_string_int_key(self) -> None:
        """Peak key '1' must be accessible after loading."""
        config = UnifiedFittingConfig.from_file(RIXS_CONFIG)
        assert "1" in config.peaks, (
            "Peak key '1' not found — v1.x string-integer key contract broken"
        )

    def test_minimizer_present(self) -> None:
        """Minimizer settings must survive the v1.x → v2 migration."""
        config = UnifiedFittingConfig.from_file(RIXS_CONFIG)
        assert config.minimizer is not None

    def test_optimizer_present(self) -> None:
        """Optimizer settings must survive the v1.x → v2 migration."""
        config = UnifiedFittingConfig.from_file(RIXS_CONFIG)
        assert config.optimizer is not None


@pytest.mark.integration
class TestV1CompatFromDict:
    """UnifiedFittingConfig.from_dict() must handle the v1.x nested structure directly."""

    V1_STRUCTURE = {
        "fitting": {
            "description": {"project": "rixs_test", "title": "RIXS spectrum"},
            "parameters": {
                "minimizer": {"nan_policy": "propagate", "calc_covar": True},
                "optimizer": {"max_nfev": 1000, "method": "leastsq"},
            },
            "peaks": {
                "1": {
                    "gaussian": {
                        "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                        "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
                        "fwhmg": {"min": 0.01, "max": 1.0, "value": 0.5, "vary": True},
                    }
                }
            },
        }
    }

    def test_from_dict_with_fitting_wrapper(self) -> None:
        config = UnifiedFittingConfig.from_dict(self.V1_STRUCTURE["fitting"])
        assert config is not None
        assert "1" in config.peaks

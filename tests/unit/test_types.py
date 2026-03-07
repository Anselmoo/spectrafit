"""Unit tests for TypeAlias definitions (v2.0.0).

Tests the TypeAlias contract that currently lives in ``spectrafit.models.autopeak``
and will be migrated to ``spectrafit.models.types`` in Phase 1.

Import path is parametrised so this file works both before and after the migration.
"""

from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Import-path compatibility shim
# ---------------------------------------------------------------------------
try:
    from spectrafit.models.types import FittingArgs  # target location (post-Phase 1)
    from spectrafit.models.types import (  # target location (post-Phase 1)
        ModelParameterSpec,
    )
    from spectrafit.models.types import (  # target location (post-Phase 1)
        ParameterConstraint,
    )
    from spectrafit.models.types import PeakModelSpec  # target location (post-Phase 1)
    from spectrafit.models.types import PeaksDict  # target location (post-Phase 1)
except ImportError:
    from spectrafit.models.autopeak import FittingArgs  # current location (pre-Phase 1)
    from spectrafit.models.autopeak import (  # current location (pre-Phase 1)
        ModelParameterSpec,
    )
    from spectrafit.models.autopeak import (  # current location (pre-Phase 1)
        ParameterConstraint,
    )
    from spectrafit.models.autopeak import (  # current location (pre-Phase 1)
        PeakModelSpec,
    )
    from spectrafit.models.autopeak import PeaksDict  # current location (pre-Phase 1)


# ---------------------------------------------------------------------------
# ParameterConstraint
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParameterConstraint:
    """ParameterConstraint = dict[str, float | bool | str | None]."""

    def test_valid_full_constraint(self) -> None:
        constraint: ParameterConstraint = {
            "min": 0.0,
            "max": 2.0,
            "value": 1.0,
            "vary": True,
            "expr": None,
        }
        assert isinstance(constraint, dict)

    def test_partial_constraint(self) -> None:
        constraint: ParameterConstraint = {"value": 0.5, "vary": False}
        assert constraint["vary"] is False


# ---------------------------------------------------------------------------
# ModelParameterSpec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModelParameterSpec:
    """ModelParameterSpec = dict[str, ParameterConstraint]."""

    def test_amplitude_center_fwhmg(self) -> None:
        spec: ModelParameterSpec = {
            "amplitude": {"min": 0, "max": 2, "value": 1, "vary": True},
            "center": {"min": -2, "max": 2, "value": 0, "vary": True},
            "fwhmg": {"min": 0.01, "max": 1.0, "value": 0.1, "vary": True},
        }
        assert set(spec.keys()) == {"amplitude", "center", "fwhmg"}


# ---------------------------------------------------------------------------
# PeakModelSpec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPeakModelSpec:
    """PeakModelSpec = dict[str, ModelParameterSpec]  — maps model name → params."""

    def test_gaussian_spec(self) -> None:
        spec: PeakModelSpec = {
            "gaussian": {
                "amplitude": {"value": 1.0, "vary": True},
                "center": {"value": 0.0, "vary": True},
                "fwhmg": {"value": 0.5, "vary": True},
            }
        }
        assert "gaussian" in spec
        assert "amplitude" in spec["gaussian"]


# ---------------------------------------------------------------------------
# PeaksDict
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPeaksDict:
    """PeaksDict = dict[str, PeakModelSpec]  — string-integer keys."""

    def test_single_peak(self) -> None:
        peaks: PeaksDict = {
            "1": {
                "pseudovoigt": {
                    "amplitude": {"value": 1.0, "vary": True},
                    "center": {"value": 0.0, "vary": True},
                    "fwhmg": {"value": 0.1, "vary": True},
                    "fwhml": {"value": 0.1, "vary": True},
                }
            }
        }
        assert "1" in peaks

    def test_multiple_peaks_ordered_by_string_key(self) -> None:
        peaks: PeaksDict = {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0},
                    "center": {"value": -1.0},
                    "fwhmg": {"value": 0.5},
                }
            },
            "2": {
                "lorentzian": {
                    "amplitude": {"value": 0.5},
                    "center": {"value": 1.0},
                    "fwhml": {"value": 0.5},
                }
            },
        }
        assert list(peaks.keys()) == ["1", "2"]


# ---------------------------------------------------------------------------
# FittingArgs
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFittingArgs:
    """FittingArgs = dict[str, Any]  — top-level pipeline input dict."""

    def test_minimal_valid_args(self) -> None:
        args: FittingArgs = {
            "peaks": {
                "1": {
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": 0.0},
                        "fwhmg": {"value": 0.5},
                    }
                }
            },
            "column": ["energy", "intensity"],
            "global_": 0,
        }
        assert args["global_"] == 0
        assert isinstance(args["peaks"], dict)

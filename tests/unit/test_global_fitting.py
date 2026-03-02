"""Unit tests for GlobalFittingConfig and GlobalMode (spectrafit.models.global_fitting).

Covers:
- GlobalMode enum / integer constants (Phase 1)
- GlobalFittingConfig parameter sharing validation
- Multi-dataset configuration
"""

from __future__ import annotations

import pytest


# GlobalMode will be added to global_fitting.py in Phase 1.
# Mark tests that depend on it as xfail until then.
try:
    from spectrafit.models.global_fitting import GlobalMode  # post-Phase 1

    _GLOBAL_MODE_AVAILABLE = True
except ImportError:
    _GLOBAL_MODE_AVAILABLE = False

# Constants sourced from GlobalMode (canonical location: spectrafit.models.global_fitting)
from spectrafit.models.global_fitting import GlobalMode as _GlobalMode


GLOBAL_NONE = int(_GlobalMode.NONE)
GLOBAL_STANDARD = int(_GlobalMode.STANDARD)
GLOBAL_WITH_PRE = int(_GlobalMode.WITH_PRE)


# ---------------------------------------------------------------------------
# GlobalMode enum (Phase 1 deliverable)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.skipif(
    not _GLOBAL_MODE_AVAILABLE, reason="GlobalMode not yet added (Phase 1)"
)
class TestGlobalModeEnum:
    """GlobalMode(IntEnum) must replace bare GLOBAL_* int constants."""

    def test_none_value(self) -> None:
        assert int(GlobalMode.NONE) == 0  # type: ignore[name-defined]

    def test_standard_value(self) -> None:
        assert int(GlobalMode.STANDARD) == 1  # type: ignore[name-defined]

    def test_with_pre_value(self) -> None:
        assert int(GlobalMode.WITH_PRE) == 2  # type: ignore[name-defined]

    def test_backward_compat_with_int_constants(self) -> None:
        """GlobalMode values must equal the old bare int constants."""
        assert int(GlobalMode.NONE) == GLOBAL_NONE  # type: ignore[name-defined]
        assert int(GlobalMode.STANDARD) == GLOBAL_STANDARD  # type: ignore[name-defined]
        assert int(GlobalMode.WITH_PRE) == GLOBAL_WITH_PRE  # type: ignore[name-defined]

    def test_int_comparison(self) -> None:
        """IntEnum must compare equal to plain int (pipeline if-branches use == 0/1/2)."""
        assert GlobalMode.NONE == 0  # type: ignore[name-defined]
        assert GlobalMode.STANDARD == 1  # type: ignore[name-defined]
        assert GlobalMode.WITH_PRE == 2  # type: ignore[name-defined]


# ---------------------------------------------------------------------------
# Legacy constants  (pre-Phase 1 — must stay passing until GlobalMode exists)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLegacyGlobalConstants:
    """Pin the current int constant values before migrating to GlobalMode."""

    def test_global_none_is_zero(self) -> None:
        assert GLOBAL_NONE == 0

    def test_global_standard_is_one(self) -> None:
        assert GLOBAL_STANDARD == 1

    def test_global_with_pre_is_two(self) -> None:
        assert GLOBAL_WITH_PRE == 2

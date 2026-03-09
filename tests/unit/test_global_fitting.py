"""Unit tests for GlobalFittingConfig and FittingMode coercion.

Covers:
- FittingMode coercion from legacy int values (replaces GlobalMode)
- GlobalFittingConfig parameter sharing validation
- Multi-dataset configuration
"""

from __future__ import annotations

import pytest

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.global_fitting import SharedParameter

MINIMAL_COMPONENTS = [
    {
        "id": "p1",
        "model": "gaussian",
        "parameters": {"amplitude": {"value": 1.0}},
    }
]


# ---------------------------------------------------------------------------
# FittingMode coercion from legacy int values (replaces TestGlobalModeEnum)
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFittingModeCoercion:
    """UnifiedFittingConfig.global_ must coerce legacy int values to FittingMode."""

    @pytest.mark.parametrize(
        ("int_value", "expected_mode"),
        [
            (0, FittingMode.STANDARD),
            (1, FittingMode.GLOBAL),
            (2, FittingMode.GLOBAL),
        ],
    )
    def test_int_coercion(self, int_value: int, expected_mode: FittingMode) -> None:
        """Legacy integers 0/1/2 coerce to the correct FittingMode."""
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        cfg = UnifiedFittingConfig(components=MINIMAL_COMPONENTS, **{"global": int_value})
        assert cfg.global_ == expected_mode

    def test_string_coercion(self) -> None:
        """String 'global' coerces to FittingMode.GLOBAL."""
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        cfg = UnifiedFittingConfig(
            components=MINIMAL_COMPONENTS,
            **{"global": "global"},
        )
        assert cfg.global_ == FittingMode.GLOBAL

    def test_default_is_standard(self) -> None:
        """Default global_ is FittingMode.STANDARD (replaces GlobalMode.NONE=0)."""
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        cfg = UnifiedFittingConfig(components=MINIMAL_COMPONENTS)
        assert cfg.global_ == FittingMode.STANDARD

    def test_invalid_int_raises(self) -> None:
        """Integer values outside 0/1/2 raise ValueError."""
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        with pytest.raises(Exception):
            UnifiedFittingConfig(
                components=MINIMAL_COMPONENTS,
                **{"global": 99},
            )


# ---------------------------------------------------------------------------
# Legacy backward-compat constants (still pinned in autopeak/builtin shims)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# GlobalFittingConfig
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestGlobalFittingConfig:
    """GlobalFittingConfig parameter sharing validation."""

    def test_shared_parameter_requires_name(self) -> None:
        """SharedParameter.name must be non-empty."""
        with pytest.raises(Exception):
            SharedParameter(name="")

    def test_global_fitting_config_valid(self) -> None:
        """A valid GlobalFittingConfig with one shared parameter constructs."""
        gfc = GlobalFittingConfig(
            n_datasets=2,
            shared_parameters=[SharedParameter(name="p1_center")],
        )
        assert gfc.n_datasets == 2
        assert len(gfc.shared_parameters) == 1

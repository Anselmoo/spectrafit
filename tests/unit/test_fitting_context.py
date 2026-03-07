"""Tests for Phase 6.4 — FittingContext and FittingMode.

Verifies:
- FittingMode is a str enum with correct values
- FittingContext defaults to STANDARD mode
- GLOBAL mode requires n_datasets >= 2
- from_global_int converts legacy values correctly
- global_int property provides backward-compat integer
- time_axis length validation
"""

from __future__ import annotations

import pytest

from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode


class TestFittingMode:
    def test_values_are_strings(self) -> None:
        assert FittingMode.STANDARD == "standard"
        assert FittingMode.GLOBAL == "global"
        assert FittingMode.TIME_RESOLVED == "time_resolved"
        assert FittingMode.SEQUENTIAL == "sequential"

    def test_construct_from_string(self) -> None:
        assert FittingMode("standard") == FittingMode.STANDARD
        assert FittingMode("global") == FittingMode.GLOBAL


class TestFittingContextDefaults:
    def test_default_mode_is_standard(self) -> None:
        ctx = FittingContext()
        assert ctx.mode == FittingMode.STANDARD

    def test_default_n_datasets(self) -> None:
        ctx = FittingContext()
        assert ctx.n_datasets == 1

    def test_default_shared_parameters_empty(self) -> None:
        ctx = FittingContext()
        assert ctx.shared_parameters == []

    def test_default_time_axis_none(self) -> None:
        ctx = FittingContext()
        assert ctx.time_axis is None


class TestFittingContextValidation:
    def test_global_mode_requires_n_datasets_ge_2(self) -> None:
        with pytest.raises(ValueError, match="n_datasets >= 2"):
            FittingContext(mode=FittingMode.GLOBAL, n_datasets=1)

    def test_global_mode_n_datasets_2_ok(self) -> None:
        ctx = FittingContext(mode=FittingMode.GLOBAL, n_datasets=2)
        assert ctx.n_datasets == 2

    def test_time_axis_wrong_length_raises(self) -> None:
        with pytest.raises(ValueError, match="time_axis length"):
            FittingContext(
                mode=FittingMode.TIME_RESOLVED,
                n_datasets=3,
                time_axis=[0.0, 1.0],  # length 2, not 3
            )

    def test_time_axis_correct_length_ok(self) -> None:
        ctx = FittingContext(
            mode=FittingMode.TIME_RESOLVED,
            n_datasets=3,
            time_axis=[0.0, 1.0, 2.0],
        )
        assert len(ctx.time_axis) == 3  # type: ignore[arg-type]


class TestGlobalInt:
    def test_standard_gives_zero(self) -> None:
        ctx = FittingContext(mode=FittingMode.STANDARD)
        assert ctx.global_int == 0

    def test_global_gives_one(self) -> None:
        ctx = FittingContext(mode=FittingMode.GLOBAL, n_datasets=2)
        assert ctx.global_int == 1

    def test_sequential_gives_one(self) -> None:
        ctx = FittingContext(mode=FittingMode.SEQUENTIAL)
        assert ctx.global_int == 1


class TestFromGlobalInt:
    @pytest.mark.parametrize(
        ("value", "expected_mode"),
        [
            (0, FittingMode.STANDARD),
            (1, FittingMode.GLOBAL),
            (2, FittingMode.GLOBAL),
        ],
    )
    def test_golden_table(self, value: int, expected_mode: FittingMode) -> None:
        ctx = FittingContext.from_global_int(value)
        assert ctx.mode == expected_mode

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError, match="global_"):
            FittingContext.from_global_int(3)

    def test_zero_returns_single_dataset(self) -> None:
        ctx = FittingContext.from_global_int(0)
        assert ctx.n_datasets == 1

    def test_one_returns_two_datasets(self) -> None:
        """from_global_int(1) sets n_datasets=2 as minimum valid GLOBAL config."""
        ctx = FittingContext.from_global_int(1)
        assert ctx.n_datasets == 2

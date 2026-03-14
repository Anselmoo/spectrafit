"""Unit tests for TypeAlias definitions (v2.0.0)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from spectrafit.models.split_frame import SplitFrame


if TYPE_CHECKING:
    from spectrafit.models.types import FitReportKwargs
    from spectrafit.models.types import ModelParameterSpec
    from spectrafit.models.types import ParameterConstraint


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


@pytest.mark.unit
class TestSplitFrame:
    """SplitFrame matches pandas ``orient='split'`` structure."""

    def test_split_payload_shape(self) -> None:
        split = SplitFrame(
            columns=["x", "y"],
            index=[0, 1],
            data=[[1.0, 2.0], [3.0, 4.0]],
        )
        assert split.columns == ["x", "y"]
        assert len(split.data) == 2

    def test_compatibility_key_access(self) -> None:
        split = SplitFrame(columns=["x"], index=[0], data=[[1.0]])
        assert split["columns"] == ["x"]


@pytest.mark.unit
class TestFitReportKwargs:
    """FitReportKwargs remains a typed optional-keys mapping."""

    def test_optional_kwargs(self) -> None:
        kwargs: FitReportKwargs = {
            "sort_pars": True,
            "show_correl": False,
            "min_correl": 0.25,
        }
        assert kwargs["sort_pars"] is True

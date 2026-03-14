"""Focused regression tests for post-processing immutability."""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from spectrafit.core.postprocessing import PostProcessing
from spectrafit.models.bundle import build_composite_bundle
from spectrafit.models.column_names import ColumnNames
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.results.fit_result import DataSummary


_COLS = ColumnNames()


def _build_local_postprocessor() -> tuple[PostProcessing, pd.DataFrame]:
    component = Component(
        id="main",
        model="gaussian",
        parameters={
            "amplitude": FitParameter(value=1.0, min=0.0, max=5.0),
            "center": FitParameter(value=0.0, min=-2.0, max=2.0),
            "fwhmg": FitParameter(value=0.5, min=0.05, max=2.0),
        },
    )
    bundle = build_composite_bundle([component])
    x = np.linspace(-2, 2, 40)
    y = bundle.decompose(bundle.params, x)["main"]
    source_df = pd.DataFrame({"binding_energy": x, "signal": y})
    minimizer = SimpleNamespace(max_nfev=25, nan_policy="raise")
    result = SimpleNamespace(
        params=bundle.params,
        residual=np.zeros_like(x),
        chisqr=0.0,
        redchi=0.0,
        aic=0.0,
        bic=0.0,
        nfev=1,
        success=True,
        message="ok",
        errorbars=False,
        method="leastsq",
    )
    return (
        PostProcessing(
            df=source_df,
            minimizer=minimizer,
            result=result,
            is_global=False,
            conf_interval=False,
            bundle=bundle,
            source_x_column="binding_energy",
            source_y_columns=["signal"],
        ),
        source_df,
    )


def _build_global_postprocessor() -> PostProcessing:
    x = np.array([0.0, 1.0, 2.0])
    source_df = pd.DataFrame(
        {
            "binding_energy": x,
            "signal_a": np.array([10.0, 20.0, 30.0]),
            "signal_b": np.array([1.0, 2.0, 3.0]),
        }
    )
    minimizer = SimpleNamespace(max_nfev=25, nan_policy="raise")
    result = SimpleNamespace(
        params={},
        residual=np.array([0.1, 1.0, 0.2, 1.1, 0.3, 1.2]),
        chisqr=0.0,
        redchi=0.0,
        aic=0.0,
        bic=0.0,
        nfev=1,
        success=True,
        message="ok",
        errorbars=False,
        method="leastsq",
    )
    return PostProcessing(
        df=source_df,
        minimizer=minimizer,
        result=result,
        is_global=True,
        conf_interval=False,
        bundle=None,
        source_x_column="binding_energy",
        source_y_columns=["signal_a", "signal_b"],
    )


@pytest.mark.unit
def test_postprocessing_call_keeps_instance_dataframe_immutable() -> None:
    """Calling post-processing should return a new enriched frame."""
    postprocessor, source_df = _build_local_postprocessor()
    renamed_input = postprocessor.df.copy(deep=True)

    result = postprocessor()

    pd.testing.assert_frame_equal(postprocessor.df, renamed_input)
    pd.testing.assert_frame_equal(
        source_df,
        pd.DataFrame(
            {
                "binding_energy": renamed_input[_COLS.energy].to_numpy(),
                "signal": renamed_input[_COLS.intensity].to_numpy(),
            }
        ),
    )
    assert list(postprocessor.df.columns) == [_COLS.energy, _COLS.intensity]
    assert list(result.df.columns) == [
        _COLS.energy,
        _COLS.intensity,
        _COLS.residual,
        _COLS.fit,
        "main",
    ]


@pytest.mark.unit
def test_postprocessing_result_dataframe_is_separate_from_instance_state() -> None:
    """The returned fit dataframe should not alias the stored input frame."""
    postprocessor, _ = _build_local_postprocessor()

    result = postprocessor()

    assert result.df is not postprocessor.df
    assert _COLS.residual not in postprocessor.df.columns
    assert _COLS.fit not in postprocessor.df.columns
    assert "main" not in postprocessor.df.columns


@pytest.mark.unit
def test_postprocessing_result_exposes_grouped_data_summary() -> None:
    """Post-processing should keep grouped typed summary data available."""
    postprocessor, _ = _build_local_postprocessor()

    result = postprocessor()

    assert isinstance(result.data_summary, DataSummary)
    assert result.data_summary.regression_metrics == result.regression_metrics
    assert result.data_summary.descriptive_statistic == result.descriptive_statistic
    assert result.data_summary.linear_correlation == result.linear_correlation


@pytest.mark.unit
def test_postprocessing_builds_global_residual_fit_columns_without_mutation() -> None:
    postprocessor = _build_global_postprocessor()
    original_df = postprocessor.df.copy(deep=True)

    result_df = postprocessor._make_residual_fit(postprocessor.df)  # noqa: SLF001

    pd.testing.assert_frame_equal(postprocessor.df, original_df)
    assert list(result_df.columns) == [
        _COLS.energy,
        f"{_COLS.intensity}_1",
        f"{_COLS.intensity}_2",
        f"{_COLS.residual}_1",
        f"{_COLS.fit}_1",
        f"{_COLS.residual}_2",
        f"{_COLS.fit}_2",
        f"{_COLS.residual}_avg",
    ]
    np.testing.assert_allclose(result_df[f"{_COLS.residual}_1"], [0.1, 0.2, 0.3])
    np.testing.assert_allclose(result_df[f"{_COLS.fit}_1"], [10.1, 20.2, 30.3])
    np.testing.assert_allclose(result_df[f"{_COLS.residual}_2"], [1.0, 1.1, 1.2])
    np.testing.assert_allclose(result_df[f"{_COLS.fit}_2"], [2.0, 3.1, 4.2])
    np.testing.assert_allclose(result_df[f"{_COLS.residual}_avg"], [0.55, 0.65, 0.75])


@pytest.mark.unit
def test_postprocessing_normalizes_only_valid_confidence_bounds() -> None:
    normalized = PostProcessing._normalize_confidence_bounds(  # noqa: SLF001
        {
            "p1_center": [
                (1, 0.25),
                [2, 0.5],
                ("bad", 0.75),
                (3,),
            ],
            "ignored": "not-iterable-bounds",
        }
    )

    assert normalized == {"p1_center": [(1.0, 0.25), (2.0, 0.5)]}


@pytest.mark.unit
def test_postprocessing_requires_y_column_for_standard_fit() -> None:
    df = pd.DataFrame({"binding_energy": [0.0]})
    minimizer = SimpleNamespace(max_nfev=5, nan_policy="raise")
    result = SimpleNamespace(
        params={},
        residual=np.array([0.0]),
        chisqr=0.0,
        redchi=0.0,
        aic=0.0,
        bic=0.0,
        nfev=1,
        success=True,
        message="ok",
        errorbars=False,
        method="leastsq",
    )

    with pytest.raises(
        ValueError,
        match="requires at least one y-column for standard fits",
    ):
        PostProcessing(
            df=df,
            minimizer=minimizer,
            result=result,
            is_global=False,
            conf_interval=False,
            bundle=None,
            source_x_column="binding_energy",
            source_y_columns=[],
        )

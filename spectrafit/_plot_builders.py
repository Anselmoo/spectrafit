"""Shared Plotly builders for CLI and notebook fit visualizations."""

from __future__ import annotations

import re

from typing import TYPE_CHECKING

import plotly.graph_objects as go

from plotly.colors import qualitative
from plotly.subplots import make_subplots
from pydantic import BaseModel
from pydantic import ConfigDict

from spectrafit.api.tools_model import ColumnNamesAPI


if TYPE_CHECKING:
    from collections.abc import Sequence

    import pandas as pd

    from spectrafit.models.split_frame import SplitFrame


_COLUMNS = ColumnNamesAPI()
_GLOBAL_SUFFIX_PATTERN = re.compile(r"_(\d+)$")
_LOCAL_COLUMNS = frozenset(_COLUMNS.model_dump().values())


class FitPlotStyle(BaseModel):
    """Visual styling for shared fit plots."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    intensity_color: str = qualitative.Plotly[0]
    residual_color: str = qualitative.Plotly[1]
    fit_color: str = qualitative.Plotly[5]
    component_colors: tuple[str, ...] = (qualitative.Plotly[6],)
    fit_dash: str = "dash"
    component_dash: str = "dot"
    show_legend: bool = True
    spectrum_title_prefix: str = "Spectrum #"


def component_columns(df: pd.DataFrame) -> list[str]:
    """Return non-canonical fit component columns for one fit dataframe."""
    return [str(column) for column in df.columns if str(column) not in _LOCAL_COLUMNS]


def iter_global_fit_frames(
    df: pd.DataFrame,
    *,
    data_statistic: SplitFrame | None = None,
) -> list[tuple[int, pd.DataFrame]]:
    """Project a global-fit dataframe into per-spectrum local-fit dataframes."""
    dataset_indices = _dataset_indices(df, data_statistic=data_statistic)
    frames = [
        (dataset_index, frame)
        for dataset_index in dataset_indices
        if (frame := _dataset_frame(df, dataset_index)) is not None
    ]
    return frames or [(1, df.copy())]


def build_local_fit_figure(
    df: pd.DataFrame,
    *,
    style: FitPlotStyle | None = None,
) -> go.Figure:
    """Build a local-fit Plotly figure with residual and fit panels."""
    resolved_style = style or FitPlotStyle()
    figure = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.25, 0.75],
    )
    residual_traces, fit_traces = _build_local_fit_traces(
        df,
        style=resolved_style,
        showlegend=resolved_style.show_legend,
    )
    for trace in residual_traces:
        figure.add_trace(trace, row=1, col=1)
    for trace in fit_traces:
        figure.add_trace(trace, row=2, col=1)
    return figure


def build_global_fit_figure(
    df: pd.DataFrame,
    *,
    data_statistic: SplitFrame | None = None,
    style: FitPlotStyle | None = None,
) -> go.Figure:
    """Build a global-fit Plotly figure with one column per dataset."""
    resolved_style = style or FitPlotStyle()
    frames = iter_global_fit_frames(df, data_statistic=data_statistic)
    figure = make_subplots(
        rows=2,
        cols=len(frames),
        shared_xaxes=True,
        vertical_spacing=0.05,
        horizontal_spacing=0.04,
        row_heights=[0.25, 0.75],
        subplot_titles=[
            f"{resolved_style.spectrum_title_prefix}{dataset_index}"
            for dataset_index, _ in frames
        ],
    )
    for column_index, (_, frame) in enumerate(frames, start=1):
        residual_traces, fit_traces = _build_local_fit_traces(
            frame,
            style=resolved_style,
            showlegend=resolved_style.show_legend and column_index == 1,
        )
        for trace in residual_traces:
            figure.add_trace(trace, row=1, col=column_index)
        for trace in fit_traces:
            figure.add_trace(trace, row=2, col=column_index)
    return figure


def _build_local_fit_traces(
    df: pd.DataFrame,
    *,
    style: FitPlotStyle,
    showlegend: bool,
) -> tuple[list[go.Scatter], list[go.Scatter]]:
    x_values = df[_COLUMNS.energy]
    residual_traces = [
        go.Scatter(
            x=x_values,
            y=df[_COLUMNS.residual],
            mode="lines",
            name=_COLUMNS.residual,
            line={"color": style.residual_color},
            showlegend=showlegend,
            legendgroup=_COLUMNS.residual,
        )
    ]
    fit_traces = [
        go.Scatter(
            x=x_values,
            y=df[_COLUMNS.intensity],
            mode="lines",
            name=_COLUMNS.intensity,
            line={"color": style.intensity_color},
            showlegend=showlegend,
            legendgroup=_COLUMNS.intensity,
        ),
        go.Scatter(
            x=x_values,
            y=df[_COLUMNS.fit],
            mode="lines",
            name=_COLUMNS.fit,
            line={"color": style.fit_color, "dash": style.fit_dash},
            showlegend=showlegend,
            legendgroup=_COLUMNS.fit,
        ),
    ]
    for component, color in zip(
        component_columns(df),
        _resolve_component_colors(style.component_colors, len(component_columns(df))),
        strict=False,
    ):
        fit_traces.append(
            go.Scatter(
                x=x_values,
                y=df[component],
                mode="lines",
                name=component,
                line={"color": color, "dash": style.component_dash},
                showlegend=showlegend,
                legendgroup=component,
            )
        )
    return residual_traces, fit_traces


def _resolve_component_colors(
    component_colors: Sequence[str],
    component_count: int,
) -> list[str]:
    palette = list(component_colors) or [qualitative.Plotly[6]]
    return [palette[index % len(palette)] for index in range(component_count)]


def _dataset_indices(
    df: pd.DataFrame,
    *,
    data_statistic: SplitFrame | None,
) -> list[int]:
    indices = sorted(
        {
            int(match.group(1))
            for column in df.columns
            if (match := _GLOBAL_SUFFIX_PATTERN.search(str(column))) is not None
        }
    )
    if indices:
        return indices
    if data_statistic is not None and data_statistic.index:
        return list(range(1, len(data_statistic.index) + 1))
    return []


def _dataset_frame(df: pd.DataFrame, dataset_index: int) -> pd.DataFrame | None:
    dataset_suffix = f"_{dataset_index}"
    scoped_columns = [
        str(column) for column in df.columns if str(column).endswith(dataset_suffix)
    ]
    if not scoped_columns:
        return None
    renamed_columns = {
        _COLUMNS.intensity_for_dataset(dataset_index): _COLUMNS.intensity,
        _COLUMNS.fit_for_dataset(dataset_index): _COLUMNS.fit,
        _COLUMNS.residual_for_dataset(dataset_index): _COLUMNS.residual,
    }
    return df[[_COLUMNS.energy, *scoped_columns]].rename(columns=renamed_columns)

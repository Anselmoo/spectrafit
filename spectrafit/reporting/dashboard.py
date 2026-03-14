"""Static dashboard rendering helpers for canonical fit results."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import TypedDict

from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from spectrafit.reporting.service import DashboardPayload
from spectrafit.reporting.service import DashboardTrace
from spectrafit.reporting.service import project_dashboard_payload


if TYPE_CHECKING:
    from spectrafit.models.results.fit_result import FitResult


class TraceStyle(TypedDict):
    """Supported Matplotlib line styling for dashboard traces."""

    color: str
    linestyle: str
    linewidth: float


def _trace_style(trace: DashboardTrace, component_index: int) -> TraceStyle:
    """Return deterministic Matplotlib styling for one dashboard trace."""
    if trace.trace_kind == "observed":
        return {"color": "C0", "linestyle": "-", "linewidth": 1.8}
    if trace.trace_kind == "fit":
        return {"color": "C1", "linestyle": "--", "linewidth": 1.8}
    return {
        "color": f"C{2 + component_index}",
        "linestyle": ":",
        "linewidth": 1.2,
    }


def _summary_lines(payload: DashboardPayload) -> list[str]:
    """Build benchmark-friendly summary lines for the static dashboard panel."""
    return [
        f"Mode: {payload.global_fitting}",
        f"Method: {payload.statistics.method or 'unknown'}",
        f"Chi-square: {payload.summary.chi_square}",
        f"Reduced chi-square: {payload.summary.reduced_chi_square}",
        f"AIC: {payload.summary.akaike_information}",
        f"BIC: {payload.summary.bayesian_information}",
        f"Parameters: {len(payload.parameters)}",
        f"Components: {len(payload.components)}",
    ]


def build_dashboard_figure(
    payload: DashboardPayload,
    *,
    figsize: tuple[float, float] = (10.0, 7.0),
) -> Figure:
    """Build a deterministic Matplotlib dashboard figure from typed payload data."""
    figure = Figure(figsize=figsize, constrained_layout=True)
    FigureCanvasAgg(figure)
    grid = figure.add_gridspec(2, 1, height_ratios=[3.5, 1.2])
    trace_axis = figure.add_subplot(grid[0, 0])
    summary_axis = figure.add_subplot(grid[1, 0])

    component_index = 0
    for trace in payload.traces:
        trace_axis.plot(
            payload.x_values,
            trace.y_values,
            label=trace.label,
            **_trace_style(trace, component_index),
        )
        if trace.trace_kind == "component":
            component_index += 1

    trace_axis.set_title(payload.title)
    trace_axis.set_xlabel(payload.x_label)
    trace_axis.set_ylabel(payload.y_label)
    trace_axis.grid(True, alpha=0.25)
    if payload.traces:
        trace_axis.legend(loc="best")

    summary_axis.axis("off")
    summary_axis.text(
        0.01,
        0.98,
        "\n".join(_summary_lines(payload)),
        va="top",
        ha="left",
        family="monospace",
    )

    return figure


def write_dashboard_png(
    fit_result: FitResult | DashboardPayload,
    output_path: str | Path,
    *,
    dpi: int = 150,
) -> Path:
    """Write a static PNG dashboard from canonical fit-result data."""
    payload = (
        fit_result
        if isinstance(fit_result, DashboardPayload)
        else project_dashboard_payload(fit_result)
    )
    resolved_output = Path(output_path)
    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    figure = build_dashboard_figure(payload)
    try:
        figure.savefig(resolved_output, dpi=dpi, bbox_inches="tight")
    finally:
        figure.clear()
    return resolved_output

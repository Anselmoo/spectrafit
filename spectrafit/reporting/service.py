"""Shared report rendering helpers for canonical ``FitResult`` data."""

from __future__ import annotations

import sys

from typing import TYPE_CHECKING
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict


if TYPE_CHECKING:
    from collections.abc import Iterable

    from spectrafit.models.results.fit_result import ComponentResult
    from spectrafit.models.results.fit_result import ComputationalMeta
    from spectrafit.models.results.fit_result import FitConfigurations
    from spectrafit.models.results.fit_result import FitResult
    from spectrafit.models.results.fit_result import FitStatistics
    from spectrafit.models.results.fit_result import ParameterResult
    from spectrafit.models.results.fit_result import VariableFitResult
    from spectrafit.models.split_frame import SplitFrame


type ConfidenceSettingValue = bool | int | str | list[str]


class SolverReportProjection(BaseModel):
    """Typed solver-facing report projection derived from canonical ``FitResult``."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    goodness_of_fit: dict[str, float]
    regression_metrics: SplitFrame
    descriptive_statistic: SplitFrame
    linear_correlation: SplitFrame
    component_correlation: dict[str, dict[str, float]]
    confidence_interval: dict[str, list[tuple[float, float]]]
    covariance_matrix: dict[str, dict[str, float]]
    variables: dict[str, VariableFitResult]
    errorbars: dict[str, str]
    computational: ComputationalMeta


class FitSummaryProjection(BaseModel):
    """Typed summary metrics used by notebook and report presentation layers."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    chi_square: float | None = None
    reduced_chi_square: float | None = None
    akaike_information: float | None = None
    bayesian_information: float | None = None


class RuntimeReportPayload(BaseModel):
    """Typed JSON payload for verbose runtime report emission."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    preprocessing: SplitFrame
    fit_result: FitResult


class CanonicalReportSchema(BaseModel):
    """Single canonical report/result projection owned by the reporting service.

    This model is the active runtime reporting contract for SpectraFit. Runtime
    renderers and frozen compatibility adapters should derive their output from
    this projection instead of inventing parallel schemas in the legacy frozen
    report package.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    summary: FitSummaryProjection
    solver: SolverReportProjection
    statistics: FitStatistics
    configurations: FitConfigurations
    confidence_settings: bool | dict[str, ConfidenceSettingValue]


class DashboardTrace(BaseModel):
    """Typed series metadata for dashboard and benchmark-friendly rendering."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    y_values: list[float]
    trace_kind: Literal["observed", "fit", "component"]
    component_id: str | None = None
    model: str | None = None


class DashboardPayload(BaseModel):
    """Typed dashboard/report payload projected from canonical ``FitResult`` data."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    title: str = "SpectraFit Dashboard"
    x_label: str = "energy"
    y_label: str = "intensity"
    x_values: list[float]
    traces: list[DashboardTrace]
    summary: FitSummaryProjection
    statistics: FitStatistics
    parameters: list[ParameterResult]
    components: list[ComponentResult]
    global_fitting: str
    confidence_settings: bool | dict[str, ConfidenceSettingValue]


class JsonReportDocument(BaseModel):
    """Typed JSON document emitted by the shared report renderer."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    summary: FitSummaryProjection | None = None
    variables: dict[str, VariableFitResult] | None = None
    regression_metrics: SplitFrame | None = None
    correlation: SplitFrame | None = None


def _solver_report_types() -> dict[str, type[object]]:
    """Resolve runtime types for ``SolverReportProjection`` model rebuilding."""
    from spectrafit.models.results.fit_result import ComponentResult  # noqa: PLC0415
    from spectrafit.models.results.fit_result import ComputationalMeta  # noqa: PLC0415
    from spectrafit.models.results.fit_result import FitConfigurations  # noqa: PLC0415
    from spectrafit.models.results.fit_result import FitResult  # noqa: PLC0415
    from spectrafit.models.results.fit_result import FitStatistics  # noqa: PLC0415
    from spectrafit.models.results.fit_result import ParameterResult  # noqa: PLC0415
    from spectrafit.models.results.fit_result import VariableFitResult  # noqa: PLC0415
    from spectrafit.models.split_frame import SplitFrame  # noqa: PLC0415

    return {
        "ComputationalMeta": ComputationalMeta,
        "ComponentResult": ComponentResult,
        "FitConfigurations": FitConfigurations,
        "FitResult": FitResult,
        "FitStatistics": FitStatistics,
        "ParameterResult": ParameterResult,
        "VariableFitResult": VariableFitResult,
        "SplitFrame": SplitFrame,
    }


_REPORT_TYPES = _solver_report_types()

CanonicalReportSchema.model_rebuild(_types_namespace=_REPORT_TYPES)
DashboardPayload.model_rebuild(_types_namespace=_REPORT_TYPES)
DashboardTrace.model_rebuild(_types_namespace=_REPORT_TYPES)
SolverReportProjection.model_rebuild(_types_namespace=_REPORT_TYPES)
RuntimeReportPayload.model_rebuild(_types_namespace=_REPORT_TYPES)
JsonReportDocument.model_rebuild(_types_namespace=_REPORT_TYPES)


VERBOSE_DETAILED = 2


def normalize_confidence_interval_settings(
    fit_result: FitResult,
) -> bool | dict[str, ConfidenceSettingValue]:
    """Project canonical confidence settings to the public report contract."""
    return fit_result.confidence.report_settings()


def _has_material_fit_statistics(fit_result: FitResult) -> bool:
    """Return whether canonical fit statistics carry meaningful summary values."""
    statistics = fit_result.statistics
    return bool(
        statistics.method
        or statistics.chisqr
        or statistics.redchi
        or statistics.aic
        or statistics.bic
    )


def project_fit_summary(fit_result: FitResult) -> FitSummaryProjection:
    """Normalize fit summary statistics for presentation adapters."""
    summary_values = dict(fit_result.fit_insights.statistics)
    if _has_material_fit_statistics(fit_result):
        if "chi_square" not in summary_values:
            summary_values["chi_square"] = fit_result.statistics.chisqr
        if "reduced_chi_square" not in summary_values:
            summary_values["reduced_chi_square"] = fit_result.statistics.redchi
        if "akaike_information" not in summary_values:
            summary_values["akaike_information"] = fit_result.statistics.aic
        if "bayesian_information" not in summary_values:
            summary_values["bayesian_information"] = fit_result.statistics.bic
    return FitSummaryProjection.model_validate(summary_values)


def project_canonical_report(fit_result: FitResult) -> CanonicalReportSchema:
    """Project canonical ``FitResult`` data into the singular reporting schema."""
    return CanonicalReportSchema(
        summary=project_fit_summary(fit_result),
        solver=project_solver_report(fit_result),
        statistics=fit_result.statistics,
        configurations=fit_result.fit_insights.configurations,
        confidence_settings=normalize_confidence_interval_settings(fit_result),
    )


def project_dashboard_payload(fit_result: FitResult) -> DashboardPayload:
    """Project canonical ``FitResult`` data into a dashboard-friendly payload."""
    traces = [
        DashboardTrace(
            label="Observed",
            y_values=fit_result.y_data,
            trace_kind="observed",
        ),
        DashboardTrace(
            label="Fit",
            y_values=fit_result.y_fit,
            trace_kind="fit",
        ),
        *[
            DashboardTrace(
                label=component.id,
                y_values=component.curve,
                trace_kind="component",
                component_id=component.id,
                model=component.model,
            )
            for component in fit_result.components
        ],
    ]
    return DashboardPayload(
        x_values=fit_result.x,
        traces=traces,
        summary=project_fit_summary(fit_result),
        statistics=fit_result.statistics,
        parameters=fit_result.parameters,
        components=fit_result.components,
        global_fitting=fit_result.global_fitting.value,
        confidence_settings=normalize_confidence_interval_settings(fit_result),
    )


def project_solver_report(fit_result: FitResult) -> SolverReportProjection:
    """Project canonical ``FitResult`` fields into the solver report shape."""
    return SolverReportProjection.model_construct(
        # ``fit_result`` already owns validation; this layer only reshapes
        # canonical typed state for downstream report/export consumers.
        goodness_of_fit=fit_result.fit_insights.statistics,
        regression_metrics=fit_result.data_summary.regression_metrics,
        descriptive_statistic=fit_result.data_summary.descriptive_statistic,
        linear_correlation=fit_result.data_summary.linear_correlation,
        component_correlation=fit_result.fit_insights.correlations,
        confidence_interval=fit_result.confidence.report_results(),
        covariance_matrix=fit_result.fit_insights.covariance_matrix,
        variables=fit_result.fit_insights.variables,
        errorbars=fit_result.fit_insights.errorbars,
        computational=fit_result.fit_insights.computational,
    )


def _frame_has_columns(frame: SplitFrame) -> bool:
    """Return whether a split-orient frame contains any columns."""
    return bool(frame.columns)


def _iter_frame_rows(
    frame: SplitFrame,
) -> Iterable[tuple[str | int | float, list[float | int | str | None]]]:
    """Iterate split-orient frame rows paired with their labels."""
    return zip(frame.columns, frame.data, strict=False)


def _iter_frame_index_rows(
    frame: SplitFrame,
) -> Iterable[tuple[str | int | float, list[float | int | str | None]]]:
    """Iterate split-orient frame rows using index labels when available."""
    return zip(frame.index, frame.data, strict=False)


def _append_text_statistics(summary: FitSummaryProjection, lines: list[str]) -> None:
    """Append goodness-of-fit statistics to report lines."""
    lines.append(f"  Chi-square:      {summary.chi_square}")
    lines.append(f"  Reduced chi-sq:  {summary.reduced_chi_square}")
    lines.append(f"  AIC:             {summary.akaike_information}")
    lines.append(f"  BIC:             {summary.bayesian_information}")


def _append_text_variables(
    variables: dict[str, VariableFitResult],
    lines: list[str],
) -> None:
    """Append variable summary lines to a text report."""
    if not variables:
        return

    lines.extend(("\n📈 FIT VARIABLES", "-" * 40))
    for var_name, variable in variables.items():
        lines.append(
            f"  {var_name}: best={variable.best_value}, stderr={variable.stderr}"
        )


def _render_split_frame_section(
    title: str,
    frame: SplitFrame,
) -> str:
    """Render a split-orient frame as a plain-text section."""
    if not _frame_has_columns(frame):
        return ""

    lines = [title, "-" * 40]
    for label, row in _iter_frame_index_rows(frame):
        lines.append(f"  {label}: {row}")
    return "\n".join(lines)


def _render_confidence_section(fit_result: FitResult) -> str:
    """Render typed confidence interval output as a plain-text section."""
    confidence = fit_result.confidence
    if confidence.settings is False or not confidence.results:
        return ""

    lines = ["Confidence intervals", "-" * 40]
    for parameter, bounds in confidence.results.items():
        formatted_bounds = ", ".join(f"({sigma}, {bound})" for sigma, bound in bounds)
        lines.append(f"  {parameter}: {formatted_bounds}")
    return "\n".join(lines)


def render_text_report(fit_result: FitResult, sections: list[str]) -> str:
    """Render a plain text report from canonical fit results."""
    lines: list[str] = ["=" * 60, "SpectraFit Report", "=" * 60]
    report_schema = project_canonical_report(fit_result)
    solver_projection = report_schema.solver

    if "summary" in sections:
        lines.extend(("\n📊 FIT SUMMARY", "-" * 40))
        _append_text_statistics(report_schema.summary, lines)

    if "variables" in sections:
        _append_text_variables(solver_projection.variables, lines)

    if "statistics" in sections and _frame_has_columns(
        solver_projection.regression_metrics
    ):
        metrics = solver_projection.regression_metrics
        lines.extend(("\n📉 REGRESSION METRICS", "-" * 40))
        for col, row in _iter_frame_rows(metrics):
            lines.append(f"  {col}: {row}")

    if "correlation" in sections and _frame_has_columns(
        solver_projection.linear_correlation
    ):
        lines.extend(("\n🔗 CORRELATION MATRIX", "-" * 40))
        lines.append("  (See full correlation in _correlation.csv file)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def render_runtime_report(
    *,
    fit_result: FitResult,
    data_statistic: SplitFrame,
    verbose: int,
) -> str:
    """Render the runtime fit output for interactive CLI usage."""
    if verbose <= 0:
        return ""

    if verbose >= VERBOSE_DETAILED:
        return RuntimeReportPayload(
            preprocessing=data_statistic,
            fit_result=fit_result,
        ).model_dump_json(indent=2)

    blocks = [
        _render_split_frame_section("Preprocessing statistics", data_statistic),
        render_text_report(
            fit_result,
            ["summary", "variables", "statistics", "correlation"],
        ),
        _render_confidence_section(fit_result),
    ]
    return "\n\n".join(block for block in blocks if block)


def emit_runtime_report(
    *,
    fit_result: FitResult,
    data_statistic: SplitFrame,
    verbose: int,
) -> None:
    """Emit runtime fit output to stdout using the shared typed report service."""
    report = render_runtime_report(
        fit_result=fit_result,
        data_statistic=data_statistic,
        verbose=verbose,
    )
    if report:
        sys.stdout.write(f"{report}\n")


def render_markdown_report(fit_result: FitResult, sections: list[str]) -> str:
    """Render a Markdown report from canonical fit results."""
    report_schema = project_canonical_report(fit_result)
    summary = report_schema.summary
    solver_projection = report_schema.solver
    lines: list[str] = ["# SpectraFit Report\n"]

    if "summary" in sections:
        lines.extend(
            (
                "## Fit Summary\n",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Chi-square | {summary.chi_square} |",
                f"| Reduced chi-sq | {summary.reduced_chi_square} |",
                f"| AIC | {summary.akaike_information} |",
                f"| BIC | {summary.bayesian_information} |",
                "",
            )
        )

    if "variables" in sections:
        variables = solver_projection.variables
        if variables:
            lines.extend(
                (
                    "## Fit Variables\n",
                    "| Parameter | Best Value | Stderr |",
                    "|-----------|------------|--------|",
                )
            )
            for var_name, var in variables.items():
                lines.append(f"| {var_name} | {var.best_value} | {var.stderr} |")
            lines.append("")

    if "statistics" in sections and _frame_has_columns(
        solver_projection.regression_metrics
    ):
        metrics = solver_projection.regression_metrics
        lines.extend(
            ("## Regression Metrics\n", "| Metric | Value |", "|--------|-------|")
        )
        for col, row in _iter_frame_rows(metrics):
            lines.append(f"| {col} | {row} |")
        lines.append("")

    return "\n".join(lines)


def render_json_report(fit_result: FitResult, sections: list[str]) -> str:
    """Render a JSON report from canonical fit results."""
    report_schema = project_canonical_report(fit_result)
    summary = report_schema.summary
    solver_projection = report_schema.solver
    report_document = JsonReportDocument()

    if "summary" in sections:
        report_document = report_document.model_copy(update={"summary": summary})

    if "variables" in sections:
        report_document = report_document.model_copy(
            update={"variables": solver_projection.variables}
        )

    if "statistics" in sections and _frame_has_columns(
        solver_projection.regression_metrics
    ):
        report_document = report_document.model_copy(
            update={"regression_metrics": solver_projection.regression_metrics}
        )

    if "correlation" in sections and _frame_has_columns(
        solver_projection.linear_correlation
    ):
        report_document = report_document.model_copy(
            update={"correlation": solver_projection.linear_correlation}
        )

    return report_document.model_dump_json(indent=2, exclude_none=True)


def render_report(fit_result: FitResult, format_: str, sections: list[str]) -> str:
    """Render a report in the requested format."""
    if format_ == "json":
        return render_json_report(fit_result, sections)
    if format_ == "markdown":
        return render_markdown_report(fit_result, sections)
    return render_text_report(fit_result, sections)

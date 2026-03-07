"""Report command for SpectraFit CLI."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.models.fit_summary import FitInsightsReport
from spectrafit.models.fit_summary import FitSummaryReport


def report(
    results_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the SpectraFit results JSON file (_summary.json).",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output: Annotated[
        Path | None,
        typer.Option(
            "-o",
            "--output",
            help="Output file path for the report. If not specified, prints to stdout.",
        ),
    ] = None,
    format_: Annotated[
        str,
        typer.Option(
            "-f",
            "--format",
            help="Report format: 'text', 'markdown', or 'json'.",
        ),
    ] = "text",
    sections: Annotated[
        list[str] | None,
        typer.Option(
            "-s",
            "--section",
            help="Sections to include: 'summary', 'variables', 'statistics', 'correlation'.",
        ),
    ] = None,
) -> None:
    """Generate a report from SpectraFit fitting results.

    This command reads a SpectraFit results JSON file and generates a formatted
    report with fit statistics, variables, and correlation information.

    Examples:
        spectrafit report fit_results_summary.json
        spectrafit report results.json -f markdown -o report.md
        spectrafit report results.json -s summary -s variables
    """
    try:
        summary = FitSummaryReport.from_json_file(results_file)
        active_sections = (
            sections if sections is not None else ["summary", "variables", "statistics"]
        )

        if format_ == "json":
            report_content = _generate_json_report(summary, active_sections)
        elif format_ == "markdown":
            report_content = _generate_markdown_report(summary, active_sections)
        else:
            report_content = _generate_text_report(summary, active_sections)

        if output:
            output.write_text(report_content, encoding="utf-8")
            typer.echo(f"✅ Report saved to '{output}'")
        else:
            typer.echo(report_content)

    except Exception as e:
        typer.echo(f"❌ Error generating report: {e}", err=True)
        raise typer.Exit(1) from e


def _generate_text_report(summary: FitSummaryReport, sections: list[str]) -> str:
    """Generate a plain text report.

    Args:
        summary: Validated fit summary model.
        sections: Sections to include.

    Returns:
        Formatted text report.
    """
    lines: list[str] = ["=" * 60, "SpectraFit Report", "=" * 60]

    if "summary" in sections:
        lines.extend(("\n📊 FIT SUMMARY", "-" * 40))
        _append_text_statistics(summary.fit_insights, lines)

    if "variables" in sections:
        variables = summary.fit_insights.variables
        if variables:
            lines.extend(("\n📈 FIT VARIABLES", "-" * 40))
            for var_name, var in variables.items():
                lines.extend(
                    (
                        f"  {var_name}:",
                        f"    Best value: {var.best_value}",
                        f"    Stderr:     {var.stderr}",
                    )
                )

    if "statistics" in sections and summary.regression_metrics.columns:
        metrics = summary.regression_metrics
        lines.extend(("\n📉 REGRESSION METRICS", "-" * 40))
        for col, row in zip(metrics.columns, metrics.data, strict=False):
            lines.append(f"  {col}: {row}")

    if "correlation" in sections and summary.linear_correlation:
        lines.extend(("\n🔗 CORRELATION MATRIX", "-" * 40))
        lines.append("  (See full correlation in _correlation.csv file)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def _append_text_statistics(insights: FitInsightsReport, lines: list[str]) -> None:
    """Append goodness-of-fit statistics to report lines.

    Args:
        insights: Fit insights model.
        lines: Mutable list of report lines.
    """
    stats = insights.statistics
    lines.append(f"  Chi-square:      {stats.chi_square}")
    lines.append(f"  Reduced chi-sq:  {stats.reduced_chi_square}")
    lines.append(f"  AIC:             {stats.akaike_information}")
    lines.append(f"  BIC:             {stats.bayesian_information}")


def _generate_markdown_report(summary: FitSummaryReport, sections: list[str]) -> str:
    """Generate a Markdown report.

    Args:
        summary: Validated fit summary model.
        sections: Sections to include.

    Returns:
        Formatted Markdown report.
    """
    stats = summary.fit_insights.statistics
    lines: list[str] = ["# SpectraFit Report\n"]

    if "summary" in sections:
        lines.extend(
            (
                "## Fit Summary\n",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Chi-square | {stats.chi_square} |",
                f"| Reduced chi-sq | {stats.reduced_chi_square} |",
                f"| AIC | {stats.akaike_information} |",
                f"| BIC | {stats.bayesian_information} |",
                "",
            )
        )

    if "variables" in sections:
        variables = summary.fit_insights.variables
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

    if "statistics" in sections and summary.regression_metrics.columns:
        metrics = summary.regression_metrics
        lines.extend(
            ("## Regression Metrics\n", "| Metric | Value |", "|--------|-------|")
        )
        for col, row in zip(metrics.columns, metrics.data, strict=False):
            lines.append(f"| {col} | {row} |")
        lines.append("")

    return "\n".join(lines)


def _generate_json_report(summary: FitSummaryReport, sections: list[str]) -> str:
    """Generate a JSON report with selected sections.

    Args:
        summary: Validated fit summary model.
        sections: Sections to include.

    Returns:
        JSON formatted report.
    """
    report_data: dict[str, object] = {}

    if "summary" in sections:
        report_data["summary"] = summary.fit_insights.statistics.model_dump(
            exclude_none=True
        )

    if "variables" in sections:
        report_data["variables"] = {
            k: v.model_dump(exclude_none=True)
            for k, v in summary.fit_insights.variables.items()
        }

    if "statistics" in sections and summary.regression_metrics.columns:
        report_data["regression_metrics"] = summary.regression_metrics.model_dump()

    if "correlation" in sections and summary.linear_correlation.columns:
        report_data["correlation"] = summary.linear_correlation.model_dump()

    return json.dumps(report_data, indent=2)

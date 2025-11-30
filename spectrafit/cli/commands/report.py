"""Report command for SpectraFit CLI."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Annotated
from typing import Any

import typer


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
        # Read results file
        with results_file.open(encoding="utf-8") as f:
            results = json.load(f)

        # Default sections if none specified
        if sections is None:
            sections = ["summary", "variables", "statistics"]

        # Generate report
        if format_ == "json":
            report_content = _generate_json_report(results, sections)
        elif format_ == "markdown":
            report_content = _generate_markdown_report(results, sections)
        else:
            report_content = _generate_text_report(results, sections)

        # Output report
        if output:
            output.write_text(report_content, encoding="utf-8")
            typer.echo(f"✅ Report saved to '{output}'")
        else:
            typer.echo(report_content)

    except json.JSONDecodeError as e:
        typer.echo(f"❌ Invalid JSON file: {e}", err=True)
        raise typer.Exit(1) from e
    except KeyError as e:
        typer.echo(f"❌ Missing expected key in results: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"❌ Error generating report: {e}", err=True)
        raise typer.Exit(1) from e


def _generate_text_report(results: dict[str, Any], sections: list[str]) -> str:
    """Generate a plain text report.

    Args:
        results: Fit results dictionary.
        sections: Sections to include.

    Returns:
        Formatted text report.
    """
    lines: list[str] = ["=" * 60, "SpectraFit Report", "=" * 60]

    if "summary" in sections and "fit_insights" in results:
        insights = results["fit_insights"]
        lines.append("\n📊 FIT SUMMARY")
        lines.append("-" * 40)
        if "statistics" in insights:
            _append_summary_statistics(insights, lines)
    if "variables" in sections and "fit_insights" in results:
        insights = results["fit_insights"]
        if "variables" in insights:
            lines.append("\n📈 FIT VARIABLES")
            lines.append("-" * 40)
            variables = insights["variables"]
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    value = var_data.get("value", "N/A")
                    stderr = var_data.get("stderr", "N/A")
                    lines.append(f"  {var_name}:")
                    lines.append(f"    Value:  {value}")
                    lines.append(f"    Stderr: {stderr}")

    if "statistics" in sections and "regression_metrics" in results:
        metrics = results["regression_metrics"]
        lines.extend(("\n📉 REGRESSION METRICS", "-" * 40))
        for key, value in metrics.items():
            lines.append(f"  {key}: {value}")

    if "correlation" in sections and "linear_correlation" in results:
        lines.append("\n🔗 CORRELATION MATRIX")
        lines.append("-" * 40)
        lines.append("  (See full correlation in _correlation.csv file)")

    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


def _append_summary_statistics(insights: dict[str, Any], lines: list[str]) -> None:
    """Append summary statistics to the report lines.

    Args:
        insights: Fit insights dictionary.
        lines: List of report lines to append to.
    """
    stats = insights["statistics"]
    lines.append(f"  Chi-square:      {stats.get('chi_square', 'N/A')}")
    lines.append(f"  Reduced chi-sq:  {stats.get('reduced_chi_square', 'N/A')}")
    lines.append(f"  AIC:             {stats.get('aic', 'N/A')}")
    lines.append(f"  BIC:             {stats.get('bic', 'N/A')}")
    lines.append(f"  R-squared:       {stats.get('rsquared', 'N/A')}")


def _generate_markdown_report(results: dict[str, Any], sections: list[str]) -> str:
    """Generate a Markdown report.

    Args:
        results: Fit results dictionary.
        sections: Sections to include.

    Returns:
        Formatted Markdown report.
    """
    lines: list[str] = []
    lines.append("# SpectraFit Report\n")

    if "summary" in sections and "fit_insights" in results:
        insights = results["fit_insights"]
        lines.append("## Fit Summary\n")

        if "statistics" in insights:
            stats = insights["statistics"]
            lines.append("| Metric | Value |")
            lines.append("|--------|-------|")
            lines.append(f"| Chi-square | {stats.get('chi_square', 'N/A')} |")
            lines.append(
                f"| Reduced chi-sq | {stats.get('reduced_chi_square', 'N/A')} |"
            )
            lines.append(f"| AIC | {stats.get('aic', 'N/A')} |")
            lines.append(f"| BIC | {stats.get('bic', 'N/A')} |")
            lines.append(f"| R-squared | {stats.get('rsquared', 'N/A')} |")
            lines.append("")

    if "variables" in sections and "fit_insights" in results:
        insights = results["fit_insights"]
        if "variables" in insights:
            lines.append("## Fit Variables\n")
            lines.append("| Parameter | Value | Stderr |")
            lines.append("|-----------|-------|--------|")
            variables = insights["variables"]
            for var_name, var_data in variables.items():
                if isinstance(var_data, dict):
                    value = var_data.get("value", "N/A")
                    stderr = var_data.get("stderr", "N/A")
                    lines.append(f"| {var_name} | {value} | {stderr} |")
            lines.append("")

    if "statistics" in sections and "regression_metrics" in results:
        metrics = results["regression_metrics"]
        lines.append("## Regression Metrics\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        for key, value in metrics.items():
            lines.append(f"| {key} | {value} |")
        lines.append("")

    return "\n".join(lines)


def _generate_json_report(results: dict[str, Any], sections: list[str]) -> str:
    """Generate a JSON report with selected sections.

    Args:
        results: Fit results dictionary.
        sections: Sections to include.

    Returns:
        JSON formatted report.
    """
    report_data: dict[str, Any] = {}

    if "summary" in sections and "fit_insights" in results:
        report_data["summary"] = results["fit_insights"].get("statistics", {})

    if "variables" in sections and "fit_insights" in results:
        report_data["variables"] = results["fit_insights"].get("variables", {})

    if "statistics" in sections and "regression_metrics" in results:
        report_data["regression_metrics"] = results["regression_metrics"]

    if "correlation" in sections and "linear_correlation" in results:
        report_data["correlation"] = results["linear_correlation"]

    return json.dumps(report_data, indent=2)

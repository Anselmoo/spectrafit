"""Report command for SpectraFit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.adapters.fit_result_json import load_fit_result
from spectrafit.reporting.service import render_report


def report(
    results_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the SpectraFit saved results JSON file.",
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
        fit_result = load_fit_result(results_file)
        active_sections = (
            sections if sections is not None else ["summary", "variables", "statistics"]
        )

        report_content = render_report(fit_result, format_, active_sections)

        if output:
            output.write_text(report_content, encoding="utf-8")
            typer.echo(
                typer.style(f"✅ Report saved to '{output}'", fg=typer.colors.GREEN)
            )
        else:
            typer.echo(report_content)

    except Exception as e:
        typer.echo(
            typer.style(f"❌ Error generating report: {e}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(1) from e

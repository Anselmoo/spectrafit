"""Shared callbacks for CLI commands."""

from __future__ import annotations

import typer

from spectrafit.report import PrintingStatus


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        status = PrintingStatus()
        typer.echo(status.version())
        raise typer.Exit

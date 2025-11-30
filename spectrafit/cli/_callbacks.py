"""Shared callbacks for CLI commands."""

from __future__ import annotations

import typer

from spectrafit.report import PrintingStatus


__status__ = PrintingStatus()


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        typer.echo(__status__.version())
        raise typer.Exit

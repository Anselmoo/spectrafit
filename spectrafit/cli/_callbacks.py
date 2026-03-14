"""Shared callbacks for CLI commands."""

from __future__ import annotations

import typer

from spectrafit.cli._status import cli_status


def version_callback(value: bool) -> None:
    """Display version information."""
    if value:
        typer.echo(cli_status.version())
        raise typer.Exit

"""Jupyter command for SpectraFit CLI.

Provides the top-level ``spectrafit jupyter`` command for launching Jupyter Lab
with SpectraFit integration. This replaces the former ``spectrafit plugins jupyter``
plugin path.
"""

from __future__ import annotations

import typer


def jupyter() -> None:
    """Launch Jupyter Lab for interactive SpectraFit analysis.

    Opens Jupyter Lab with SpectraFit integration for interactive
    data analysis, fitting, and visualization.

    Examples:
        ```bash
        spectrafit jupyter
        ```

    !!! note "Requirements"
        Requires the ``[jupyter]`` optional dependency group:
        ``pip install spectrafit[jupyter]``
    """
    try:
        from spectrafit.app.app import jupyter as jupyter_app

        typer.echo("🚀 Launching Jupyter Lab with SpectraFit integration...")
        typer.echo("   Press Ctrl+C to stop the server.\n")
        jupyter_app()

    except ImportError as e:
        typer.echo(
            "❌ Jupyter dependencies are not installed.",
            err=True,
        )
        typer.echo(
            "   Install with: pip install spectrafit[jupyter]",
            err=True,
        )
        typer.echo(f"\n   Error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"❌ Unexpected error launching Jupyter: {e}", err=True)
        raise typer.Exit(1) from e

"""Jupyter command for SpectraFit CLI.

Provides the top-level ``spectrafit jupyter`` command for launching Jupyter Lab
with SpectraFit integration. This replaces the former ``spectrafit plugins jupyter``
plugin path.
"""

from __future__ import annotations

import contextlib

from pathlib import Path
from typing import Annotated

import typer


def jupyter(
    notebook: Annotated[
        Path | None,
        typer.Argument(
            help=(
                "Notebook ``.ipynb`` file to open on launch. "
                "Auto-detected from ``spectrafit.toml`` when omitted."
            ),
        ),
    ] = None,
) -> None:
    """Launch Jupyter Lab for interactive SpectraFit analysis.

    Opens Jupyter Lab with SpectraFit integration for interactive
    data analysis, fitting, and visualization.

    When no notebook file is supplied the command looks for:

    1. The ``default_notebook`` path declared in ``spectrafit.toml``
       (if the file exists in the current directory).
    2. ``spectrafit_getting_started.ipynb`` in the current directory.

    Examples:
        ```bash
        spectrafit jupyter
        spectrafit jupyter spectrafit_getting_started.ipynb
        ```

    !!! note "Requirements"
        Requires the ``[jupyter]`` optional dependency group:
        ``pip install spectrafit[jupyter]``
    """
    resolved: Path | None = notebook

    # --- auto-detect notebook from spectrafit.toml or CWD ---
    if resolved is None:
        project_toml = Path("spectrafit.toml")
        if project_toml.exists():
            with contextlib.suppress(Exception):
                from spectrafit.models.project_config import ProjectConfig

                pc = ProjectConfig.from_toml(project_toml)
                candidate = Path(pc.project.files.default_notebook)
                if candidate.exists():
                    resolved = candidate

        if resolved is None:
            fallback = Path("spectrafit_getting_started.ipynb")
            if fallback.exists():
                resolved = fallback

    # --- validate before launching ---
    if resolved is not None and not resolved.exists():
        typer.echo(f"❌ Notebook not found: {resolved}", err=True)
        raise typer.Exit(1)

    try:
        from spectrafit.app.app import jupyter as jupyter_app

        if resolved is not None:
            typer.echo(f"📓 Opening notebook: {resolved}")
        typer.echo("🚀 Launching Jupyter Lab with SpectraFit integration...")
        typer.echo("   Press Ctrl+C to stop the server.\n")
        jupyter_app(notebook_file=resolved)

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

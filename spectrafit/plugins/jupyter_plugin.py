"""Jupyter Notebook plugin for SpectraFit.

This plugin provides Jupyter notebook integration and visualization capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import typer

from spectrafit.plugins.protocol import SpectraFitPlugin


if TYPE_CHECKING:
    pass


class JupyterPlugin:
    """Jupyter Notebook plugin.

    Provides interactive Jupyter notebook integration for SpectraFit,
    including data visualization, fitting, and result export.
    """

    name = "jupyter"
    version = "1.0.0"
    description = "Jupyter notebook integration for interactive fitting and visualization"

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register Jupyter-related commands with the parent Typer app.

        Args:
            parent_app: The parent Typer application to register commands with.
        """

        @parent_app.command(name="jupyter")
        def jupyter() -> None:
            """Launch Jupyter Lab for interactive SpectraFit analysis.

            Opens Jupyter Lab with SpectraFit integration for interactive
            data analysis, fitting, and visualization.
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
                typer.echo(f"❌ Unexpected error: {e}", err=True)
                raise typer.Exit(1) from e

    def register_models(self) -> list[type]:
        """Return list of Pydantic models this plugin provides.

        Returns:
            List of Jupyter-related Pydantic models.
        """
        try:
            # Import notebook-related models if available
            from spectrafit.plugins.notebook.core import SpectraFitNotebook

            # Return any Pydantic models used in the notebook interface
            return []
        except ImportError:
            return []


# Ensure this is recognized as a SpectraFitPlugin
assert isinstance(JupyterPlugin(), SpectraFitPlugin)

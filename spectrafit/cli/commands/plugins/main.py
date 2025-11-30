"""Main plugins command group for SpectraFit CLI."""

from __future__ import annotations

from typing import Annotated

import typer


# Create plugins Typer app
plugins_app = typer.Typer(
    help="SpectraFit plugins - Additional tools and visualizers.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


# Plugin metadata for discovery
AVAILABLE_PLUGINS: dict[str, dict[str, str]] = {
    "rixs": {
        "name": "RIXS Visualizer",
        "description": "Interactive RIXS plane viewer for 2D/3D visualization",
        "module": "spectrafit.cli.commands.plugins.rixs",
    },
}


@plugins_app.command(name="list")
def list_plugins(
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Show detailed plugin information.",
        ),
    ] = False,
) -> None:
    """List all available SpectraFit plugins."""
    typer.echo("\n📦 Available SpectraFit Plugins:\n")

    for plugin_id, info in AVAILABLE_PLUGINS.items():
        if verbose:
            typer.echo(f"  {plugin_id}:")
            typer.echo(f"    Name: {info['name']}")
            typer.echo(f"    Description: {info['description']}")
            typer.echo(f"    Module: {info['module']}")
            typer.echo()
        else:
            typer.echo(f"  • {plugin_id}: {info['name']}")

    if not verbose:
        typer.echo("\n  Use 'spectrafit plugins <plugin> --help' for plugin details.")
        typer.echo("  Use 'spectrafit plugins list -v' for verbose output.")


# Import and register RIXS plugin commands
# This is done lazily to avoid import errors if dependencies are missing
def _register_rixs_plugin() -> None:
    """Register RIXS visualizer plugin commands."""
    try:
        from spectrafit.cli.commands.plugins.rixs import rixs

        plugins_app.command(
            name="rixs",
            help="Launch the RIXS Visualizer for interactive 2D/3D visualization.",
        )(rixs)
    except ImportError as import_error:
        # Create a placeholder command that shows the import error
        error_msg = str(import_error)

        @plugins_app.command(name="rixs")
        def rixs_unavailable() -> None:
            """RIXS Visualizer (dependencies not installed)."""
            typer.echo(
                "❌ RIXS Visualizer is not available. "
                "Install required dependencies with:",
                err=True,
            )
            typer.echo("   pip install spectrafit[jupyter-dash]", err=True)
            typer.echo(f"\n   Error: {error_msg}", err=True)
            raise typer.Exit(1)


# Register plugins on import
_register_rixs_plugin()

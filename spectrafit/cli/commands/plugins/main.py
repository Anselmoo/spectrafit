"""Main plugins command group for SpectraFit CLI.

This module manages the plugin system and registers plugin commands.
"""

from __future__ import annotations

import logging

from typing import Annotated

import typer

from spectrafit.plugins import get_plugin_registry


logger = logging.getLogger(__name__)

# Create plugins Typer app
plugins_app = typer.Typer(
    help="SpectraFit plugins - Additional tools and visualizers.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


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
    registry = get_plugin_registry()

    typer.echo("\n📦 Available SpectraFit Plugins:\n")

    # List built-in plugins
    builtin_plugins = registry.list_available_builtins()
    for plugin_name in builtin_plugins:
        plugin = registry.load_builtin_plugin(plugin_name)
        if plugin:
            if verbose:
                typer.echo(f"  {plugin.name}:")
                typer.echo(f"    Version: {plugin.version}")
                typer.echo(f"    Description: {plugin.description}")
                typer.echo()
            else:
                typer.echo(f"  • {plugin.name}: {plugin.description}")

    # Discover and list external plugins
    for _discovered_count, plugin in enumerate(registry.discover_plugins(), start=1):
        if verbose:
            typer.echo(f"  {plugin.name} (external):")
            typer.echo(f"    Version: {plugin.version}")
            typer.echo(f"    Description: {plugin.description}")
            typer.echo()
        else:
            typer.echo(f"  • {plugin.name} (external): {plugin.description}")

    if not verbose:
        typer.echo("\n  Use 'spectrafit plugins <plugin> --help' for plugin details.")
        typer.echo("  Use 'spectrafit plugins list -v' for verbose output.")


def _register_builtin_plugins() -> None:
    """Register built-in plugin commands."""
    registry = get_plugin_registry()

    # Load and register built-in plugins
    for plugin_name in registry.list_available_builtins():
        try:
            plugin = registry.load_builtin_plugin(plugin_name)
            if plugin:
                plugin.register_commands(plugins_app)
                logger.info("Registered plugin: %s", plugin.name)
        except ImportError as e:
            logger.warning("Failed to load plugin %s: %s", plugin_name, e)
        except (TypeError, AttributeError):
            logger.exception("Error registering plugin %s", plugin_name)


# Register plugins on import
_register_builtin_plugins()

"""Main plugins command group for SpectraFit CLI.

This module exposes discovery helpers for external SpectraFit plugins.
"""

from __future__ import annotations

import logging

from typing import TYPE_CHECKING
from typing import Annotated
from typing import cast

import typer

from typer.core import TyperGroup

from spectrafit.plugins import get_plugin_registry


if TYPE_CHECKING:
    import click

    from spectrafit.plugins import PluginRegistry


logger = logging.getLogger(__name__)
_REGISTERED_PLUGIN_ATTR = "_spectrafit_registered_plugin_names"


class PluginCommandGroup(TyperGroup):
    """Typer group that discovers external plugin commands on first use."""

    def _ensure_plugin_commands_registered(self) -> None:
        register_discovered_plugin_commands(self)

    def get_command(
        self,
        ctx: click.Context,
        cmd_name: str,
    ) -> click.Command | None:
        """Load plugin commands before resolving a subcommand by name."""
        self._ensure_plugin_commands_registered()
        return super().get_command(ctx, cmd_name)

    def list_commands(self, ctx: click.Context) -> list[str]:
        """Load plugin commands before rendering the command list/help output."""
        self._ensure_plugin_commands_registered()
        return super().list_commands(ctx)


def _registered_plugin_names(parent_app: typer.Typer | click.Group) -> set[str]:
    """Return the per-app cache of plugin names already registered."""
    registered_plugins = getattr(parent_app, _REGISTERED_PLUGIN_ATTR, None)
    if registered_plugins is None:
        registered_plugins = set()
        setattr(parent_app, _REGISTERED_PLUGIN_ATTR, registered_plugins)
    return cast("set[str]", registered_plugins)


# Create plugins Typer app
plugins_app = typer.Typer(
    cls=PluginCommandGroup,
    help="SpectraFit plugins - Discover and inspect external plugins.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


def register_discovered_plugin_commands(
    parent_app: typer.Typer | click.Group,
    *,
    registry: PluginRegistry | None = None,
) -> None:
    """Register commands exposed by discovered plugins exactly once."""
    registered_plugins = _registered_plugin_names(parent_app)
    resolved_registry = get_plugin_registry() if registry is None else registry
    for plugin in resolved_registry.discover_plugins():
        if plugin.name in registered_plugins:
            continue
        plugin.register_commands(parent_app)
        registered_plugins.add(plugin.name)


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

    discovered_plugins = list(registry.discover_plugins())
    for plugin in discovered_plugins:
        if verbose:
            typer.echo(f"  {plugin.name} (external):")
            typer.echo(f"    Version: {plugin.version}")
            typer.echo(f"    Description: {plugin.description}")
            typer.echo()
        else:
            typer.echo(f"  • {plugin.name} (external): {plugin.description}")

    if not discovered_plugins:
        typer.echo("  No external plugins discovered.")

    if not verbose:
        typer.echo("\n  Use 'spectrafit plugins <plugin> --help' for plugin details.")
        typer.echo("  Use 'spectrafit plugins list -v' for verbose output.")

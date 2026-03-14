"""Main CLI entry point for SpectraFit."""

from __future__ import annotations

from typing import Annotated

import typer

from spectrafit.cli._callbacks import version_callback
from spectrafit.cli.commands.convert import convert
from spectrafit.cli.commands.examples import examples_app
from spectrafit.cli.commands.fit import fit
from spectrafit.cli.commands.jupyter import jupyter
from spectrafit.cli.commands.plugins import plugins_app
from spectrafit.cli.commands.report import report
from spectrafit.cli.commands.scaffolding import init
from spectrafit.cli.commands.scaffolding import new_config
from spectrafit.cli.commands.validate import validate
from spectrafit.cli.runtime import build_cli_runtime


_BANNER_COMMANDS: set[str] = {"fit", "init", "jupyter", "plugins"}


# Create main Typer app
app = typer.Typer(
    help="SpectraFit - Fast Fitting Program for ascii txt files.",
    epilog="For more information, visit https://anselmoo.github.io/spectrafit/",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich",
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
)


# Register version callback at app level
@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: Annotated[
        bool | None,
        typer.Option(
            "-v",
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Display the current version of SpectraFit.",
        ),
    ] = None,
) -> None:
    """Command line interface for spectral fitting.

    Use 'spectrafit <command> --help' for more information about a command.
    """
    from rich.console import Console  # noqa: PLC0415

    from spectrafit.cli.banner import render_startup_panel  # noqa: PLC0415
    from spectrafit.models.fitting_context import detect_environment  # noqa: PLC0415

    show_banner = (
        ctx.invoked_subcommand is None or ctx.invoked_subcommand in _BANNER_COMMANDS
    )
    ctx.obj = {"runtime": build_cli_runtime()}
    if show_banner:
        render_startup_panel(Console(), detect_environment())

    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())
        raise typer.Exit


# Register subcommands
app.command(name="fit", help="Fit spectra data using SpectraFit.")(fit)
app.add_typer(examples_app, name="examples", help="Inspect and run shipped examples.")
app.command(name="validate", help="Validate input configuration files.")(validate)
app.command(name="convert", help="Convert configuration files between formats.")(
    convert,
)
app.command(name="report", help="Generate reports from fitting results.")(report)
app.command(name="init", help="Scaffold a new fitting project.")(init)
app.command(name="new-config", help="Generate a configuration file.")(new_config)
app.command(
    name="jupyter",
    help="Launch Jupyter Lab for interactive SpectraFit analysis.",
)(jupyter)

# Register plugins subcommand group
app.add_typer(plugins_app, name="plugins", help="Additional tools and visualizers.")


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()

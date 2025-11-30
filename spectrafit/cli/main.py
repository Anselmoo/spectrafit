"""Main CLI entry point for SpectraFit."""

from __future__ import annotations

from typing import Annotated

import typer

from spectrafit.cli._callbacks import version_callback
from spectrafit.cli.commands.convert import convert
from spectrafit.cli.commands.fit import fit
from spectrafit.cli.commands.plugins import plugins_app
from spectrafit.cli.commands.report import report
from spectrafit.cli.commands.validate import validate


# Create main Typer app
app = typer.Typer(
    help="SpectraFit - Fast Fitting Program for ascii txt files.",
    epilog="For more information, visit https://anselmoo.github.io/spectrafit/",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


# Register version callback at app level
@app.callback()
def main(
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


# Register subcommands
app.command(name="fit", help="Fit spectra data using SpectraFit.")(fit)
app.command(name="validate", help="Validate input configuration files.")(validate)
app.command(name="convert", help="Convert configuration files between formats.")(
    convert
)
app.command(name="report", help="Generate reports from fitting results.")(report)

# Register plugins subcommand group
app.add_typer(plugins_app, name="plugins", help="Additional tools and visualizers.")


def run() -> None:
    """Run the CLI application."""
    app()


if __name__ == "__main__":
    run()

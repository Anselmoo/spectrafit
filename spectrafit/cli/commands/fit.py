"""Fit command for SpectraFit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.core import SaveResult
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.models.output_config import OutputConfig
from spectrafit.plotting import PlotSpectra
from spectrafit.report import PrintingStatus


__status__ = PrintingStatus()


def fit(
    config: Annotated[
        Path,
        typer.Argument(
            help=(
                "Path to the fitting configuration file. "
                "Supported formats: [bold]*.toml[/bold], [bold]*.json[/bold], "
                "[bold]*.yml[/bold], [bold]*.yaml[/bold]."
            ),
        ),
    ],
    outfile: Annotated[
        str,
        typer.Option(
            "-o",
            "--outfile",
            help="Filename prefix for exported results; default [bold]spectrafit_results[/bold].",
        ),
    ] = "spectrafit_results",
    noplot: Annotated[
        bool,
        typer.Option(
            "-np",
            "--noplot",
            help="Suppress plotting of the spectra and fit.",
        ),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "-vb",
            "--verbose",
            min=0,
            max=2,
            help=(
                "Verbosity level: [bold]0[/bold]=silent, "
                "[bold]1[/bold]=table (default), [bold]2[/bold]=dict."
            ),
        ),
    ] = 1,
) -> None:
    """Fit spectra data using SpectraFit.

    All fitting parameters (data path, preprocessing, peak components) are
    defined in the configuration file.  The CLI only controls output behaviour.

    [bold]Examples:[/bold]

        $ spectrafit fit fitting_input.toml

        $ spectrafit fit my_xps.toml --outfile xps_results --verbose 2
    """
    from rich.console import Console
    from rich.status import Status

    console = Console()

    while True:
        __status__.start()

        try:
            cfg = UnifiedFittingConfig.from_file(config)
        except Exception as exc:
            typer.echo(
                typer.style(f"Configuration error: {exc}", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(code=1) from exc

        output = OutputConfig(outfile=outfile, noplot=noplot, verbose=verbose)

        try:
            with Status(
                f"[bold cyan]Fitting[/bold cyan] [green]{config.name}[/green] …",
                console=console,
                spinner="dots",
            ):
                df_result, result_args = fitting_routine_pipeline(
                    args=cfg, output=output
                )
        except Exception as exc:
            typer.echo(
                typer.style(f"Fitting error: {exc}", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(code=1) from exc

        console.print(
            f"[bold green]✓[/bold green] Fit complete: [cyan]{config.name}[/cyan]"
        )

        PlotSpectra(df=df_result, args=result_args)()
        SaveResult(df=df_result, args=result_args)()

        __status__.end()

        if noplot:
            return

        from spectrafit.cli._types import reset_keyboard_protocol

        reset_keyboard_protocol()
        if not typer.confirm("Would you like to fit again?", default=False):
            return

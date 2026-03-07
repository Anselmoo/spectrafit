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
                "Supported formats: '*.toml', '*.json', '*.yml', '*.yaml'."
            )
        ),
    ],
    outfile: Annotated[
        str,
        typer.Option(
            "-o",
            "--outfile",
            help="Filename prefix for exported results; default 'spectrafit_results'.",
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
            help=("Verbosity level: 0=silent, 1=table (default), 2=dict."),
        ),
    ] = 1,
) -> None:
    """Fit spectra data using SpectraFit.

    All fitting parameters (data path, preprocessing, peak components) are
    defined in the configuration file.  The CLI only controls output behaviour.

    Examples:
        $ spectrafit fit fitting_input.toml
        $ spectrafit fit my_xps.toml --outfile xps_results --verbose 2
    """
    __status__.welcome()

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
            df_result, result_args = fitting_routine_pipeline(args=cfg, output=output)
        except Exception as exc:
            typer.echo(
                typer.style(f"Fitting error: {exc}", fg=typer.colors.RED),
                err=True,
            )
            raise typer.Exit(code=1) from exc

        PlotSpectra(df=df_result, args=result_args)()
        SaveResult(df=df_result, args=result_args)()

        __status__.end()

        from spectrafit.cli._types import reset_keyboard_protocol

        reset_keyboard_protocol()
        if not typer.confirm("Would you like to fit again?", default=False):
            __status__.thanks()
            __status__.credits()
            return

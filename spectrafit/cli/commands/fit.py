"""Fit command for SpectraFit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.core import SaveResult
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.output_config import OutputConfig
from spectrafit.models.plot_config import PlotConfig
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
    import re
    import warnings

    from rich.console import Console
    from rich.panel import Panel
    from rich.status import Status
    from rich.text import Text

    console = Console()
    _original_showwarning = warnings.showwarning

    def _rich_showwarning(
        message: warnings.WarningMessage | Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: object = None,
        line: str | None = None,
    ) -> None:
        # Strip the legacy ASCII-art borders produced by report/metrics.py warn_meassage()
        raw = str(message)
        cleaned = re.sub(r"^[#\s]+$", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"^##\s*WARNING\s*#+", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()
        console.print(
            Panel(
                Text(cleaned, style="yellow"),
                title=f"[bold yellow]⚠  {category.__name__}[/bold yellow]",
                title_align="left",
                border_style="yellow",
                expand=False,
                padding=(0, 1),
            )
        )

    warnings.showwarning = _rich_showwarning  # type: ignore[invalid-assignment]

    while True:
        __status__.start()

        try:
            cfg = UnifiedFittingConfig.from_file(config)
        except Exception as exc:
            console.print(
                Panel(
                    Text(str(exc), style="red"),
                    title="[bold red]✗  Configuration error[/bold red]",
                    title_align="left",
                    border_style="red",
                    expand=False,
                    padding=(0, 1),
                )
            )
            raise typer.Exit(code=1) from exc

        output = OutputConfig(outfile=outfile, noplot=noplot, verbose=verbose)

        try:
            with Status(
                f"[bold cyan]Fitting[/bold cyan] [green]{config.name}[/green] …",
                console=console,
                spinner="dots",
            ):
                fit_result = fitting_routine_pipeline(args=cfg, output=output)
        except Exception as exc:
            console.print(
                Panel(
                    Text(str(exc), style="red"),
                    title="[bold red]✗  Fitting error[/bold red]",
                    title_align="left",
                    border_style="red",
                    expand=False,
                    padding=(0, 1),
                )
            )
            raise typer.Exit(code=1) from exc

        console.print(
            f"[bold green]✓[/bold green] Fit complete: [cyan]{config.name}[/cyan]"
        )

        PlotSpectra(
            df=fit_result.df,
            config=PlotConfig(
                noplot=noplot,
                global_fitting=(
                    FittingMode.GLOBAL
                    if fit_result.config.context.is_global
                    else FittingMode.STANDARD
                ),
                data_statistic=fit_result.data_statistic,
            ),
        )()
        SaveResult(
            df=fit_result.df,
            post=fit_result.post,
            outfile=outfile,
        )()

        __status__.end()

        if noplot:
            warnings.showwarning = _original_showwarning
            return

        from spectrafit.cli._types import reset_keyboard_protocol

        reset_keyboard_protocol()
        if not typer.confirm("Would you like to fit again?", default=False):
            warnings.showwarning = _original_showwarning
            return

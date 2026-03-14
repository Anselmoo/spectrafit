"""Fit command for SpectraFit CLI."""

from __future__ import annotations

import re
import warnings

from pathlib import Path
from typing import Annotated

import typer

from rich.console import Console
from rich.panel import Panel
from rich.status import Status
from rich.text import Text

from spectrafit.cli.runtime import get_cli_runtime
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.core.result_bridge import write_cli_outputs
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.output_config import OutputConfig
from spectrafit.models.plot_config import PlotConfig
from spectrafit.plotting import PlotSpectra


def _clean_warning_message(message: warnings.WarningMessage | Warning | str) -> str:
    """Normalize legacy warning text before rendering."""
    cleaned = re.sub(r"^[#\s]+$", "", str(message), flags=re.MULTILINE)
    cleaned = re.sub(r"^##\s*WARNING\s*#+", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()


def _render_warning_panel(
    console: Console,
    message: warnings.WarningMessage | Warning | str,
    category: type[Warning],
) -> None:
    """Render CLI warnings using a Rich panel."""
    console.print(
        Panel(
            Text(_clean_warning_message(message), style="yellow"),
            title=f"[bold yellow]⚠  {category.__name__}[/bold yellow]",
            title_align="left",
            border_style="yellow",
            expand=False,
            padding=(0, 1),
        )
    )


def _install_warning_renderer(console: Console) -> object:
    """Install the Rich warning renderer and return the previous hook."""
    original_showwarning = warnings.showwarning

    def _rich_showwarning(
        message: warnings.WarningMessage | Warning | str,
        category: type[Warning],
        filename: str,
        lineno: int,
        file: object = None,
        line: str | None = None,
    ) -> None:
        _render_warning_panel(console, message, category)

    warnings.showwarning = _rich_showwarning  # type: ignore[invalid-assignment]
    return original_showwarning


def _render_error_panel(console: Console, title: str, exc: Exception) -> None:
    """Render a CLI error as a Rich panel."""
    console.print(
        Panel(
            Text(str(exc), style="red"),
            title=title,
            title_align="left",
            border_style="red",
            expand=False,
            padding=(0, 1),
        )
    )


def _resolve_runtime_config(
    runtime: object,
    console: Console,
    config: Path | None,
) -> tuple[Path, object]:
    """Resolve and load the requested fitting config."""
    try:
        resolved_config = runtime.resolve_config_path(config)
        return resolved_config, runtime.load_fitting_config(resolved_config)
    except Exception as exc:
        _render_error_panel(console, "[bold red]✗  Configuration error[/bold red]", exc)
        raise typer.Exit(code=1) from exc


def _run_fitting_pipeline(
    console: Console,
    resolved_config: Path,
    cfg: object,
    output: OutputConfig,
) -> object:
    """Execute the fitting pipeline under the Rich status spinner."""
    try:
        with Status(
            f"[bold cyan]Fitting[/bold cyan] [green]{resolved_config.name}[/green] …",
            console=console,
            spinner="dots",
        ):
            return fitting_routine_pipeline(
                request=FittingRequest.from_config(cfg, output=output),
            )
    except Exception as exc:
        _render_error_panel(console, "[bold red]✗  Fitting error[/bold red]", exc)
        raise typer.Exit(code=1) from exc


def _plot_fit_result(fit_result: object, noplot: bool) -> None:
    """Plot the fit result using a PlotConfig derived from fit context."""
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


def _write_fit_outputs(fit_result: object, outfile: str) -> None:
    """Write fit outputs for the CLI."""
    write_cli_outputs(
        fit_result=fit_result.fit_result,
        fit_df=fit_result.df,
        outfile=outfile,
    )


def _run_fit_iteration(
    runtime: object,
    console: Console,
    config: Path | None,
    outfile: str,
    noplot: bool,
    verbose: int,
) -> None:
    """Execute one complete fit iteration."""
    runtime.status_printer.start()
    resolved_config, cfg = _resolve_runtime_config(runtime, console, config)
    output = OutputConfig(outfile=outfile, noplot=noplot, verbose=verbose)
    fit_result = _run_fitting_pipeline(console, resolved_config, cfg, output)

    console.print(
        f"[bold green]✓[/bold green] Fit complete: [cyan]{resolved_config.name}[/cyan]"
    )
    _plot_fit_result(fit_result, noplot)
    _write_fit_outputs(fit_result, outfile)
    runtime.status_printer.end()


def _should_repeat_fit(*, noplot: bool, interactive: bool) -> bool:
    """Return whether the CLI should prompt to run the fit again."""
    if noplot or not interactive:
        return False

    from spectrafit.cli._types import reset_keyboard_protocol

    reset_keyboard_protocol()
    return typer.confirm("Would you like to fit again?", default=False)


def fit(
    ctx: typer.Context,
    config: Annotated[
        Path | None,
        typer.Argument(
            help=(
                "Path to the fitting configuration file. When omitted, SpectraFit "
                "uses SPECTRAFIT_CONFIG or the default config stored under "
                "typer.get_app_dir('spectrafit'). "
                "Supported formats: [bold]*.toml[/bold], [bold]*.json[/bold], "
                "[bold]*.yml[/bold], [bold]*.yaml[/bold]."
            ),
        ),
    ] = None,
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
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive/--no-interactive",
            help=(
                "Prompt to fit again after completion. Disabled by default for "
                "non-interactive CLI use."
            ),
        ),
    ] = False,
) -> None:
    """Fit spectra data using SpectraFit.

    All fitting parameters (data path, preprocessing, peak components) are
    defined in the configuration file.  The CLI only controls output behaviour.

    [bold]Examples:[/bold]

        $ spectrafit fit fitting_input.toml

        $ spectrafit fit my_xps.toml --outfile xps_results --verbose 2
    """
    console = Console()
    _original_showwarning = _install_warning_renderer(console)
    runtime = get_cli_runtime(ctx)

    try:
        while True:
            _run_fit_iteration(
                runtime=runtime,
                console=console,
                config=config,
                outfile=outfile,
                noplot=noplot,
                verbose=verbose,
            )
            if not _should_repeat_fit(noplot=noplot, interactive=interactive):
                return
    finally:
        warnings.showwarning = _original_showwarning

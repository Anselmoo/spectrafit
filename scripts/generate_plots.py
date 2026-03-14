"""Generate fit-validation HTML plots for every SpectraFit example.

For each ``examples/*/input.toml`` the script runs ``FittingPipeline``,
builds a shared Plotly fit figure, and writes
``examples/<name>/fit_validation.html``.

Usage::

    uv run python scripts/generate_plots.py
    uv run python scripts/generate_plots.py --show  # open interactive figure after saving
"""

from __future__ import annotations

from pathlib import Path

import typer

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.plot_config import PlotConfig
from spectrafit.plotting import PlotSpectra


_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLES_DIR = _REPO_ROOT / "examples"
_GREEN = "\033[92m"
_RED = "\033[91m"
_RESET = "\033[0m"

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


def _load_config(input_toml: Path) -> UnifiedFittingConfig:
    """Load a config and resolve its data path to the local example CSV."""
    return UnifiedFittingConfig.from_file(input_toml).with_data_infile(
        (input_toml.parent / "data.csv").resolve()
    )


def _plot_example(input_toml: Path, *, show: bool) -> Path:
    """Run the pipeline for one example and save a validation HTML plot."""
    example_name = input_toml.parent.name
    config = _load_config(input_toml)
    fit = FittingPipeline(request=FittingRequest.from_config(config)).run()

    if not fit.success:
        msg = f"Fit did not converge for '{example_name}': {fit.result.message}"
        raise RuntimeError(msg)

    plotter = PlotSpectra(
        df=fit.df,
        config=PlotConfig(
            noplot=True,
            global_fitting=config.context.mode,
            data_statistic=fit.data_statistic,
        ),
    )
    out_path = input_toml.parent / "fit_validation.html"
    plotter.write_html(out_path)
    if show:
        plotter.figure().show()
    return out_path


@app.command()
def main(
    show: bool = typer.Option(
        False,
        "--show",
        help="Open an interactive Plotly figure for each example after saving.",
    ),
) -> None:
    """Generate fit-validation Plotly HTML artifacts for all examples."""
    input_tomls = sorted(_EXAMPLES_DIR.glob("*/input.toml"))

    if not input_tomls:
        typer.echo(f"{_RED}✗ No input.toml files found under {_EXAMPLES_DIR}{_RESET}")
        raise typer.Exit(code=1)

    errors: list[tuple[str, str]] = []
    for input_toml in input_tomls:
        example_name = input_toml.parent.name
        try:
            out_path = _plot_example(input_toml, show=show)
            size_kb = out_path.stat().st_size // 1024
            typer.echo(f"{_GREEN}✓{_RESET}  {example_name}  →  {out_path}  ({size_kb} KB)")
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"{_RED}✗  {example_name}: {exc}{_RESET}", err=True)
            errors.append((example_name, str(exc)))

    if errors:
        typer.echo(f"\n{_RED}{len(errors)} example(s) failed.{_RESET}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

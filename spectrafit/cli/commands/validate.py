"""Validate command for SpectraFit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.core.fitting_config import UnifiedFittingConfig


def validate(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the input configuration file to validate.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    verbose: Annotated[
        bool,
        typer.Option(
            "-v",
            "--verbose",
            help="Show detailed validation results.",
        ),
    ] = False,
) -> None:
    """Validate a SpectraFit input configuration file.

    Parses the file with :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`
    and reports any validation errors. Accepts only v2
    (``[data]``/``[[components]]``) format.
    """
    try:
        cfg = UnifiedFittingConfig.from_file(input_file)
        component_count = len(cfg.components)
        typer.echo(typer.style(f"\n✅ '{input_file}' is valid.", fg=typer.colors.GREEN))
        if verbose:
            typer.echo(f"   📊 Components: {component_count}")
            if cfg.data:
                typer.echo(f"   📂 Data file : {cfg.data.infile}")
            if cfg.preprocessing:
                typer.echo(
                    f"   ⚙️  Energy range: "
                    f"{cfg.preprocessing.energy_start} - {cfg.preprocessing.energy_stop}",
                )
    except OSError as e:
        typer.echo(
            typer.style(f"\n❌ Cannot read file: {e}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(
            typer.style(f"\n❌ Validation error: {e}", fg=typer.colors.RED),
            err=True,
        )
        raise typer.Exit(1) from e

"""Validate command for SpectraFit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.cli.runtime import get_cli_runtime
from spectrafit.core.data_loader import load_data
from spectrafit.models.data_config import DataConfig


class ValidationRuntimeError(ValueError):
    """Base class for runtime validation errors."""


class DataFileValidationError(ValidationRuntimeError):
    """Raised when the referenced data file cannot be used."""


class DataColumnsValidationError(ValidationRuntimeError):
    """Raised when configured columns are not available in the data file."""


def _validate_referenced_input_data(cfg: object) -> None:
    """Validate that the configured input data file can be loaded as configured."""
    data_config = getattr(cfg, "data", None)
    if data_config is None:
        msg = "Configuration is missing the required [data] section."
        raise ValidationRuntimeError(msg)

    resolved_data_config = DataConfig.from_unified(cfg)
    data_path = resolved_data_config.infile
    if not data_path.is_file():
        msg = f"Data file not found: '{data_path}'"
        raise DataFileValidationError(msg)

    try:
        df = load_data(resolved_data_config)
    except OSError as exc:
        msg = f"Could not read data file '{data_path}': {exc}"
        raise DataFileValidationError(msg) from exc
    except ValueError as exc:
        expected_columns = [resolved_data_config.x_col, resolved_data_config.y_col]
        if "Usecols do not match columns" in str(exc):
            msg = (
                f"Configured columns are not available in '{data_path}': "
                f"{expected_columns}"
            )
            raise DataColumnsValidationError(msg) from exc
        msg = f"Could not load data file '{data_path}': {exc}"
        raise DataFileValidationError(msg) from exc

    available_columns = {str(column) for column in df.columns}
    required_columns = {resolved_data_config.x_col}
    if not resolved_data_config.context.is_global:
        required_columns.add(resolved_data_config.y_col)
    missing_columns = sorted(required_columns - available_columns)
    if missing_columns:
        msg = (
            f"Configured columns are not available in '{data_path}': {missing_columns}"
        )
        raise DataColumnsValidationError(msg)


def validate(
    ctx: typer.Context,
    input_file: Annotated[
        Path | None,
        typer.Argument(
            help="Path to the input configuration file to validate.",
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
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
    runtime = get_cli_runtime(ctx)
    try:
        resolved_input = runtime.resolve_config_path(input_file)
        cfg = runtime.load_fitting_config(resolved_input)
        _validate_referenced_input_data(cfg)
        component_count = len(cfg.components)
        typer.echo(
            typer.style(
                f"\n✅ '{resolved_input}' is valid.",
                fg=typer.colors.GREEN,
            )
        )
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

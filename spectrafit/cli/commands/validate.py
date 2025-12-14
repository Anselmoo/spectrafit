"""Validate command for SpectraFit CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit.core import read_input_file


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

    This command checks if the input file is valid JSON, YAML, or TOML
    and contains the required structure for SpectraFit fitting.
    """
    try:
        config = read_input_file(input_file)

        # Check required sections
        errors: list[str] = []
        warnings: list[str] = []

        if "fitting" not in config:
            errors.append("Missing required section: 'fitting'")
        else:
            fitting = config["fitting"]

            if "parameters" not in fitting:
                errors.append("Missing required section: 'fitting.parameters'")
            else:
                params = fitting["parameters"]
                if "minimizer" not in params:
                    errors.append(
                        "Missing required key: 'fitting.parameters.minimizer'"
                    )
                if "optimizer" not in params:
                    errors.append(
                        "Missing required key: 'fitting.parameters.optimizer'"
                    )

            if "peaks" not in fitting:
                warnings.append("No peaks defined in 'fitting.peaks'")

            if "description" not in fitting and verbose:
                warnings.append("Optional 'fitting.description' section not found")

        if "settings" in config and verbose:
            settings = config["settings"]
            typer.echo("\n📋 Settings found:")
            for key, value in settings.items():
                typer.echo(f"   {key}: {value}")

        # Report results
        if errors:
            typer.echo("\n❌ Validation failed with errors:", err=True)
            for error in errors:
                typer.echo(f"   • {error}", err=True)
            raise typer.Exit(1)

        if warnings and verbose:
            typer.echo("\n⚠️  Warnings:")
            for warning in warnings:
                typer.echo(f"   • {warning}")

        typer.echo(f"\n✅ Input file '{input_file}' is valid!")

        if verbose and "fitting" in config:
            fitting = config["fitting"]
            if "peaks" in fitting:
                peak_count = len(fitting["peaks"])
                typer.echo(f"   📊 Found {peak_count} peak(s) defined")
            if "parameters" in fitting:
                params = fitting["parameters"]
                if "minimizer" in params:
                    typer.echo(f"   🔧 Minimizer: {params['minimizer']}")
                if "optimizer" in params:
                    method = params["optimizer"].get("method", "not specified")
                    typer.echo(f"   ⚙️  Optimizer method: {method}")

    except OSError as e:
        typer.echo(f"❌ Error reading file: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"❌ Validation error: {e}", err=True)
        raise typer.Exit(1) from e

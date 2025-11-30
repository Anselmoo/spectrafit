"""Convert command for SpectraFit CLI."""

from __future__ import annotations

import json

from pathlib import Path
from typing import Annotated
from typing import Any

import tomli
import typer
import yaml

from spectrafit.cli._types import OutputFormatEnum


def convert(
    input_file: Annotated[
        Path,
        typer.Argument(
            help="Path to the input configuration file to convert.",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ],
    output_format: Annotated[
        OutputFormatEnum,
        typer.Option(
            "-f",
            "--format",
            help="Output format (json, yaml, or toml).",
        ),
    ] = OutputFormatEnum.TOML,
    output_file: Annotated[
        Path | None,
        typer.Option(
            "-o",
            "--output",
            help="Output file path. If not specified, uses input filename with new extension.",
        ),
    ] = None,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Overwrite output file if it exists.",
        ),
    ] = False,
) -> None:
    """Convert input configuration files between JSON, YAML, and TOML formats.

    This command allows you to convert SpectraFit configuration files between
    different formats while preserving the structure and content.

    Examples:
        spectrafit convert input.json --format yaml
        spectrafit convert config.toml -f json -o output.json
    """
    try:
        # Read input file
        config = _read_config(input_file)

        # Determine output filename
        if output_file is None:
            output_file = input_file.with_suffix(f".{output_format.value}")

        # Check if output file exists
        if output_file.exists() and not force:
            typer.echo(
                f"❌ Output file '{output_file}' already exists. Use --force to overwrite.",
                err=True,
            )
            raise typer.Exit(1)

        # Check if input and output are the same
        if input_file.resolve() == output_file.resolve():
            typer.echo(
                "❌ Input and output files cannot be the same.",
                err=True,
            )
            raise typer.Exit(1)

        # Write output file
        _write_config(config, output_file, output_format)

        typer.echo(f"✅ Successfully converted '{input_file}' → '{output_file}'")
        typer.echo(
            f"   Format: {input_file.suffix[1:].upper()} → {output_format.value.upper()}"
        )

    except OSError as e:
        typer.echo(f"❌ File error: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"❌ Conversion error: {e}", err=True)
        raise typer.Exit(1) from e


def _read_config(filepath: Path) -> dict[str, Any]:
    """Read configuration from file.

    Args:
        filepath: Path to the configuration file.

    Returns:
        Configuration dictionary.

    Raises:
        OSError: If file format is not supported.
    """
    suffix = filepath.suffix.lower()

    if suffix == ".json":
        with filepath.open(encoding="utf-8") as f:
            return json.load(f)
    elif suffix == ".toml":
        with filepath.open("rb") as f:
            return tomli.load(f)
    elif suffix in {".yaml", ".yml"}:
        with filepath.open(encoding="utf-8") as f:
            return yaml.safe_load(f)
    else:
        msg = f"Unsupported input format: {suffix}. Use .json, .yaml, .yml, or .toml"
        raise OSError(msg)


def _write_config(
    config: dict[str, Any], filepath: Path, fmt: OutputFormatEnum
) -> None:
    """Write configuration to file.

    Args:
        config: Configuration dictionary.
        filepath: Output file path.
        fmt: Output format.
    """
    if fmt == OutputFormatEnum.JSON:
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    elif fmt == OutputFormatEnum.YAML:
        with filepath.open("w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    elif fmt == OutputFormatEnum.TOML:
        # Use tomli_w for writing TOML if available, otherwise use toml
        try:
            import tomli_w

            with filepath.open("wb") as f:
                tomli_w.dump(config, f)
        except ImportError:
            # Fallback: write as formatted string
            with filepath.open("w", encoding="utf-8") as f:
                f.write(_dict_to_toml(config))


def _dict_to_toml(data: dict[str, Any], prefix: str = "") -> str:
    """Convert dictionary to TOML string (simple implementation).

    Args:
        data: Dictionary to convert.
        prefix: Key prefix for nested tables.

    Returns:
        TOML formatted string.
    """
    lines: list[str] = []
    tables: list[tuple[str, dict[str, Any]]] = []

    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, dict):
            tables.append((full_key, value))
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                # Array of tables
                for item in value:
                    lines.append(f"\n[[{full_key}]]")
                    lines.append(_dict_to_toml(item))
            else:
                lines.append(f"{key} = {_format_toml_value(value)}")
        else:
            lines.append(f"{key} = {_format_toml_value(value)}")

    for table_key, table_value in tables:
        lines.append(f"\n[{table_key}]")
        lines.append(_dict_to_toml(table_value))

    return "\n".join(lines)


def _format_toml_value(value: Any) -> str:
    """Format a value for TOML output.

    Args:
        value: Value to format.

    Returns:
        TOML formatted string representation.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return f'"{value}"'
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        items = ", ".join(_format_toml_value(v) for v in value)
        return f"[{items}]"
    if value is None:
        return '""'
    return str(value)

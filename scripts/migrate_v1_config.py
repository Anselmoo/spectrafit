"""Convert legacy SpectraFit v1 config payloads into canonical v2 configs."""

from __future__ import annotations

import json

from pathlib import Path  # noqa: TC003
from typing import Annotated

import tomli_w
import typer
import yaml

from spectrafit.adapters.v1_config_migration import migrate_v1_payload
from spectrafit.core.config_loader import load_config_payload
from spectrafit.core.fitting_config import UnifiedFittingConfig


app = typer.Typer(help="Migrate legacy SpectraFit v1 configs to canonical v2 format.")


def _write_output(payload: dict[str, object], output_path: Path, fmt: str) -> None:
    """Write a migrated config payload to disk."""
    if fmt == "json":
        output_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")
        return
    if fmt == "yaml":
        output_path.write_text(
            yaml.safe_dump(payload, sort_keys=False),
            encoding="utf-8",
        )
        return
    if fmt == "toml":
        output_path.write_text(tomli_w.dumps(payload), encoding="utf-8")
        return
    msg = f"Unsupported output format: {fmt}"
    raise ValueError(msg)


@app.command()
def main(
    input_file: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    output_file: Annotated[Path, typer.Option("--output", "-o")],
    format_: Annotated[
        str,
        typer.Option("--format", "-f", help="Output format: toml, json, or yaml."),
    ] = "toml",
) -> None:
    """Read a legacy v1 config and emit a validated v2 config file."""
    raw_payload = load_config_payload(input_file)
    migrated_payload = migrate_v1_payload(raw_payload)
    validated = UnifiedFittingConfig.model_validate(migrated_payload)
    payload = validated.model_dump(mode="json", exclude_none=True)
    _write_output(payload, output_file, format_)
    typer.echo(f"✅ Migrated '{input_file}' → '{output_file}' ({format_})")


if __name__ == "__main__":
    app()

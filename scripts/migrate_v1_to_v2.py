#!/usr/bin/env python
"""Migrate a SpectraFit v1.x input file to v2 ``[[components]]`` TOML format.

Usage::

    uv run python scripts/migrate_v1_to_v2.py old_input.json -o new_input.toml
    uv run python scripts/migrate_v1_to_v2.py old_input.toml -o new_input.toml

The script reads any v1.x TOML or JSON file (both nested-wrapper patterns are
supported), normalises the structure via :func:`spectrafit.models.migration.migrate_v1_format`,
converts the legacy ``peaks`` dict to a v2 ``[[components]]`` array, and writes a clean
v2-compatible TOML file.

!!! note "What changes"
    - ``{"fitting": {"peaks": {...}}}`` / ``{"parameters": {...}, "peaks": {...}}``
      wrappers are unwrapped.
    - ``peaks["1"]["gaussian"] = {"amplitude": {...}}`` notation is converted to::

        [[components]]
        id    = "p1"
        model = "gaussian"
        [components.parameters]
        amplitude = { value = 1.0, bounds = [0.0, 3.0], vary = true }

    - Flat data / preprocessing keys (``infile``, ``energy_start``, …) are
      wrapped into ``[data]`` / ``[preprocessing]`` sub-tables.
    - ``minimizer`` / ``optimizer`` dicts are preserved as-is (v2 still reads them).

!!! note "What does NOT change"
    - The ``infile`` path is preserved verbatim — update it manually if needed.
    - No physical data files are moved or copied.
    - The ``[[components]]`` parameter dicts use the same keys as v1 (``value``,
      ``min``, ``max``, ``vary``, ``expr``) — ``bounds`` consolidation is optional
      (supported by v2 but not mandatory).
"""

from __future__ import annotations

import json

from pathlib import Path

import tomli
import tomli_w
import typer

from spectrafit.models.migration import migrate_v1_format


app = typer.Typer(
    name="migrate-v1",
    help="Migrate a SpectraFit v1.x input file to v2 TOML format.",
    no_args_is_help=True,
)


# ---------------------------------------------------------------------------
# Conversion helpers (pure functions, no spectrafit pipeline imports)
# ---------------------------------------------------------------------------


def _read_input(path: Path) -> dict[str, object]:
    """Read a JSON or TOML input file.

    Args:
        path: Path to the v1 input file (.json or .toml).

    Returns:
        dict: Parsed raw dict.

    Raises:
        typer.Exit: If the format is unsupported or the file cannot be read.
    """
    if path.suffix == ".json":
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            typer.echo(typer.style(f"✗ JSON parse error: {exc}", fg=typer.colors.RED))
            raise typer.Exit(1) from exc
    if path.suffix in (".toml",):
        try:
            with path.open("rb") as fh:
                return tomli.load(fh)
        except tomli.TOMLDecodeError as exc:
            typer.echo(typer.style(f"✗ TOML parse error: {exc}", fg=typer.colors.RED))
            raise typer.Exit(1) from exc
    typer.echo(
        typer.style(
            f"✗ Unsupported file format '{path.suffix}'. "
            "Use .json or .toml input.",
            fg=typer.colors.RED,
        )
    )
    raise typer.Exit(1)


def _convert_param_spec(spec: dict[str, object]) -> dict[str, object]:
    """Convert a v1 parameter dict to compact v2 inline-table form.

    v1 uses separate ``min`` and ``max`` keys; v2 prefers ``bounds = [min, max]``.
    Both forms are valid in v2, so we consolidate into ``bounds`` only when both
    ``min`` and ``max`` are present.

    Args:
        spec: v1 parameter dict (may contain ``min``, ``max``, ``value``, ``vary``,
            ``expr``).

    Returns:
        dict: v2-compatible parameter dict.
    """
    result = dict(spec)
    if "min" in result and "max" in result:
        min_val = result.pop("min")
        max_val = result.pop("max")
        result["bounds"] = [min_val, max_val]
    return result


def _peaks_to_components(peaks: dict[str, object]) -> list[dict[str, object]]:
    """Convert the v1 ``peaks`` dict to a list of v2 component dicts.

    v1 structure::

        peaks:
          "1":
            gaussian:
              amplitude: {value: 1.0, min: 0.0, max: 3.0, vary: true}
              center:    {value: -0.5, ...}

    v2 structure (list of dicts, becomes ``[[components]]`` in TOML)::

        [{"id": "p1", "model": "gaussian",
          "parameters": {"amplitude": {value: 1.0, bounds: [0.0, 3.0], vary: true}}}]

    Args:
        peaks: v1 peaks dict keyed by peak index (str or int).

    Returns:
        list: Ordered list of v2 component dicts.
    """
    components: list[dict[str, object]] = []
    for peak_key, model_spec in peaks.items():
        # Normalise numeric string keys: "1" → "p1", "bg" stays "bg"
        raw_id = str(peak_key)
        component_id = f"p{raw_id}" if raw_id.isdigit() else raw_id

        if not isinstance(model_spec, dict):
            continue
        for model_name, param_spec in model_spec.items():
            if not isinstance(param_spec, dict):
                continue
            converted_params = {
                field: _convert_param_spec(pdict)
                if isinstance(pdict, dict)
                else pdict
                for field, pdict in param_spec.items()
            }
            components.append(
                {
                    "id": component_id,
                    "model": model_name,
                    "parameters": converted_params,
                }
            )
    return components


def _build_v2_dict(migrated: dict[str, object]) -> dict[str, object]:
    """Build the final v2 output dict from a normalised v1 dict.

    Args:
        migrated: Dict produced by :func:`~spectrafit.models.migration.migrate_v1_format`.

    Returns:
        dict: v2-compatible dict ready for ``tomli_w.dumps()``.
    """
    result: dict[str, object] = {
        "schema_version": "2.0",
        "config_type": "peak_fit",
    }

    # Forward [data] and [preprocessing] sub-dicts as-is
    for section in ("data", "preprocessing"):
        if section in migrated and isinstance(migrated[section], dict):
            result[section] = migrated[section]

    # Forward minimizer / optimizer at root (v2 still supports these)
    for key in ("minimizer", "optimizer", "conf_interval", "global_"):
        if key in migrated:
            result[key] = migrated[key]

    # Convert peaks → [[components]]
    peaks = migrated.get("peaks")
    if isinstance(peaks, dict) and peaks:
        result["components"] = _peaks_to_components(peaks)

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


@app.command()
def migrate(
    infile: Path = typer.Argument(  # noqa: B008
        ...,
        help="v1.x input file (.json or .toml)",
        exists=True,
        file_okay=True,
        readable=True,
    ),
    outfile: Path = typer.Option(  # noqa: B008
        None,
        "--output",
        "-o",
        help="Output .toml path.  Defaults to <infile stem>_v2.toml in the same directory.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print the output TOML to stdout without writing a file.",
    ),
) -> None:
    """Migrate a SpectraFit v1.x input file to v2 ``[[components]]`` TOML format."""
    # Resolve default output path
    if outfile is None:
        outfile = infile.parent / f"{infile.stem}_v2.toml"

    typer.echo(f"Reading  : {infile}")

    raw = _read_input(infile)

    # --- Step 1: normalise v1 wrapper patterns ---
    migrated = migrate_v1_format(raw)

    # --- Step 2: convert to v2 output dict ---
    v2_dict = _build_v2_dict(migrated)

    # --- Step 3: serialise to TOML ---
    try:
        toml_bytes = tomli_w.dumps(v2_dict)
    except Exception as exc:
        typer.echo(typer.style(f"✗ TOML serialisation failed: {exc}", fg=typer.colors.RED))
        raise typer.Exit(1) from exc

    if dry_run:
        typer.echo("\n" + toml_bytes)
        return

    outfile.write_text(toml_bytes, encoding="utf-8")
    typer.echo(
        typer.style(f"✓ Written : {outfile}", fg=typer.colors.GREEN)
    )
    typer.echo(
        typer.style(
            "\nNext step: validate with\n"
            f'  uv run python -c "'
            f"from spectrafit.core.fitting_config import UnifiedFittingConfig; "
            f"print(UnifiedFittingConfig.from_file('{outfile}'))\"",
            fg=typer.colors.BRIGHT_BLACK,
        )
    )


if __name__ == "__main__":
    app()

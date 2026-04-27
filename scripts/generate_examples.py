"""Generate committed example artifacts from shared synthetic scenarios."""

from __future__ import annotations

import json

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from typing import cast

import typer

from spectrafit.generators.scenarios import iter_example_scenarios
from spectrafit.jupyter.templates.starter_nb import write_example_notebook


app = typer.Typer(
    help="Generate shared SpectraFit example artifacts.", no_args_is_help=False
)

_REPO_ROOT = Path(__file__).parent.parent


def _normalized_cell_source(source: object) -> str:
    """Return stable cell source text across string/list notebook serializations."""
    if isinstance(source, str):
        return source.rstrip("\n")
    return "".join(
        line if line.endswith("\n") else f"{line}\n"
        for line in cast("list[str]", source)
    ).rstrip("\n")


def _normalized_notebook(path: Path) -> dict[str, object]:
    """Return a semantic notebook view stable across editor serializations."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    cells = raw.get("cells", [])
    if not isinstance(cells, list):
        msg = f"Notebook at {path} does not contain a valid cell list."
        raise TypeError(msg)

    normalized_cells: list[dict[str, object]] = []
    for cell in cells:
        if not isinstance(cell, dict):
            msg = f"Notebook at {path} contains a non-object cell."
            raise TypeError(msg)

        source = cell.get("source", "")
        normalized_cell: dict[str, object] = {
            "cell_type": cell.get("cell_type"),
            "source": _normalized_cell_source(source),
        }
        normalized_cells.append(normalized_cell)

    return {"cells": normalized_cells}


def _materialize_examples(*, root: Path, seed: int) -> tuple[str, ...]:
    """Write the generated example artifacts beneath ``root/examples``."""
    labels: list[str] = []
    for scenario in iter_example_scenarios():
        if scenario.example_dir is None:
            continue

        scenario.write_example_artifacts(root=root / "examples", seed=seed)
        write_example_notebook(
            example_name=scenario.example_dir,
            description=scenario.description,
            output_path=root / "examples" / scenario.example_dir / "notebook.ipynb",
        )
        labels.append(
            ", ".join(
                (
                    f"{scenario.example_dir}/data.csv",
                    f"{scenario.example_dir}/input.toml",
                    f"{scenario.example_dir}/notebook.ipynb",
                )
            )
        )

    return tuple(labels)


def _stale_example_artifacts(
    *, actual_root: Path, expected_root: Path
) -> tuple[str, ...]:
    """Return relative example artifact paths that are missing or stale."""
    stale: list[str] = []

    for scenario in iter_example_scenarios():
        if scenario.example_dir is None:
            continue

        for relative_path in (
            Path(scenario.example_dir) / "data.csv",
            Path(scenario.example_dir) / "input.toml",
            Path(scenario.example_dir) / "notebook.ipynb",
        ):
            actual_path = actual_root / "examples" / relative_path
            expected_path = expected_root / "examples" / relative_path

            if not actual_path.exists():
                stale.append(f"{relative_path.as_posix()} (missing)")
                continue
            if relative_path.suffix == ".ipynb":
                is_stale = _normalized_notebook(actual_path) != _normalized_notebook(
                    expected_path
                )
            else:
                is_stale = actual_path.read_bytes() != expected_path.read_bytes()
            if is_stale:
                stale.append(f"{relative_path.as_posix()} (stale)")

    return tuple(stale)


def _check_examples(*, seed: int) -> None:
    """Verify that committed example artifacts match the generator output."""
    with TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        _materialize_examples(root=tmp_root, seed=seed)
        stale = _stale_example_artifacts(actual_root=_REPO_ROOT, expected_root=tmp_root)

    if stale:
        typer.secho(
            "Committed example artifacts are stale:", fg=typer.colors.RED, err=True
        )
        for relative_path in stale:
            typer.echo(f"- {relative_path}", err=True)
        typer.echo(
            "Run `uv run poe generate-examples` to refresh committed artifacts.",
            err=True,
        )
        raise typer.Exit(code=1)

    typer.secho(
        "✓  Committed example artifacts are up to date.",
        fg=typer.colors.GREEN,
    )


@app.command()
def main(
    seed: Annotated[
        int, typer.Option("--seed", help="Random seed for reproducibility.")
    ] = 42,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Verify committed examples are up to date without rewriting files.",
        ),
    ] = False,
) -> None:
    """Write committed example artifacts for all example directories.

    Args:
        seed: Integer seed passed to ``numpy.random.default_rng``.
        check: When True, verify committed files instead of rewriting them.
    """
    if check:
        _check_examples(seed=seed)
        return

    for label in _materialize_examples(root=_REPO_ROOT, seed=seed):
        typer.echo(
            typer.style(
                f"✓  Materialized: {label}",
                fg=typer.colors.GREEN,
            )
        )


if __name__ == "__main__":
    app()

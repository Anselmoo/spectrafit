"""Generate committed example artifacts from shared synthetic scenarios."""

from __future__ import annotations

from pathlib import Path

import typer

from spectrafit.generators.scenarios import iter_example_scenarios
from spectrafit.jupyter.templates.starter_nb import write_example_notebook


app = typer.Typer(help="Generate shared SpectraFit example artifacts.", no_args_is_help=False)

_REPO_ROOT = Path(__file__).parent.parent


@app.command()
def main(
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
) -> None:
    """Write committed example artifacts for all example directories.

    Args:
        seed: Integer seed passed to ``numpy.random.default_rng``.
    """
    for scenario in iter_example_scenarios():
        if scenario.example_dir is None:
            continue

        scenario.write_example_artifacts(root=_REPO_ROOT / "examples", seed=seed)
        write_example_notebook(
            example_name=scenario.example_dir,
            description=scenario.description,
            output_path=_REPO_ROOT / "examples" / scenario.example_dir / "notebook.ipynb",
        )
        label = (
            f"{scenario.example_dir}/data.csv, "
            f"{scenario.example_dir}/input.toml, "
            f"{scenario.example_dir}/notebook.ipynb"
        )
        typer.echo(
            typer.style(
                f"✓  Materialized: {label}",
                fg=typer.colors.GREEN,
            )
        )


if __name__ == "__main__":
    app()

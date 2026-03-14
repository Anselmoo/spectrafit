"""Example external SpectraFit plugin."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from spectrafit_example_plugin.materializer import materialize_notebook_from_config


class ExamplePlugin:
    """Minimal plugin implementation for third-party extension packages."""

    name = "example"
    version = "0.1.0"
    description = "Example plugin template for external SpectraFit extensions"

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register example plugin commands."""

        @parent_app.command(name="example-materialize-notebook")
        def example_materialize_notebook(
            config_path: Annotated[
                Path,
                typer.Argument(
                    help="Path to the input TOML/JSON/YAML config to convert.",
                    exists=True,
                    dir_okay=False,
                    readable=True,
                    resolve_path=True,
                ),
            ],
            output_path: Annotated[
                Path,
                typer.Option(
                    "--output",
                    "-o",
                    help="Destination path for the generated notebook.",
                    dir_okay=False,
                    resolve_path=True,
                ),
            ] = Path("materialized_notebook.ipynb"),
            artifact_name: Annotated[
                str | None,
                typer.Option(
                    "--artifact-name",
                    help="Basename used for live notebook export artifacts.",
                ),
            ] = None,
            data_path: Annotated[
                str | None,
                typer.Option(
                    "--data-path",
                    help="Local CSV path the notebook should load at runtime.",
                ),
            ] = None,
            title: Annotated[
                str | None,
                typer.Option(
                    "--title",
                    help="Optional notebook title override.",
                ),
            ] = None,
            description: Annotated[
                str | None,
                typer.Option(
                    "--description",
                    help="Optional intro text shown at the top of the notebook.",
                ),
            ] = None,
        ) -> None:
            """Convert an input config file into an editable SpectraFit notebook."""
            notebook_path = materialize_notebook_from_config(
                config_path=config_path,
                output_path=output_path,
                artifact_name=artifact_name,
                data_path=data_path,
                title=title,
                description=description,
            )
            typer.echo(f"Materialized editable notebook at {notebook_path}")

    def register_models(self) -> list[type]:
        """Return plugin-owned Pydantic model types."""
        return []

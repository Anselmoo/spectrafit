"""Example discovery and execution commands for shipped SpectraFit workflows."""

from __future__ import annotations

from typing import Annotated

import typer

from spectrafit.workflow.validation import EXAMPLE_INPUTS
from spectrafit.workflow.validation import ExampleWorkflowSurface
from spectrafit.workflow.validation import run_example_workflows


examples_app = typer.Typer(
    help="Inspect and run the shipped SpectraFit examples.",
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)


@examples_app.command(name="list")
def list_examples() -> None:
    """List the example workflows bundled with SpectraFit."""
    if not EXAMPLE_INPUTS:
        typer.echo("No shipped examples found.")
        return

    for input_toml in EXAMPLE_INPUTS:
        typer.echo(input_toml.parent.name)


@examples_app.command(name="run")
def run_examples(
    example_name: Annotated[
        str | None,
        typer.Argument(
            help="Optional example name. Omit to run all shipped examples.",
        ),
    ] = None,
    surface: Annotated[
        ExampleWorkflowSurface,
        typer.Option(
            "--surface",
            help="Which workflow surface to run.",
        ),
    ] = ExampleWorkflowSurface.BOTH,
) -> None:
    """Run shipped example workflows through CLI, notebook, or both surfaces."""
    try:
        run_example_workflows(
            example_name=example_name,
            surface=surface,
        )
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc

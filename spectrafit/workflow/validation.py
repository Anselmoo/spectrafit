"""Live validation and example workflow runtime.

Provides reusable functions for executing example workflows through
the CLI and notebook surfaces, including config resolution, workspace
preparation, and validation of outputs.
"""

from __future__ import annotations

import contextlib
import json
import shutil

from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.models.plot_config import PlotConfig
from spectrafit.plotting import PlotSpectra


if TYPE_CHECKING:
    from collections.abc import Callable

    from typer.testing import CliRunner


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = REPO_ROOT / "examples"
EXAMPLE_INPUTS = sorted(EXAMPLES_DIR.glob("*/input.toml"))
LIVE_OUTPUTS_DIR = "outputs"
LIVE_WORKFLOW_DIR = "live"
CLI_WORKFLOW_DIR = "cli"
NOTEBOOK_WORKFLOW_DIR = "notebook"


class ExampleWorkflowSurface(StrEnum):
    """Workflow surfaces supported by shipped SpectraFit examples."""

    CLI = "cli"
    NOTEBOOK = "notebook"
    BOTH = "both"


def resolved_config(input_toml: Path) -> UnifiedFittingConfig:
    """Load an example config and resolve its data file canonically.

    Args:
        input_toml: Path to the example's input.toml file.

    Returns:
        UnifiedFittingConfig with resolved data file path.
    """
    data_csv = (input_toml.parent / "data.csv").resolve()
    return UnifiedFittingConfig.from_file(input_toml).with_data_infile(data_csv)


def prepare_live_workspace(*, input_toml: Path, surface: str) -> Path:
    """Create a deterministic, clean output workspace under the example directory.

    Creates a workspace within the example directory's persistent outputs tree,
    removing any stale files from previous runs.

    Args:
        input_toml: Path to the example's input.toml file.
        surface: The workflow surface name (e.g., 'cli', 'notebook').

    Returns:
        Path to the prepared workspace directory.
    """
    workspace = input_toml.parent / LIVE_OUTPUTS_DIR / LIVE_WORKFLOW_DIR / surface
    shutil.rmtree(workspace, ignore_errors=True)
    workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def run_cli_example(*, runner: CliRunner, input_toml: Path, workspace: Path) -> None:
    """Execute one example through the public CLI surface.

    Validates that the CLI produces required output artifacts (fit CSV and
    summary JSON) and generates an HTML visualization of the fit.

    Args:
        runner: Typer CliRunner instance.
        input_toml: Path to the example's input.toml file.
        workspace: Working directory for outputs.

    Raises:
        RuntimeError: If the CLI invocation fails or outputs are missing.
    """
    from spectrafit.cli.main import app  # noqa: PLC0415

    config = resolved_config(input_toml)
    config_path = workspace / "input.resolved.json"
    config_path.write_text(
        json.dumps(config.model_dump(mode="json", exclude_none=True), indent=2),
        encoding="utf-8",
    )

    with contextlib.chdir(workspace):
        result = runner.invoke(
            app,
            [
                "fit",
                str(config_path),
                "--noplot",
                "--outfile",
                input_toml.parent.name,
            ],
        )

    if result.exit_code != 0:
        msg = f"CLI live run failed for '{input_toml.parent.name}':\n{result.output}"
        raise RuntimeError(msg)

    if not list(workspace.glob("*_fit.csv")):
        msg = f"CLI live run did not export a fit CSV for '{input_toml.parent.name}'."
        raise RuntimeError(msg)
    if not list(workspace.glob("*_summary.json")):
        msg = f"CLI live run did not export a summary JSON for '{input_toml.parent.name}'."
        raise RuntimeError(msg)
    fit_csv = workspace / f"{input_toml.parent.name}_fit.csv"
    PlotSpectra(
        df=pd.read_csv(fit_csv),
        config=PlotConfig(
            noplot=True,
            global_fitting=config.context.mode,
        ),
    ).write_html(workspace / f"{input_toml.parent.name}_fit.html")


def run_notebook_example(*, input_toml: Path, workspace: Path) -> None:
    """Execute one example through the notebook surface and export artifacts.

    Validates that the notebook produces required output artifacts
    (fit CSV, metric CSV, peaks CSV, HTML plot, and lock file).

    Args:
        input_toml: Path to the example's input.toml file.
        workspace: Working directory for outputs.

    Raises:
        RuntimeError: If the notebook execution fails or outputs are missing.
    """
    config = resolved_config(input_toml)
    if config.data is None:
        msg = f"Example '{input_toml.parent.name}' is missing a [data] block."
        raise RuntimeError(msg)
    data_csv = Path(str(config.data.infile))
    notebook = SpectraFitNotebook.from_config(
        df=pd.read_csv(data_csv),
        config=config,
        fname=input_toml.parent.name,
        folder=str(workspace),
    )
    notebook.solver_model(
        notebook.initial_components,
        show_plot=False,
        show_metric=False,
        config=config,
    )
    notebook.export_fit_dataframe()
    notebook.export_metric_df()
    notebook.export_peaks_df()
    notebook.export_fit_plot_html()
    notebook.generate_fit_report()

    expected_patterns = (
        "fit_*.csv",
        "fit_*.html",
        "metric_*.csv",
        "peaks_*.csv",
        "*.lock",
    )
    for pattern in expected_patterns:
        if list(workspace.glob(pattern)):
            continue
        msg = (
            f"Notebook live run did not export '{pattern}' for "
            f"'{input_toml.parent.name}'."
        )
        raise RuntimeError(msg)


def selected_example_inputs(example_name: str | None = None) -> tuple[Path, ...]:
    """Return example input configs filtered by optional example name."""
    if example_name is None:
        return tuple(EXAMPLE_INPUTS)

    matches = tuple(
        input_toml
        for input_toml in EXAMPLE_INPUTS
        if input_toml.parent.name == example_name
    )
    if matches:
        return matches

    msg = (
        f"Unknown example '{example_name}'. "
        f"Available: {', '.join(input_toml.parent.name for input_toml in EXAMPLE_INPUTS)}"
    )
    raise ValueError(msg)


def run_example_workflows(
    *,
    example_name: str | None = None,
    surface: ExampleWorkflowSurface = ExampleWorkflowSurface.BOTH,
    runner: CliRunner | None = None,
    echo: Callable[[str], None] | None = None,
) -> tuple[Path, ...]:
    """Run shipped example workflows through the requested public surfaces."""
    from typer import echo as typer_echo  # noqa: PLC0415
    from typer.testing import CliRunner  # noqa: PLC0415

    input_tomls = selected_example_inputs(example_name)
    if not input_tomls:
        msg = f"No example configs found under '{EXAMPLES_DIR}'."
        raise RuntimeError(msg)

    resolved_runner = CliRunner() if runner is None else runner
    emit = typer_echo if echo is None else echo

    for input_toml in input_tomls:
        example_dir = input_toml.parent
        if surface in (ExampleWorkflowSurface.CLI, ExampleWorkflowSurface.BOTH):
            cli_workspace = prepare_live_workspace(
                input_toml=input_toml,
                surface=CLI_WORKFLOW_DIR,
            )
            emit(f"[live] CLI: {example_dir.name} -> {cli_workspace}")
            run_cli_example(
                runner=resolved_runner,
                input_toml=input_toml,
                workspace=cli_workspace,
            )

        if surface in (ExampleWorkflowSurface.NOTEBOOK, ExampleWorkflowSurface.BOTH):
            notebook_workspace = prepare_live_workspace(
                input_toml=input_toml,
                surface=NOTEBOOK_WORKFLOW_DIR,
            )
            emit(f"[live] Notebook: {example_dir.name} -> {notebook_workspace}")
            run_notebook_example(
                input_toml=input_toml,
                workspace=notebook_workspace,
            )

    return input_tomls

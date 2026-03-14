"""Integration smoke tests for examples/*/input.toml via FittingPipeline."""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
import warnings

from pathlib import Path

import pandas as pd
import pytest

from spectrafit.cli.main import app
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.jupyter.templates.starter_nb import build_example_notebook
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.workflow.validation import CLI_WORKFLOW_DIR
from spectrafit.workflow.validation import EXAMPLE_INPUTS
from spectrafit.workflow.validation import LIVE_OUTPUTS_DIR
from spectrafit.workflow.validation import LIVE_WORKFLOW_DIR
from spectrafit.workflow.validation import ExampleWorkflowSurface
from spectrafit.workflow.validation import prepare_live_workspace
from spectrafit.workflow.validation import run_cli_example
from spectrafit.workflow.validation import run_example_workflows
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_committed_example_notebook_matches_generator(input_toml: Path) -> None:
    """Committed example notebooks must stay aligned with the typed generator contract."""
    example_name = input_toml.parent.name
    scenario = get_synthetic_scenario(example_name)
    committed_notebook = json.loads(
        (input_toml.parent / "notebook.ipynb").read_text(encoding="utf-8")
    )

    assert committed_notebook == build_example_notebook(
        example_name=example_name,
        description=scenario.description,
    ), f"Committed notebook for {example_name} is stale. Run `uv run poe generate-examples`."


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_notebook_config_roundtrip_prefers_typed_component_state(
    input_toml: Path,
) -> None:
    """Notebook config ETL should keep typed components canonical for examples."""
    data_csv = input_toml.parent / "data.csv"
    raw = UnifiedFittingConfig.from_file(input_toml).model_dump(
        mode="json",
        exclude_none=True,
    )
    data_section = dict(raw["data"])
    data_section["infile"] = str(data_csv.resolve())
    raw["data"] = data_section
    config = UnifiedFittingConfig.model_validate(raw)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        notebook = SpectraFitNotebook.from_config(
            df=pd.read_csv(data_csv),
            config=config,
        )
        roundtrip = notebook.args_to_config()

    initial_model_warnings = [
        warning
        for warning in caught
        if issubclass(warning.category, FutureWarning)
        and "SpectraFitNotebook.initial_model" in str(warning.message)
    ]

    assert not initial_model_warnings
    assert roundtrip.components == config.components
    assert notebook.initial_components == config.components


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_loads_and_converges(input_toml: Path, tmp_path: Path) -> None:
    """Each example must load, fit, and converge with residuals < 0.1 RMS."""
    data_csv = input_toml.parent / "data.csv"
    assert data_csv.exists(), f"Missing data.csv for {input_toml.parent.name}"

    df = pd.read_csv(data_csv)
    assert df.shape[1] == 2, f"Expected 2 columns, got {df.shape[1]}"

    # Load config and override infile to the absolute path so the pipeline can
    # resolve the data file regardless of the working directory.
    raw = UnifiedFittingConfig.from_file(input_toml).model_dump()
    raw["data"]["infile"] = str(data_csv.resolve())
    cfg = UnifiedFittingConfig.model_validate(raw)
    assert len(cfg.components) >= 1

    fit = FittingPipeline(request=FittingRequest.from_config(cfg)).run()

    assert fit.success, (
        f"Fit did not converge for {input_toml.parent.name}: {fit.result.message}"
    )

    y_col = df.columns[1]
    # The pipeline stores the best-fit values in fit.df["fit"]
    residuals = fit.df["fit"].to_numpy() - fit.df[y_col].to_numpy()
    rms = math.sqrt(float((residuals**2).mean()))
    assert rms < 0.1, (
        f"RMS residual {rms:.4f} >= 0.1 for {input_toml.parent.name} — fit quality too poor"
    )


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_cli_fit_writes_outputs(
    input_toml: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Each committed example should run through the CLI and write artifacts."""
    data_csv = input_toml.parent / "data.csv"
    raw = UnifiedFittingConfig.from_file(input_toml).model_dump(
        mode="json",
        exclude_none=True,
    )
    data_section = dict(raw["data"])
    data_section["infile"] = str(data_csv.resolve())
    raw["data"] = data_section

    config_path = tmp_path / f"{input_toml.parent.name}.json"
    config_path.write_text(json.dumps(raw), encoding="utf-8")

    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["fit", str(config_path), "--noplot"])

    assert result.exit_code == 0, result.output
    assert list(tmp_path.glob("*_fit.csv")), "Fit command did not write a fit CSV"
    assert list(tmp_path.glob("*_summary.json")), "Fit command did not write a summary JSON"


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_live_cli_fit_writes_visual_artifact(
    input_toml: Path,
    tmp_path: Path,
) -> None:
    """Each example live CLI workflow should write a deterministic HTML fit artifact."""
    working_example_dir = tmp_path / input_toml.parent.name
    shutil.copytree(input_toml.parent, working_example_dir)
    workspace = working_example_dir / "outputs" / "live" / "cli"
    workspace.mkdir(parents=True, exist_ok=True)

    run_cli_example(
        runner=runner,
        input_toml=working_example_dir / "input.toml",
        workspace=workspace,
    )

    assert (workspace / f"{working_example_dir.name}_fit.html").exists(), (
        "Live CLI workflow did not export an HTML fit artifact"
    )


@pytest.mark.integration
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_notebook_fit_writes_outputs(input_toml: Path, tmp_path: Path) -> None:
    """Each committed example should run through notebook mode and export artifacts."""
    data_csv = input_toml.parent / "data.csv"
    raw = UnifiedFittingConfig.from_file(input_toml).model_dump(
        mode="json",
        exclude_none=True,
    )
    data_section = dict(raw["data"])
    data_section["infile"] = str(data_csv.resolve())
    raw["data"] = data_section
    config = UnifiedFittingConfig.model_validate(raw)

    notebook = SpectraFitNotebook.from_config(
        df=pd.read_csv(data_csv),
        config=config,
        fname=input_toml.parent.name,
        folder=str(tmp_path),
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

    assert notebook.fit_result.fit_insights.variables
    assert list(tmp_path.glob("fit_*.csv")), "Notebook flow did not export a fit CSV"
    assert list(tmp_path.glob("metric_*.csv")), "Notebook flow did not export a metric CSV"
    assert list(tmp_path.glob("peaks_*.csv")), "Notebook flow did not export a peaks CSV"
    assert list(tmp_path.glob("fit_*.html")), "Notebook flow did not export an HTML fit plot"
    assert list(tmp_path.glob("*.lock")), "Notebook flow did not export a report lockfile"


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.parametrize("input_toml", EXAMPLE_INPUTS, ids=lambda p: p.parent.name)
def test_example_notebook_executes_headlessly(
    input_toml: Path,
    tmp_path: Path,
) -> None:
    """Each committed example notebook should execute from its local example root."""
    pytest.importorskip("nbconvert")

    source_example_dir = input_toml.parent
    working_example_dir = tmp_path / source_example_dir.name
    shutil.copytree(source_example_dir, working_example_dir)

    notebook_path = working_example_dir / "notebook.ipynb"
    assert notebook_path.exists(), f"Missing notebook.ipynb for {source_example_dir.name}"

    shutil.rmtree(working_example_dir / "outputs" / "live" / "notebook", ignore_errors=True)

    exec_result = subprocess.run(  # noqa: S603 - fixed interpreter/module invocation
        [
            sys.executable,
            "-m",
            "jupyter",
            "nbconvert",
            "--to",
            "notebook",
            "--execute",
            "--inplace",
            str(notebook_path),
        ],
        capture_output=True,
        check=False,
        cwd=working_example_dir,
        text=True,
        timeout=180,
    )

    assert exec_result.returncode == 0, (
        f"Committed notebook failed for {source_example_dir.name}.\n"
        f"STDOUT:\n{exec_result.stdout}\n"
        f"STDERR:\n{exec_result.stderr}"
    )

    executed_nb = json.loads(notebook_path.read_text(encoding="utf-8"))
    code_cells = [
        cell for cell in executed_nb["cells"] if cell.get("cell_type") == "code"
    ]
    assert code_cells, "Expected committed notebook to contain code cells"

    for index, cell in enumerate(code_cells):
        assert cell["execution_count"] is not None, (
            f"Code cell {index} was not executed "
            f"(execution_count is {cell['execution_count']!r})"
        )
        assert all(
            output.get("output_type") != "error" for output in cell.get("outputs", [])
        ), f"Code cell {index} produced an error output"

    output_dir = working_example_dir / "outputs" / "live" / "notebook"
    assert list(output_dir.glob("fit_*.csv")), "Headless notebook run did not export a fit CSV"
    assert list(output_dir.glob("metric_*.csv")), (
        "Headless notebook run did not export a metric CSV"
    )
    assert list(output_dir.glob("peaks_*.csv")), (
        "Headless notebook run did not export a peaks CSV"
    )
    assert list(output_dir.glob("fit_*.html")), (
        "Headless notebook run did not export an HTML fit plot"
    )
    assert list(output_dir.glob("*.lock")), "Headless notebook run did not export a lockfile"


@pytest.mark.integration
def test_prepare_live_workspace_resets_example_local_outputs(tmp_path: Path) -> None:
    """Live workspaces should be recreated inside each example's persistent outputs tree."""
    input_toml = tmp_path / "demo" / "input.toml"
    input_toml.parent.mkdir(parents=True)
    input_toml.write_text('schema_version = "2.0"\n', encoding="utf-8")

    stale_file = (
        input_toml.parent
        / LIVE_OUTPUTS_DIR
        / LIVE_WORKFLOW_DIR
        / CLI_WORKFLOW_DIR
        / "stale.txt"
    )
    stale_file.parent.mkdir(parents=True)
    stale_file.write_text("old run", encoding="utf-8")

    workspace = prepare_live_workspace(
        input_toml=input_toml,
        surface=CLI_WORKFLOW_DIR,
    )

    assert workspace == input_toml.parent / "outputs" / "live" / "cli"
    assert workspace.is_dir()
    assert not stale_file.exists()


@pytest.mark.integration
def test_run_example_workflows_persists_outputs_under_example_directories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The live workflow should write inspectable artifacts beneath each example."""
    examples_dir = tmp_path / "examples"
    example_dir = examples_dir / "demo"
    example_dir.mkdir(parents=True)
    input_toml = example_dir / "input.toml"
    input_toml.write_text('schema_version = "2.0"\n', encoding="utf-8")

    stale_cli_file = example_dir / "outputs" / "live" / "cli" / "obsolete.txt"
    stale_cli_file.parent.mkdir(parents=True)
    stale_cli_file.write_text("remove me", encoding="utf-8")

    def _fake_cli(*, runner: CliRunner, input_toml: Path, workspace: Path) -> None:
        assert isinstance(runner, CliRunner)
        assert input_toml == example_dir / "input.toml"
        assert workspace == example_dir / "outputs" / "live" / "cli"
        assert workspace.is_dir()
        assert not stale_cli_file.exists()
        (workspace / "input.resolved.json").write_text("{}", encoding="utf-8")
        (workspace / "demo_fit.csv").write_text("fit", encoding="utf-8")
        (workspace / "demo_fit.html").write_text("<html></html>", encoding="utf-8")
        (workspace / "demo_summary.json").write_text("{}", encoding="utf-8")

    def _fake_notebook(*, input_toml: Path, workspace: Path) -> None:
        assert input_toml == example_dir / "input.toml"
        assert workspace == example_dir / "outputs" / "live" / "notebook"
        assert workspace.is_dir()
        (workspace / "fit_demo.csv").write_text("fit", encoding="utf-8")
        (workspace / "fit_demo.html").write_text("<html></html>", encoding="utf-8")
        (workspace / "metric_demo.csv").write_text("metric", encoding="utf-8")
        (workspace / "peaks_demo.csv").write_text("peaks", encoding="utf-8")
        (workspace / "demo.lock").write_text("", encoding="utf-8")

    monkeypatch.setattr("spectrafit.workflow.validation.EXAMPLE_INPUTS", [input_toml])
    monkeypatch.setattr("spectrafit.workflow.validation.run_cli_example", _fake_cli)
    monkeypatch.setattr("spectrafit.workflow.validation.run_notebook_example", _fake_notebook)

    run_example_workflows(
        surface=ExampleWorkflowSurface.BOTH,
        echo=lambda _message: None,
    )

    assert (example_dir / "outputs" / "live" / "cli" / "input.resolved.json").exists()
    assert (example_dir / "outputs" / "live" / "cli" / "demo_fit.csv").exists()
    assert (example_dir / "outputs" / "live" / "cli" / "demo_fit.html").exists()
    assert (example_dir / "outputs" / "live" / "cli" / "demo_summary.json").exists()
    assert (example_dir / "outputs" / "live" / "notebook" / "fit_demo.csv").exists()
    assert (example_dir / "outputs" / "live" / "notebook" / "fit_demo.html").exists()
    assert (example_dir / "outputs" / "live" / "notebook" / "metric_demo.csv").exists()
    assert (example_dir / "outputs" / "live" / "notebook" / "peaks_demo.csv").exists()
    assert (example_dir / "outputs" / "live" / "notebook" / "demo.lock").exists()

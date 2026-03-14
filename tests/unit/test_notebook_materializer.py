"""Unit tests for notebook materialization helpers."""

from __future__ import annotations

import json
import sys

from pathlib import Path

import pytest
import typer

from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.jupyter import materialize_notebook_from_config
from spectrafit.jupyter.templates.materialized_nb import build_materialized_config_model
from spectrafit.jupyter.templates.materialized_nb import build_materialized_notebook
from typer.testing import CliRunner


runner = CliRunner()
REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_TEMPLATE_SRC = REPO_ROOT / "examples" / "plugin_template" / "src"


@pytest.mark.unit
def test_build_materialized_config_model_uses_requested_local_data_path() -> None:
    config = get_synthetic_scenario("basic").to_config()

    typed_config = build_materialized_config_model(config, data_path="local-data.csv")

    assert str(typed_config.data.infile) == "local-data.csv"
    assert typed_config.components[0].id == "peak1"


@pytest.mark.unit
def test_build_materialized_notebook_uses_simplified_notebook_api() -> None:
    config = get_synthetic_scenario("basic").to_config()

    notebook = build_materialized_notebook(
        project_name="basic",
        intro_title="basic — demo",
        intro_body="Notebook body",
        artifact_name="basic",
        config=config,
        data_path="data.csv",
    )
    code_text = "\n".join(
        cell["source"]
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code" and isinstance(cell.get("source"), str)
    )

    assert "import spectrafit.notebook as sf" in code_text
    assert "df = sf.read(DATA_PATH" in code_text
    assert "sf.peak(" in code_text
    assert "sf.background(" in code_text
    assert "result = sf.fit(" in code_text
    assert "artifacts = result.save(OUTPUT_DIR" in code_text
    assert "FitParameter(" not in code_text
    assert "Component(" not in code_text
    assert "DataConfig(" not in code_text
    assert "UnifiedFittingConfig(" not in code_text
    assert "SpectraFitNotebook.from_config" not in code_text
    assert "load_data(config.data)" not in code_text
    assert "config = config.with_data_infile(" not in code_text
    assert "notebook." not in code_text
    assert "DATA_PATH = NOTEBOOK_ROOT / 'data.csv'" in code_text
    assert "{{" not in code_text


@pytest.mark.unit
def test_build_materialized_notebook_restores_dot_notation_ties() -> None:
    config = get_synthetic_scenario("two-peak-constrained").to_config()

    notebook = build_materialized_notebook(
        project_name="two-peak-constrained",
        intro_title="two-peak-constrained — demo",
        intro_body="Notebook body",
        artifact_name="two-peak-constrained",
        config=config,
        data_path="data.csv",
    )
    code_text = "\n".join(
        cell["source"]
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code" and isinstance(cell.get("source"), str)
    )

    assert "sf.tie('p1.center + 1.0')" in code_text
    assert "sf.tie('p2.fwhmg')" in code_text
    assert "sf.tie('p1_center + 1.0')" not in code_text
    assert "sf.tie('p2_fwhmg')" not in code_text


@pytest.mark.unit
def test_core_materializer_writes_notebook_from_input_config(tmp_path: Path) -> None:
    scenario = get_synthetic_scenario("basic")
    config_path = tmp_path / "input.toml"
    output_path = tmp_path / "materialized.ipynb"
    config_path.write_text(scenario.example_input_toml(), encoding="utf-8")

    written_path = materialize_notebook_from_config(
        config_path=config_path,
        output_path=output_path,
        artifact_name="core-demo",
    )

    assert written_path == output_path
    notebook = json.loads(output_path.read_text(encoding="utf-8"))
    code_text = "\n".join(
        cell["source"]
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code" and isinstance(cell.get("source"), str)
    )
    assert "import spectrafit.notebook as sf" in code_text
    assert "df = sf.read(DATA_PATH" in code_text
    assert "result = sf.fit(" in code_text
    assert "artifacts = result.save(OUTPUT_DIR, name='core-demo')" in code_text
    assert "FitParameter(" not in code_text
    assert "Component(" not in code_text
    assert "UnifiedFittingConfig(" not in code_text
    assert "SpectraFitNotebook.from_config" not in code_text
    assert "load_data(config.data)" not in code_text
    assert "config_payload = {" not in code_text
    assert "UnifiedFittingConfig.from_file(" not in code_text


@pytest.mark.unit
def test_example_plugin_materializes_notebook_from_input_config(tmp_path: Path) -> None:
    sys.path.insert(0, str(PLUGIN_TEMPLATE_SRC))
    try:
        from spectrafit_example_plugin.plugin import ExamplePlugin
    finally:
        sys.path.pop(0)

    scenario = get_synthetic_scenario("basic")
    config_path = tmp_path / "input.toml"
    output_path = tmp_path / "materialized.ipynb"
    config_path.write_text(scenario.example_input_toml(), encoding="utf-8")

    app = typer.Typer()
    ExamplePlugin().register_commands(app)

    result = runner.invoke(
        app,
        [
            str(config_path),
            "--output",
            str(output_path),
            "--artifact-name",
            "plugin-demo",
        ],
    )

    assert result.exit_code == 0, result.output
    notebook = json.loads(output_path.read_text(encoding="utf-8"))
    code_text = "\n".join(
        cell["source"]
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code" and isinstance(cell.get("source"), str)
    )
    assert "import spectrafit.notebook as sf" in code_text
    assert "df = sf.read(DATA_PATH" in code_text
    assert "result = sf.fit(" in code_text
    assert "artifacts = result.save(OUTPUT_DIR, name='plugin-demo')" in code_text
    assert "FitParameter(" not in code_text
    assert "Component(" not in code_text
    assert "UnifiedFittingConfig(" not in code_text
    assert "SpectraFitNotebook.from_config" not in code_text

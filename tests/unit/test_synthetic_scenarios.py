"""Unit tests for shared synthetic scenario definitions."""

from __future__ import annotations

import json
import tomllib

from pathlib import Path

import pandas as pd
import pandas.testing as pdt
import pytest

from scripts import generate_examples
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.generators.scenarios import ExampleInputConfig
from spectrafit.generators.scenarios import SyntheticScenario
from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.generators.scenarios import iter_example_scenarios
from spectrafit.jupyter.templates.starter_nb import build_example_notebook
from spectrafit.jupyter.templates.starter_nb import build_starter_notebook


REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
@pytest.mark.parametrize(
    "scenario", iter_example_scenarios(), ids=lambda item: item.name
)
def test_example_scenarios_match_committed_examples(
    scenario: SyntheticScenario,
) -> None:
    assert scenario.example_dir is not None

    example_dir = REPO_ROOT / "examples" / scenario.example_dir
    actual_data = pd.read_csv(example_dir / "data.csv")
    expected_data = scenario.to_dataframe()
    pdt.assert_frame_equal(actual_data, expected_data)

    actual_text = (example_dir / "input.toml").read_text()
    assert actual_text == scenario.example_input_toml()

    expected_payload = scenario.example_input_payload()
    actual_payload = tomllib.loads(actual_text)
    assert actual_payload == expected_payload

    expected_config = scenario.to_config().model_dump(mode="json", exclude_none=True)
    actual_config = UnifiedFittingConfig.from_dict(actual_payload).model_dump(
        mode="json",
        exclude_none=True,
    )

    assert actual_config["components"] == expected_config["components"]
    assert actual_config["minimizer"] == expected_config["minimizer"]
    assert actual_config["optimizer"] == expected_config["optimizer"]


@pytest.mark.unit
def test_build_starter_notebook_uses_supplied_typed_config() -> None:
    notebook = build_starter_notebook("demo", get_synthetic_scenario("basic").to_config())
    sources = [
        cell["source"]
        for cell in notebook["cells"]
        if isinstance(cell, dict) and cell.get("cell_type") == "code"
    ]
    code_text = "\n".join(source for source in sources if isinstance(source, str))

    assert 'get_synthetic_scenario("starter-notebook")' not in code_text
    assert "FitParameter(" in code_text
    assert "Component(" in code_text
    assert "UnifiedFittingConfig(" in code_text
    assert "config = config.with_data_infile(DATA_PATH.resolve())" in code_text
    assert "df = load_data(config.data)" in code_text
    assert "notebook.initial_components" in code_text
    assert "column =" not in code_text
    assert "config_payload = {" not in code_text
    assert "resolved_config_payload" not in code_text
    assert "UnifiedFittingConfig.model_validate(resolved_config_payload)" not in code_text
    assert "UnifiedFittingConfig.from_file(CONFIG_PATH)" not in code_text
    assert "SpectraFitNotebook.from_config" in code_text


@pytest.mark.unit
def test_build_example_notebook_uses_local_committed_files() -> None:
    notebook = build_example_notebook(
        example_name="basic",
        description="Single Gaussian peak with a flat linear background.",
    )
    sources = [
        cell["source"]
        for cell in notebook["cells"]
        if isinstance(cell, dict) and cell.get("cell_type") == "code"
    ]
    code_text = "\n".join(source for source in sources if isinstance(source, str))

    assert "DATA_PATH = NOTEBOOK_ROOT / 'data.csv'" in code_text
    assert "FitParameter(" in code_text
    assert "Component(" in code_text
    assert "UnifiedFittingConfig(" in code_text
    assert "config = config.with_data_infile(DATA_PATH.resolve())" in code_text
    assert "df = load_data(config.data)" in code_text
    assert "notebook.initial_components" in code_text
    assert "config_payload = {" not in code_text
    assert "resolved_config_payload" not in code_text
    assert "UnifiedFittingConfig.model_validate(resolved_config_payload)" not in code_text
    assert "UnifiedFittingConfig.from_file(CONFIG_PATH)" not in code_text
    assert "SpectraFitNotebook.from_config" in code_text
    assert "folder=str(OUTPUT_DIR)" in code_text


@pytest.mark.unit
def test_generate_examples_writes_shared_scenarios(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(generate_examples, "_REPO_ROOT", tmp_path)

    generate_examples.main(seed=7)

    for scenario in iter_example_scenarios():
        assert scenario.example_dir is not None
        written = pd.read_csv(tmp_path / "examples" / scenario.example_dir / "data.csv")
        expected = scenario.to_dataframe(seed=7)
        pdt.assert_frame_equal(written, expected)

        input_toml = tmp_path / "examples" / scenario.example_dir / "input.toml"
        assert input_toml.read_text() == scenario.example_input_toml()
        actual_payload = tomllib.loads(input_toml.read_text())
        assert actual_payload == scenario.example_input_payload()

        notebook_path = tmp_path / "examples" / scenario.example_dir / "notebook.ipynb"
        assert notebook_path.exists()
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        code_text = "\n".join(
            cell["source"]
            for cell in notebook["cells"]
            if cell.get("cell_type") == "code" and isinstance(cell.get("source"), str)
        )
        assert "DATA_PATH = NOTEBOOK_ROOT / 'data.csv'" in code_text
        assert "FitParameter(" in code_text
        assert "Component(" in code_text
        assert "UnifiedFittingConfig(" in code_text
        assert "config = config.with_data_infile(DATA_PATH.resolve())" in code_text
        assert "df = load_data(config.data)" in code_text
        assert "notebook.initial_components" in code_text
        assert "config_payload = {" not in code_text
        assert "UnifiedFittingConfig.model_validate(resolved_config_payload)" not in code_text
        assert "UnifiedFittingConfig.from_file(CONFIG_PATH)" not in code_text
        assert "SpectraFitNotebook.from_config" in code_text


@pytest.mark.unit
@pytest.mark.parametrize(
    "scenario_name",
    ["basic", "two-peak-constrained"],
)
def test_example_input_toml_uses_inline_parameter_tables(scenario_name: str) -> None:
    scenario = get_synthetic_scenario(scenario_name)

    rendered = scenario.example_input_toml()

    assert "[components.parameters]" in rendered
    assert "[components.parameters.amplitude]" not in rendered
    assert tomllib.loads(rendered) == scenario.example_input_payload()


@pytest.mark.unit
def test_constrained_example_input_toml_preserves_dot_notation_exprs() -> None:
    rendered = get_synthetic_scenario("two-peak-constrained").example_input_toml()

    assert 'expr = "p1.center + 1.0"' in rendered
    assert 'expr = "p2.fwhmg"' in rendered


@pytest.mark.unit
def test_example_input_config_is_typed_and_matches_payload() -> None:
    scenario = get_synthetic_scenario("basic")

    example_config = scenario.example_input_config()

    assert isinstance(example_config, ExampleInputConfig)
    assert example_config.data.infile == "data.csv"
    assert example_config.meta.description == scenario.description
    assert example_config.model_dump(
        mode="json",
        exclude_none=True,
    ) == scenario.example_input_payload()


@pytest.mark.unit
def test_synthetic_scenario_separates_truth_from_materialization() -> None:
    scenario = get_synthetic_scenario("basic")

    assert scenario.truth.name == scenario.name
    assert scenario.truth.description == scenario.description
    assert scenario.materialization.example_dir == scenario.example_dir

    config = scenario.to_config()
    config.components[0].parameters["amplitude"].value = 99.0

    assert (
        scenario.materialization.config.components[0].parameters["amplitude"].value == 1.0
    )


@pytest.mark.unit
def test_unknown_synthetic_scenario_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="Unknown synthetic scenario"):
        get_synthetic_scenario("does-not-exist")

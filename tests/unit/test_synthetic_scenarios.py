"""Unit tests for shared synthetic scenario definitions."""

from __future__ import annotations

import json
import tomllib

from pathlib import Path
from typing import cast

import pandas as pd
import pandas.testing as pdt
import pytest
import typer

from scripts import generate_examples
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.generators.scenarios import ExampleInputConfig
from spectrafit.generators.scenarios import SyntheticScenario
from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.generators.scenarios import iter_example_scenarios
from spectrafit.jupyter.templates.starter_nb import build_example_notebook
from spectrafit.jupyter.templates.starter_nb import build_starter_notebook


REPO_ROOT = Path(__file__).resolve().parents[2]


def _code_cell_sources(notebook: dict[str, object]) -> list[str]:
    """Return the code-cell sources from a notebook payload."""
    cells = notebook["cells"]
    assert isinstance(cells, list)

    sources: list[str] = []
    for raw_cell in cells:
        assert isinstance(raw_cell, dict)
        cell = cast("dict[str, object]", raw_cell)
        if cell.get("cell_type") != "code":
            continue
        source = cell.get("source")
        if isinstance(source, str):
            sources.append(source)
    return sources


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
    notebook = build_starter_notebook(
        "demo", get_synthetic_scenario("basic").to_config()
    )
    code_text = "\n".join(_code_cell_sources(notebook))

    assert 'get_synthetic_scenario("starter-notebook")' not in code_text
    assert "import spectrafit.notebook as sf" in code_text
    assert "df = sf.read(DATA_PATH, x='energy', y='intensity')" in code_text
    assert "sf.peak(" in code_text
    assert "sf.background(" in code_text
    assert "sf.OptimizerConfig(" in code_text
    assert "result = sf.fit(" in code_text
    assert "result.plot()" in code_text
    assert "artifacts = result.save(OUTPUT_DIR, name='demo')" in code_text
    assert "config_payload = {" not in code_text
    assert "resolved_config_payload" not in code_text
    assert "UnifiedFittingConfig(" not in code_text
    assert "FitParameter(" not in code_text
    assert "Component(" not in code_text
    assert "SpectraFitNotebook.from_config" not in code_text


@pytest.mark.unit
def test_build_example_notebook_uses_local_committed_files() -> None:
    notebook = build_example_notebook(
        example_name="basic",
        description="Single Gaussian peak with a flat linear background.",
    )
    code_text = "\n".join(_code_cell_sources(notebook))

    assert "DATA_PATH = NOTEBOOK_ROOT / 'data.csv'" in code_text
    assert "import spectrafit.notebook as sf" in code_text
    assert "df = sf.read(DATA_PATH, x='energy', y='intensity')" in code_text
    assert "sf.peak(" in code_text
    assert "sf.background(" in code_text
    assert "sf.OptimizerConfig(" in code_text
    assert "result = sf.fit(" in code_text
    assert "artifacts = result.save(OUTPUT_DIR, name='basic')" in code_text
    assert "config_payload = {" not in code_text
    assert "resolved_config_payload" not in code_text
    assert "UnifiedFittingConfig(" not in code_text
    assert "FitParameter(" not in code_text
    assert "Component(" not in code_text
    assert "SpectraFitNotebook.from_config" not in code_text


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
        code_text = "\n".join(_code_cell_sources(notebook))
        assert "DATA_PATH = NOTEBOOK_ROOT / 'data.csv'" in code_text
        assert "import spectrafit.notebook as sf" in code_text
        assert "df = sf.read(DATA_PATH, x='energy', y='intensity')" in code_text
        assert "sf.peak(" in code_text
        assert "sf.background(" in code_text
        assert "sf.OptimizerConfig(" in code_text
        assert "result = sf.fit(" in code_text
        assert "config_payload = {" not in code_text
        assert "UnifiedFittingConfig(" not in code_text
        assert "FitParameter(" not in code_text
        assert "Component(" not in code_text
        assert "SpectraFitNotebook.from_config" not in code_text


@pytest.mark.unit
def test_generate_examples_check_passes_for_fresh_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(generate_examples, "_REPO_ROOT", tmp_path)

    generate_examples.main(seed=7)
    generate_examples.main(seed=7, check=True)

    captured = capsys.readouterr()
    assert "Committed example artifacts are up to date" in captured.out


@pytest.mark.unit
def test_generate_examples_check_fails_for_stale_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(generate_examples, "_REPO_ROOT", tmp_path)

    generate_examples.main(seed=7)
    stale_file = tmp_path / "examples" / "basic" / "input.toml"
    stale_file.write_text('schema_version = "999.0"\n', encoding="utf-8")

    with pytest.raises(typer.Exit) as exc_info:
        generate_examples.main(seed=7, check=True)

    assert exc_info.value.exit_code == 1
    captured = capsys.readouterr()
    assert "Committed example artifacts are stale" in captured.err
    assert "basic/input.toml (stale)" in captured.err
    assert "uv run poe generate-examples" in captured.err


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
    assert (
        example_config.model_dump(
            mode="json",
            exclude_none=True,
        )
        == scenario.example_input_payload()
    )


@pytest.mark.unit
def test_synthetic_scenario_separates_truth_from_materialization() -> None:
    scenario = get_synthetic_scenario("basic")

    assert scenario.truth.name == scenario.name
    assert scenario.truth.description == scenario.description
    assert scenario.materialization.example_dir == scenario.example_dir

    config = scenario.to_config()
    config.components[0].parameters["amplitude"].value = 99.0

    assert (
        scenario.materialization.config.components[0].parameters["amplitude"].value
        == 1.0
    )


@pytest.mark.unit
def test_unknown_synthetic_scenario_raises_clear_error() -> None:
    with pytest.raises(ValueError, match="Unknown synthetic scenario"):
        get_synthetic_scenario("does-not-exist")

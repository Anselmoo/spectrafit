"""Unit tests for the convert CLI command."""

from __future__ import annotations

import builtins
import importlib
import json

from pathlib import Path

import pytest

from spectrafit.cli._types import OutputFormatEnum
from spectrafit.cli.commands.convert import _dict_to_toml
from spectrafit.cli.commands.convert import _format_toml_value
from spectrafit.cli.commands.convert import _read_config
from spectrafit.cli.commands.convert import _write_config
from spectrafit.cli.main import app
from spectrafit.generators.scenarios import get_synthetic_scenario
from typer.testing import CliRunner


runner = CliRunner()
convert_module = importlib.import_module("spectrafit.cli.commands.convert")


@pytest.mark.unit
def test_convert_command_creates_requested_output_format(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.toml"
    input_file.write_text(
        json.dumps({"components": [], "minimizer": {}, "optimizer": {}}),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        ["convert", str(input_file), "--format", "toml", "--output", str(output_file)],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()


@pytest.mark.unit
def test_convert_command_materializes_notebook_output(tmp_path: Path) -> None:
    input_file = tmp_path / "input.toml"
    output_file = tmp_path / "analysis.ipynb"
    input_file.write_text(
        get_synthetic_scenario("basic").example_input_toml(),
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "convert",
            str(input_file),
            "--format",
            "ipynb",
            "--output",
            str(output_file),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output_file.exists()
    notebook = json.loads(output_file.read_text(encoding="utf-8"))
    code_text = "\n".join(
        cell["source"]
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code" and isinstance(cell.get("source"), str)
    )
    assert "FitParameter(" in code_text
    assert "Component(" in code_text
    assert "UnifiedFittingConfig(" in code_text
    assert "config = config.with_data_infile(DATA_PATH.resolve())" in code_text
    assert "config_payload = {" not in code_text
    assert "resolved_config_payload = {" not in code_text
    assert "UnifiedFittingConfig.from_file(" not in code_text


@pytest.mark.unit
def test_convert_command_defaults_notebook_extension_when_requested(tmp_path: Path) -> None:
    input_file = tmp_path / "input.toml"
    output_file = tmp_path / "input.ipynb"
    input_file.write_text(
        get_synthetic_scenario("basic").example_input_toml(),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["convert", str(input_file), "--format", "ipynb"])

    assert result.exit_code == 0, result.output
    assert output_file.exists()


@pytest.mark.unit
def test_convert_command_rejects_same_input_and_output_path(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    input_file.write_text("{}", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "convert",
            str(input_file),
            "--format",
            "json",
            "--output",
            str(input_file),
            "--force",
        ],
    )

    assert result.exit_code == 1
    assert "Input and output files cannot be the same" in result.output


@pytest.mark.unit
def test_convert_command_rejects_existing_output_without_force(tmp_path: Path) -> None:
    input_file = tmp_path / "input.json"
    output_file = tmp_path / "output.yaml"
    input_file.write_text("{}", encoding="utf-8")
    output_file.write_text("already here", encoding="utf-8")

    result = runner.invoke(
        app,
        ["convert", str(input_file), "--format", "yaml", "--output", str(output_file)],
    )

    assert result.exit_code == 1
    assert "already exists" in result.output


@pytest.mark.unit
def test_convert_command_reports_unsupported_input_format(tmp_path: Path) -> None:
    input_file = tmp_path / "input.txt"
    input_file.write_text("unsupported", encoding="utf-8")

    result = runner.invoke(app, ["convert", str(input_file)])

    assert result.exit_code == 1
    assert "Unsupported input format" in result.output


@pytest.mark.unit
@pytest.mark.parametrize(
    ("suffix", "content", "expected"),
    [
        (".json", '{"alpha": 1}', {"alpha": 1}),
        (".toml", "alpha = 1\n", {"alpha": 1}),
        (".yaml", "alpha: 1\n", {"alpha": 1}),
    ],
)
def test_read_config_supports_common_input_formats(
    tmp_path: Path,
    suffix: str,
    content: str,
    expected: dict[str, object],
) -> None:
    input_file = tmp_path / f"config{suffix}"
    mode = "wb" if suffix == ".toml" else "w"
    if mode == "wb":
        input_file.write_bytes(content.encode("utf-8"))
    else:
        input_file.write_text(content, encoding="utf-8")

    assert _read_config(input_file) == expected


@pytest.mark.unit
def test_read_config_rejects_unknown_extension(tmp_path: Path) -> None:
    input_file = tmp_path / "config.ini"
    input_file.write_text("[section]\n", encoding="utf-8")

    with pytest.raises(OSError, match="Unsupported input format"):
        _read_config(input_file)


@pytest.mark.unit
def test_write_config_serializes_json_yaml_and_toml(tmp_path: Path) -> None:
    config = {"alpha": 1, "items": ["x", "y"]}

    json_path = tmp_path / "out.json"
    yaml_path = tmp_path / "out.yaml"
    toml_path = tmp_path / "out.toml"

    _write_config(config, json_path, OutputFormatEnum.JSON)
    _write_config(config, yaml_path, OutputFormatEnum.YAML)
    _write_config(config, toml_path, OutputFormatEnum.TOML)

    assert json.loads(json_path.read_text(encoding="utf-8")) == config
    assert "alpha: 1" in yaml_path.read_text(encoding="utf-8")
    toml_output = toml_path.read_text(encoding="utf-8")
    assert "alpha = 1" in toml_output
    assert '"x"' in toml_output
    assert '"y"' in toml_output


@pytest.mark.unit
def test_write_config_toml_falls_back_when_tomli_w_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output_file = tmp_path / "fallback.toml"
    original_import = builtins.__import__

    def _fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "tomli_w":
            msg = "missing for test"
            raise ImportError(msg)
        return original_import(name, globals_, locals_, fromlist, level)

    def _fallback_toml_writer(*_args: object, **_kwargs: object) -> str:
        return 'alpha = "fallback"\n'

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    monkeypatch.setattr(convert_module, "_dict_to_toml", _fallback_toml_writer)

    _write_config({"alpha": "fallback"}, output_file, OutputFormatEnum.TOML)

    assert output_file.read_text(encoding="utf-8") == 'alpha = "fallback"\n'


@pytest.mark.unit
def test_dict_to_toml_renders_nested_tables_and_array_of_tables() -> None:
    toml_text = _dict_to_toml(
        {
            "name": "demo",
            "enabled": True,
            "thresholds": [1, 2],
            "solver": {"method": "leastsq"},
            "components": [{"id": "p1", "model": "gaussian"}],
        }
    )

    assert 'name = "demo"' in toml_text
    assert "enabled = true" in toml_text
    assert "thresholds = [1, 2]" in toml_text
    assert "[solver]" in toml_text
    assert 'method = "leastsq"' in toml_text
    assert "[[components]]" in toml_text
    assert 'model = "gaussian"' in toml_text


@pytest.mark.unit
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, "true"),
        (False, "false"),
        ("alpha", '"alpha"'),
        (3, "3"),
        (2.5, "2.5"),
        ([1, "x"], '[1, "x"]'),
        (None, '""'),
    ],
)
def test_format_toml_value_supports_scalar_types(value: object, expected: str) -> None:
    assert _format_toml_value(value) == expected

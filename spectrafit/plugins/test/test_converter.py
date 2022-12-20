"""Test of the converter plugin."""

import json

from pathlib import Path
from typing import Any

import pytest
import tomli
import tomli_w
import yaml

from spectrafit.plugins.file_converter import FileConverter


def test_cmd_converter(script_runner: Any) -> None:
    """Test the converter plugin."""
    ret = script_runner.run("spectrafit-file-converter", "-h")

    assert ret.success
    assert "Converter for 'SpectraFit' input and output files." in ret.stdout
    assert ret.stderr == ""


def test_raise_input_output() -> None:
    """Test raise error input format is similar to ouptut."""
    with pytest.raises(ValueError) as excinfo:
        FileConverter().convert(
            infile=Path("spectrafit/test/scripts/fitting_input.yaml"),
            file_format="yaml",
        )

    assert (
        "The input file suffix 'yaml' is similar to the output file format 'yaml'."
        in str(excinfo.value)
    )


def test_raise_no_guilty_ouput() -> None:
    """Test illegal output format."""
    with pytest.raises(ValueError) as excinfo:
        FileConverter().convert(
            infile=Path("tests/data/input/input_1.yaml"),
            file_format="illegal",
        )
    assert "The output file format 'illegal' is not supported." in str(excinfo.value)


def test_json_conversion(tmp_path: Path) -> None:
    """Test json to yaml conversion."""
    infile = tmp_path / "input_1.json"

    with open(infile, "w", encoding="utf8") as f:
        json.dump({"a": 1, "b": 2}, f)
    FileConverter().convert(
        infile=infile,
        file_format="yaml",
    )
    with open(infile.with_suffix(".yaml"), encoding="utf8") as f:
        data = yaml.safe_load(f)

    assert data == {"a": 1, "b": 2}


def test_yaml_conversion(tmp_path: Path) -> None:
    """Test yaml to json conversion."""
    infile = tmp_path / "input_1.yaml"

    with open(infile, "w", encoding="utf8") as f:
        yaml.dump({"a": 1, "b": 2}, f)
    FileConverter().convert(
        infile=infile,
        file_format="toml",
    )
    with open(infile.with_suffix(".toml"), "rb") as f:
        data = tomli.load(f)

    assert data == {"a": 1, "b": 2}


def test_toml_conversion(tmp_path: Path) -> None:
    """Test toml to json conversion."""
    infile = tmp_path / "input_1.toml"

    with open(infile, "wb+") as f:
        tomli_w.dump({"a": 1, "b": 2}, f)
    FileConverter().convert(
        infile=infile,
        file_format="json",
    )
    with open(infile.with_suffix(".json"), encoding="utf8") as f:
        data = json.load(f)

    assert data == {"a": 1, "b": 2}

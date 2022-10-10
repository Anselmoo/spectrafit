"""Test of the converter plugin."""

import json

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pytest
import tomli
import tomli_w
import yaml

from spectrafit.plugins.converter import convert


def test_cmd_converter(script_runner: Any) -> None:
    """Test the converter plugin."""
    ret = script_runner.run("spectrafit-converter", "-h")

    assert ret.success
    assert "Converter for 'SpectraFit' input and output files." in ret.stdout
    assert ret.stderr == ""


def test_raise_input_output() -> None:
    """Test raise error input format is similar to ouptut."""
    args = {
        "infile": Path("tests/data/input/input_1.yaml"),
        "format": "yaml",
    }
    with pytest.raises(ValueError) as excinfo:
        convert(args)

    assert (
        "The input file suffix 'yaml' is similar to the output file format 'yaml'."
        in str(excinfo.value)
    )


def test_raise_no_guilty_ouput() -> None:
    """Test illegal output format."""
    args = {
        "infile": Path("tests/data/input/input_1.yaml"),
        "format": "illegal",
    }
    with pytest.raises(ValueError) as excinfo:
        convert(args)
    assert "The output file format 'illegal' is not supported." in str(excinfo.value)


def test_json_conversion() -> None:
    """Test json to yaml conversion."""
    with TemporaryDirectory() as tmpdir:
        infile = Path(tmpdir) / "input_1.json"

        # write input json
        with open(infile, "w", encoding="utf8") as f:
            json.dump({"a": 1, "b": 2}, f)
        args = {
            "infile": infile,
            "format": "yaml",
        }
        convert(args)
        with open(infile.with_suffix(".yaml"), encoding="utf8") as f:
            data = yaml.safe_load(f)

        assert data == {"a": 1, "b": 2}


def test_yaml_conversion() -> None:
    """Test yaml to json conversion."""
    with TemporaryDirectory() as tmpdir:
        infile = Path(tmpdir) / "input_1.yaml"

        # write input yaml
        with open(infile, "w", encoding="utf8") as f:
            yaml.dump({"a": 1, "b": 2}, f)
        args = {
            "infile": infile,
            "format": "toml",
        }
        convert(args)
        with open(infile.with_suffix(".toml"), "rb") as f:
            data = tomli.load(f)

        assert data == {"a": 1, "b": 2}


def test_toml_conversion() -> None:
    """Test toml to json conversion."""
    with TemporaryDirectory() as tmpdir:
        infile = Path(tmpdir) / "input_1.toml"

        # write input toml
        with open(infile, "wb+") as f:
            tomli_w.dump({"a": 1, "b": 2}, f)
        args = {
            "infile": infile,
            "format": "json",
        }
        convert(args)
        with open(infile.with_suffix(".json"), encoding="utf8") as f:
            data = json.load(f)

        assert data == {"a": 1, "b": 2}

"""Test of the converter plugin."""

import json

from pathlib import Path
from typing import Any

import pandas as pd
import pytest
import tomli
import tomli_w
import yaml

from spectrafit.plugins.data_converter import DataConverter
from spectrafit.plugins.file_converter import FileConverter


def test_cmd_file_converter(script_runner: Any) -> None:
    """Test the file converter plugin."""
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


@pytest.mark.parametrize(
    "file_format",
    [
        "json",
        "toml",
    ],
)
def test_conversion(tmp_path: Path, file_format: str) -> None:
    """Test conversion of the input file.

    Args:
        tmp_path (Path): Temporary path.
        file_format (str): File format to convert to.
    """
    infile = tmp_path / "input_1.yaml"
    with open(infile, "w", encoding="utf8") as f:
        yaml.dump({"a": 1, "b": 2}, f)

    FileConverter().convert(
        infile=infile,
        file_format=file_format,
    )

    if file_format == "json":
        with open(infile.with_suffix(f".{file_format}"), encoding="utf8") as f:
            data_json = json.load(f)
            assert data_json == {"a": 1, "b": 2}

    if file_format == "toml":
        with open(infile.with_suffix(f".{file_format}"), "rb") as f:
            data_toml = tomli.load(f)
            assert data_toml == {"a": 1, "b": 2}


# Create temporary writen file.
@pytest.fixture(scope="function", autouse=True, name="tmp_file_nor")
def tmp_file_nor(tmp_path: Path) -> Path:
    """Create temporary file.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file.nor"
    with open(tmp_file, "w", encoding="utf8") as f:
        nor_format = (
            "# Demeter.output_filetype: multicolumn normalized mu(E)\n"
            "# Element.symbol: V\n"
            "# Element.edge: K\n"
            "# Column.1: energy eV\n"
            "# Column.2: JZP-4-merged\n"
            "#------------------------\n"
            "#  energy  JZP-4-merged\n"
            "  5263.8492       0.12737417\n"
            "  5273.8501       0.10231758\n"
            "  5283.8503       0.81114410E-01\n"
            "  5293.8492       0.61588687E-01\n"
            "  5303.8493       0.47158833E-01\n"
            "  5313.8497       0.35236642E-01\n"
            "  5323.8502       0.25314870E-01\n"
            "  5333.8506       0.18438437E-01\n"
            "  5343.8501       0.12077480E-01\n"
        )
        f.write(nor_format)
    return tmp_file


@pytest.fixture(scope="function", autouse=True, name="tmp_file_txt")
def tmp_file_txt(tmp_path: Path) -> Path:
    """Create temporary file.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file.txt"
    with open(tmp_file, "w", encoding="utf8") as f:
        txt_format = (
            "energy\tJZP-4-merged\n"
            "5263.8492\t0.12737417\n"
            "5273.8501\t0.10231758\n"
            "5283.8503\t0.81114410E-01\n"
            "5293.8492\t0.61588687E-01\n"
            "5303.8493\t0.47158833E-01\n"
            "5313.8497\t0.35236642E-01\n"
            "5323.8502\t0.25314870E-01\n"
            "5333.8506\t0.18438437E-01\n"
            "5343.8501\t0.12077480E-01\n"
        )
        f.write(txt_format)
    return tmp_file


@pytest.fixture(scope="function", autouse=True, name="reference_dataframe")
def reference_dataframe() -> pd.DataFrame:
    """Create reference dataframe.

    Returns:
        pd.DataFrame: Reference dataframe.
    """
    return pd.DataFrame(
        {
            "energy": [
                5263.8492,
                5273.8501,
                5283.8503,
                5293.8492,
                5303.8493,
                5313.8497,
                5323.8502,
                5333.8506,
                5343.8501,
            ],
            "JZP-4-merged": [
                0.12737417,
                0.10231758,
                0.08111441,
                0.06158869,
                0.04715883,
                0.03523664,
                0.02531487,
                0.01843844,
                0.01207748,
            ],
        }
    )


def test_nor_to_csv(tmp_file_nor: Path, reference_dataframe: pd.DataFrame) -> None:
    """Test nor to csv conversion.

    Args:
        tmp_file_nor (Path): Path to temporary file.
        reference_dataframe (pd.DataFrame): Reference dataframe.
    """
    dc = DataConverter()
    df = dc.convert(tmp_file_nor, "ATHENA")

    assert isinstance(df, pd.DataFrame)
    pd.testing.assert_frame_equal(df, reference_dataframe)

    dc.save(tmp_file_nor.with_suffix(".csv"), df)
    assert tmp_file_nor.with_suffix(".csv").exists()


def test_txt_to_csv(tmp_file_txt: Path, reference_dataframe: pd.DataFrame) -> None:
    """Test txt to csv conversion.

    Args:
        tmp_file_txt (Path): Path to temporary file.
        reference_dataframe (pd.DataFrame): Reference dataframe.
    """
    dc = DataConverter()
    df = dc.convert(tmp_file_txt, "TXT")

    assert isinstance(df, pd.DataFrame)
    pd.testing.assert_frame_equal(df, reference_dataframe)
    dc.save(tmp_file_txt.with_suffix(".csv"), df)
    assert tmp_file_txt.with_suffix(".csv").exists()


def test_fail_convert(tmp_file_txt: Path) -> None:
    """Test fail conversion.

    Args:
        tmp_file_txt (Path): Path to temporary file.
    """
    file_format = "WRONG"
    with pytest.raises(ValueError) as excinfo:
        DataConverter().convert(tmp_file_txt, file_format)

    assert isinstance(excinfo.value, ValueError)
    assert f"File format '{file_format}' is not supported." in str(excinfo.value)


def test_cmd_data_converter(script_runner: Any) -> None:
    """Test the data converter plugin."""
    ret = script_runner.run("spectrafit-data-converter", "-h")

    assert ret.success
    assert "Converter for 'SpectraFit' from data files to CSV files." in ret.stdout
    assert ret.stderr == ""


def test_cmd_data_converter_nor_to_csv(script_runner: Any, tmp_file_nor: Path) -> None:
    """Test the data converter plugin.

    Args:
        script_runner (Any): Script runner.
        tmp_file_nor (Path): Path to temporary file.
    """
    ret = script_runner.run(
        "spectrafit-data-converter",
        str(tmp_file_nor),
        "-f",
        "ATHENA",
    )

    assert ret.success
    assert ret.stdout == ""
    assert ret.stderr == ""
    assert tmp_file_nor.with_suffix(".csv").exists()

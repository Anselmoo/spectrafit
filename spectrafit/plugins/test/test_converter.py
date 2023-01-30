"""Test of the converter plugin."""

import gzip
import json
import pickle

from pathlib import Path
from typing import Any
from typing import Dict
from typing import Tuple

import numpy as np
import pandas as pd
import pytest
import toml
import tomli
import tomli_w
import yaml

from matplotlib import pyplot
from nptyping import Float
from nptyping import NDArray
from nptyping import Shape
from spectrafit.plugins.data_converter import DataConverter
from spectrafit.plugins.file_converter import FileConverter
from spectrafit.plugins.pkl_converter import ExportData
from spectrafit.plugins.pkl_converter import PklConverter
from spectrafit.plugins.pkl_visualizer import PklVisualizer
from spectrafit.plugins.rixs_converter import RIXSConverter


class TestFileConverter:
    """Test the file converter plugin."""

    def test_cmd_file_converter(self, script_runner: Any) -> None:
        """Test the file converter plugin."""
        ret = script_runner.run("spectrafit-file-converter", "-h")

        assert ret.success
        assert "Converter for 'SpectraFit' input and output files." in ret.stdout
        assert ret.stderr == ""

    def test_raise_input_output(
        self,
    ) -> None:
        """Test raise error input format is similar to ouptut."""
        with pytest.raises(ValueError) as excinfo:
            data = FileConverter.convert(
                infile=Path("spectrafit/test/scripts/fitting_input.yaml"),
                file_format="yaml",
            )
            FileConverter().save(
                data=data,
                fname=Path("spectrafit/test/scripts/fitting_input.yaml"),
                export_format="yaml",
            )

        assert (
            "The input file suffix 'yaml' is similar to the output file format 'yaml'."
            in str(excinfo.value)
        )

    def test_raise_no_guilty_input(
        self,
    ) -> None:
        """Test illegal output format."""
        with pytest.raises(ValueError) as excinfo:
            FileConverter.convert(
                infile=Path("tests/data/input/input.yaml"),
                file_format="illegal",
            )
        assert "The input file format 'illegal' is not supported." in str(excinfo.value)

    def test_raise_no_guilty_output(self, tmp_path: Path) -> None:
        """Test illegal output format."""
        infile = tmp_path / "input_1.yaml"

        with open(infile, "w", encoding="utf-8") as f:
            yaml.dump({"a": [1, 2], "b": [2, 3]}, f)

        with pytest.raises(ValueError) as excinfo:
            FileConverter().save(
                data=FileConverter.convert(
                    infile=infile,
                    file_format="yaml",
                ),
                fname=infile,
                export_format="illegal",
            )

        assert "The output file format 'illegal' is not supported." in str(
            excinfo.value
        )

    def test_json_conversion(self, tmp_path: Path) -> None:
        """Test json to yaml conversion."""
        infile = tmp_path / "input_1.json"

        with open(infile, "w", encoding="utf-8") as f:
            json.dump({"a": 1, "b": 2}, f)

        FileConverter().save(
            data=FileConverter.convert(
                infile=infile,
                file_format="yaml",
            ),
            fname=infile,
            export_format="yaml",
        )
        with open(infile.with_suffix(".yaml"), encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data == {"a": 1, "b": 2}

    def test_yaml_conversion(self, tmp_path: Path) -> None:
        """Test yaml to json conversion."""
        infile = tmp_path / "input_2.yaml"

        with open(infile, "w", encoding="utf-8") as f:
            yaml.dump({"a": 1, "b": 2}, f)
        FileConverter().save(
            data=FileConverter.convert(
                infile=infile,
                file_format="toml",
            ),
            fname=infile,
            export_format="toml",
        )
        with open(infile.with_suffix(".toml"), "rb") as f:
            data = tomli.load(f)

        assert data == {"a": 1, "b": 2}

    def test_cmd_file_converter_2(self, script_runner: Any, tmp_path: Path) -> None:
        """Test the file converter plugin."""
        fname = tmp_path / "input_4.yaml"
        with open(fname, "w", encoding="utf-8") as f:
            yaml.dump({"a": [1, 1], "b": [2, 2]}, f)

        ret = script_runner.run(
            "spectrafit-file-converter",
            str(fname),
            "--file-format",
            "json",
        )

        assert ret.success
        assert Path(fname.with_suffix(".json")).exists()

    def test_toml_conversion(self, tmp_path: Path) -> None:
        """Test toml to json conversion."""
        infile = tmp_path / "input_1.toml"

        with open(infile, "wb+") as f:
            tomli_w.dump({"a": 1, "b": 2}, f)
        FileConverter().save(
            data=FileConverter.convert(
                infile=infile,
                file_format="json",
            ),
            fname=infile,
            export_format="json",
        )
        with open(infile.with_suffix(".json"), encoding="utf-8") as f:
            data = json.load(f)

        assert data == {"a": 1, "b": 2}

    @pytest.mark.parametrize(
        "file_format",
        [
            "json",
            "toml",
        ],
    )
    def test_conversion(self, tmp_path: Path, file_format: str) -> None:
        """Test conversion of the input file.

        Args:
            tmp_path (Path): Temporary path.
            file_format (str): File format to convert to.
        """
        infile = tmp_path / "input_3.yaml"
        with open(infile, "w", encoding="utf-8") as f:
            yaml.dump({"a": 1, "b": 2}, f)

        FileConverter().save(
            data=FileConverter.convert(
                infile=infile,
                file_format="yaml",
            ),
            fname=infile,
            export_format=file_format,
        )

        if file_format == "json":
            with open(infile.with_suffix(f".{file_format}"), encoding="utf-8") as f:
                data_json = json.load(f)
                assert data_json == {"a": 1, "b": 2}

        if file_format == "toml":
            with open(infile.with_suffix(f".{file_format}"), "rb") as f:
                data_toml = tomli.load(f)
                assert data_toml == {"a": 1, "b": 2}


@pytest.fixture(scope="function", autouse=True, name="tmp_file_nor")
def tmp_file_nor(tmp_path: Path) -> Path:
    """Create temporary file.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file.nor"
    with open(tmp_file, "w", encoding="utf-8") as f:
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
    with open(tmp_file, "w", encoding="utf-8") as f:
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


class TestDataConverter:
    """Test DataConverter class."""

    def test_nor_to_csv(
        self, tmp_file_nor: Path, reference_dataframe: pd.DataFrame
    ) -> None:
        """Test nor to csv conversion.

        Args:
            tmp_file_nor (Path): Path to temporary file.
            reference_dataframe (pd.DataFrame): Reference dataframe.
        """
        dc = DataConverter()
        df = dc.convert(tmp_file_nor, "ATHENA")

        assert isinstance(df, pd.DataFrame)
        pd.testing.assert_frame_equal(df, reference_dataframe)

        dc.save(data=df, fname=tmp_file_nor.with_suffix(".csv"), export_format="csv")
        assert tmp_file_nor.with_suffix(".csv").exists()

    def test_txt_to_csv(
        self, tmp_file_txt: Path, reference_dataframe: pd.DataFrame
    ) -> None:
        """Test txt to csv conversion.

        Args:
            tmp_file_txt (Path): Path to temporary file.
            reference_dataframe (pd.DataFrame): Reference dataframe.
        """
        dc = DataConverter()
        df = dc.convert(tmp_file_txt, "TXT")

        assert isinstance(df, pd.DataFrame)
        pd.testing.assert_frame_equal(df, reference_dataframe)
        dc.save(data=df, fname=tmp_file_txt.with_suffix(".csv"), export_format="csv")
        assert tmp_file_txt.with_suffix(".csv").exists()

    def test_fail_convert(self, tmp_file_txt: Path) -> None:
        """Test fail conversion.

        Args:
            tmp_file_txt (Path): Path to temporary file.
        """
        file_format = "WRONG"
        with pytest.raises(ValueError) as excinfo:
            DataConverter.convert(tmp_file_txt, file_format)

        assert isinstance(excinfo.value, ValueError)
        assert f"File format '{file_format}' is not supported." in str(excinfo.value)

    def test_fail_convert_export(
        self, reference_dataframe: pd.DataFrame, tmp_file_txt: Path
    ) -> None:
        """Test fail conversion.

        Args:
            reference_dataframe (pd.DataFrame): Reference dataframe.
            tmp_file_txt (Path): Path to temporary file.
        """
        export_format = "WRONG"
        with pytest.raises(ValueError) as excinfo:
            DataConverter().save(reference_dataframe, tmp_file_txt, export_format)

        assert isinstance(excinfo.value, ValueError)
        assert f"Export format '{export_format}' is not supported." in str(
            excinfo.value
        )

    def test_cmd_data_converter(self, script_runner: Any) -> None:
        """Test the data converter plugin."""
        ret = script_runner.run("spectrafit-data-converter", "-h")

        assert ret.success
        assert "Converter for 'SpectraFit' from data files to CSV files." in ret.stdout
        assert ret.stderr == ""

    def test_cmd_data_converter_nor_to_csv(
        self, script_runner: Any, tmp_file_nor: Path
    ) -> None:
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


@pytest.fixture(scope="function", autouse=True, name="tmp_file_dict")
def tmp_file_dict() -> Dict[str, Dict[str, NDArray[Shape["200"], Float]]]:
    """Create temporary file with pickle data."""
    return {
        "level_1": {
            "sub_level_1": np.arange(10),
            "sub_level_2": np.linspace(0, 20, 200),
        },
        "level_2": {
            "sub_level_1": np.arange(10),
            "sub_level_2": np.linspace(0, 20, 200),
        },
        "level_3": {
            "sub_level_1": np.arange(20),
            "sub_level_2": np.linspace(-20, 20, 200),
        },
    }


@pytest.fixture(scope="function", autouse=True, name="tmp_file_nested_dict")
def tmp_file_nested_dict() -> Dict[str, Dict[str, Any]]:
    """Create temporary file with nested pickle data."""
    return {
        "level_4": {
            "sub_level_1": np.arange(10),
            "sub_level_2": {
                "sub_sub_level_1": np.arange(10),
                "sub_sub_level_2": {
                    "sub_sub_sub_level_1": np.linspace(0, 20, 200),
                    "sub_sub_sub_level_2": [
                        np.linspace(0, 20, 200),
                        {"sub_sub_sub_level_3": np.linspace(0, 20, 200)},
                    ],
                    "sub_sub_sub_level_4": [1, 2, 3, 4, 5],
                },
            },
        },
    }


@pytest.fixture(scope="function", autouse=True, name="tmp_pkl_gz_file")
def tmp_pkl_gz_file(
    tmp_path: Path, tmp_file_dict: Dict[str, Dict[str, NDArray[Shape["200"], Float]]]
) -> Path:
    """Create temporary file with pickle data.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file_comp.pkl.gz"
    with gzip.open(tmp_file, "wb") as f:
        pickle.dump(tmp_file_dict, f)
    return tmp_file


@pytest.fixture(scope="function", autouse=True, name="tmp_file_pkl")
def tmp_file_pkl(
    tmp_path: Path, tmp_file_dict: Dict[str, Dict[str, NDArray[Shape["200"], Float]]]
) -> Path:
    """Create temporary file with pickle data.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file.pkl"
    with open(tmp_file, "wb") as f:
        pickle.dump(tmp_file_dict, f)
    return tmp_file


@pytest.fixture(scope="function", autouse=True, name="tmp_file_pkl_gz")
def tmp_file_pkl_gz(
    tmp_path: Path, tmp_file_dict: Dict[str, Dict[str, NDArray[Shape["200"], Float]]]
) -> Path:
    """Create temporary file with pickle data.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file.pkl.gz"
    with gzip.open(tmp_file, "wb") as f:
        pickle.dump(tmp_file_dict, f)
    return tmp_file


@pytest.fixture(scope="function", autouse=True, name="tmp_file_pkl_nested")
def tmp_file_pkl_nested(
    tmp_path: Path, tmp_file_nested_dict: Dict[str, Dict[str, Any]]
) -> Path:
    """Create temporary file with nested pickle data.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Path: Path to temporary file.
    """
    tmp_file = tmp_path / "tmp_file_pkl_nested.pkl"
    with open(tmp_file, "wb") as f:
        pickle.dump(tmp_file_nested_dict, f)
    return tmp_file


class TestPklConverter:
    """Test PklConverter."""

    @pytest.mark.parametrize(
        "export_format",
        ["npy", "npz", "pkl", "pkl.gz"],
    )
    def test_export_data(
        self,
        tmp_path: Path,
        tmp_file_dict: Dict[str, Dict[str, NDArray[Shape["200"], Float]]],
        export_format: str,
    ) -> None:
        """Test export data.

        Args:
            tmp_path (Path): Temporary path.
            tmp_file_dict (Dict[str, Dict[str, np.ndarray]]): Temporary file.
            export_format (str): Export format.
        """
        tmp_file = tmp_path / "tmp_file"
        ExportData(
            data=tmp_file_dict,
            fname=tmp_file,
            export_format=export_format,
        )()
        assert tmp_file.with_suffix(f".{export_format}").exists()

        if export_format == "pkl.gz":
            with gzip.open(tmp_file.with_suffix(f".{export_format}"), "rb") as f:
                data = pickle.load(f)
                assert np.array_equal(data["level_1"]["sub_level_1"], np.arange(10))
                assert np.array_equal(
                    data["level_1"]["sub_level_2"], np.linspace(0, 20, 200)
                )
        if export_format == "pkl":
            with open(tmp_file.with_suffix(f".{export_format}"), "rb") as f:
                data = pickle.load(f)
                assert np.array_equal(data["level_1"]["sub_level_1"], np.arange(10))
                assert np.array_equal(
                    data["level_1"]["sub_level_2"], np.linspace(0, 20, 200)
                )

        if export_format == "npz":
            data = np.load(tmp_file.with_suffix(f".{export_format}"), allow_pickle=True)
            assert isinstance(data, np.lib.npyio.NpzFile)
            assert data.get("data") is not None
            assert isinstance(data.get("data"), np.ndarray)

    def test_numpy2list(
        self,
        tmp_file_dict: Dict[str, Dict[str, NDArray[Shape["200"], Float]]],
    ) -> None:
        """Test numpy2list.

        Args:
            tmp_file_dict (Dict[str, Dict[str, np.ndarray]]): Temporary file.
        """
        conv_data = ExportData.numpy2list(data=list(tmp_file_dict.values()))
        assert isinstance(conv_data, list)
        assert isinstance(conv_data[0], dict)
        assert isinstance(conv_data[0]["sub_level_1"], list)
        assert isinstance(conv_data[0]["sub_level_2"], list)

    @pytest.mark.parametrize(
        "export_format",
        ["npy", "npz", "pkl", "pkl.gz"],
    )
    def test_pkl_converter(self, tmp_file_pkl: Path, export_format: str) -> None:
        """Test pickle converter.

        Args:
            tmp_file_pkl (Path): Path to temporary file.
            export_format (str): Export format.
        """
        converter = PklConverter()
        data = converter.convert(
            tmp_file_pkl,
            file_format="latin1",
        )
        converter.save(data, tmp_file_pkl, export_format=export_format)
        assert isinstance(data, dict)
        assert np.array_equal(data["level_1"][0]["sub_level_1"], np.arange(10))
        assert data.keys() == {"level_1", "level_2", "level_3"}
        assert (
            len(list(Path(tmp_file_pkl.parent).glob(f"*level_*.{export_format}"))) == 3
        )

    @pytest.mark.parametrize(
        "export_format",
        ["npy", "npz", "pkl", "pkl.gz"],
    )
    def test_pkl_gz_converter(self, tmp_file_pkl_gz: Path, export_format: str) -> None:
        """Test pickle converter.

        Args:
            tmp_file_pkl_gz (Path): Path to temporary file.
            export_format (str): Export format.
        """
        converter = PklConverter()
        data = converter.convert(
            tmp_file_pkl_gz,
            file_format="latin1",
        )
        converter.save(data, tmp_file_pkl_gz, export_format=export_format)
        assert isinstance(data, dict)
        assert np.array_equal(data["level_1"][0]["sub_level_1"], np.arange(10))
        assert (
            len(list(Path(tmp_file_pkl_gz.parent).glob(f"*level_*.{export_format}")))
            == 3
        )

    def test_pkl_converter_nested(
        self, tmp_path: Path, tmp_file_nested_dict: Dict[str, Any]
    ) -> None:
        """Test pickle converter for nested dictionaries.

        Args:
            tmp_path (Path): Temporary path.
            tmp_file_nested_dict (Dict[str, Any]): Temporary file.
        """
        converter = PklConverter()
        tmp_file = tmp_path / "tmp_file_nested_dict.pkl"
        with open(tmp_file, "wb") as f:
            pickle.dump(tmp_file_nested_dict, f)
        data = converter.convert(
            tmp_file,
            file_format="latin1",
        )
        converter.save(data, tmp_file, export_format="pkl")
        assert isinstance(data, dict)

    def test_pkl_converter_fail(self, tmp_file_pkl: Path) -> None:
        """Test pickle converter.

        Args:
            tmp_file_pkl (Path): Path to temporary file.
        """
        converter = PklConverter()
        with pytest.raises(ValueError) as excinfo:
            data = converter.convert(
                tmp_file_pkl,
                file_format="latin2",
            )
            converter.save(data, tmp_file_pkl, export_format="not_existing")
        assert "Unsupported file format" in str(excinfo.value)

    @pytest.mark.parametrize(
        "export_format",
        ["npy", "npz", "pkl", "pkl.gz"],
    )
    def test_cmd_pkl_converter(
        self, script_runner: Any, tmp_file_pkl: Path, export_format: str
    ) -> None:
        """Test the data converter plugin.

        Args:
            script_runner (Any): Script runner.
            tmp_file_pkl (Path): Path to temporary file.
            export_format (str): Export format.
        """
        ret = script_runner.run(
            "spectrafit-pkl-converter",
            str(tmp_file_pkl),
            "--export-format",
            export_format,
        )

        assert ret.success
        assert ret.stdout == ""
        assert ret.stderr == ""
        assert (
            len(list(Path(tmp_file_pkl.parent).glob(f"*level_*.{export_format}"))) == 3
        )


class TestPklAsGraph:
    """Test the pkl visualizer."""

    def test_converter(self, tmp_file_pkl: Path, plt: pyplot) -> None:
        """Test the converter.

        Args:
            tmp_file_pkl (Path): Path to temporary file.
            plt (pyplot): Pyplot.
        """
        converter = PklVisualizer()
        data = converter.convert(tmp_file_pkl, file_format="latin1")

        assert isinstance(data, dict)
        plt.show()

    @pytest.mark.parametrize("export_format", ["pdf", "png", "jpg", "jpeg"])
    def test_save(self, tmp_file_pkl: Path, export_format: str) -> None:
        """Test the save function for various export formats.

        Args:
            tmp_file_pkl (Path): Path to temporary file.
            plt (pyplot): Pyplot.
            export_format (str): Export format.
        """
        converter = PklVisualizer()
        data = converter.convert(tmp_file_pkl, file_format="latin1")
        converter.save(data, tmp_file_pkl, export_format=export_format)

        assert Path(
            tmp_file_pkl.parent / f"{tmp_file_pkl.stem}.{export_format}"
        ).exists()
        assert Path(tmp_file_pkl.parent / f"{tmp_file_pkl.stem}.json").exists()

    def test_save_fail(self, tmp_file_pkl: Path) -> None:
        """Test fail save function.

        Args:
            tmp_file_pkl (Path): Path to temporary file.
            plt (pyplot): Pyplot.
            export_format (str): Export format.
        """
        converter = PklVisualizer()
        data = converter.convert(tmp_file_pkl, file_format="latin1")
        with pytest.raises(ValueError) as excinfo:
            converter.save(data, tmp_file_pkl, export_format="not_existing")
        assert "Export format" in str(excinfo.value)

    def test_cmd_converter(self, script_runner: Any, tmp_file_pkl_nested: Path) -> None:
        """Test the data converter plugin.

        Args:
            script_runner (Any): Script runner.
            tmp_file_pkl_nested (Path): Path to temporary file of nested dictionary.
        """
        ret = script_runner.run(
            "spectrafit-pkl-visualizer",
            str(tmp_file_pkl_nested),
            "--export-format",
            "pdf",
        )

        assert ret.success
        assert ret.stdout == ""
        assert ret.stderr == ""
        assert Path(
            tmp_file_pkl_nested.parent / f"{tmp_file_pkl_nested.stem}.pdf"
        ).exists()
        assert Path(
            tmp_file_pkl_nested.parent / f"{tmp_file_pkl_nested.stem}.json"
        ).exists()

    def test_converter_fail(self, tmp_path: Path) -> None:
        """Test fail of the converter.

        Args:
            tmp_path (Path): Temporary path.
        """
        fname = tmp_path / "tmp_not_a_dict.pkl"
        with open(fname, "wb") as f:
            pickle.dump("test", f)
        with pytest.raises(ValueError) as excinfo:
            PklVisualizer.convert(fname, file_format="latin2")
        assert "Data is not a dictionary:" in str(excinfo.value)


@pytest.fixture(scope="function", autouse=True, name="tmp_list_dict_rixs")
def fixture_tmp_list_dict_rixs(
    tmp_path: Path,
) -> Tuple[Path, Tuple[str, str, str]]:
    """Fixture for temporary list of dictionaries.

    Args:
        tmp_path (Path): Temporary path.

    Returns:
        Tuple[Path, Tuple[str, str, str]]: Path to temporary file and keys of the
            list of dictionaries.
    """
    fname = tmp_path / "tmp_list_dict_rixs.pkl"
    inc_eng = np.linspace(0, 10, 11, dtype=np.float32)
    exc_eng = np.linspace(0, 10, 11, dtype=np.float32)
    xx, yy = np.meshgrid(inc_eng, exc_eng)
    rixa_map = np.sin(xx) * np.cos(yy)
    keys = ("inc_eng", "exc_eng", "rixs_map")
    data_list_dict = [
        {
            keys[0]: inc_eng,
            keys[1]: exc_eng,
            keys[2]: rixa_map,
        }
    ]
    with open(fname, "wb") as f:
        pickle.dump(data_list_dict, f)
    return fname, keys


class TestRixsConverter:
    """Test the rixs converter."""

    def test_convertet(
        self, tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]]
    ) -> None:
        """Test the converter.

        Args:
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
        """
        fname, keys = tmp_list_dict_rixs
        converter = RIXSConverter()
        data = converter.convert(fname, file_format="latin1")

        assert isinstance(data, dict)
        assert keys[0] in data
        assert keys[1] in data
        assert keys[2] in data

    @pytest.mark.parametrize("export_format", ["json", "toml", "lock", "npy", "npz"])
    def test_save(
        self,
        tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]],
        export_format: str,
    ) -> None:
        """Test the save function for various export formats.

        Args:
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
            export_format (str): Export format.
        """
        fname, keys = tmp_list_dict_rixs
        converter = RIXSConverter()
        data = converter.convert(fname, file_format="latin1")
        converter.save(data, fname, export_format=export_format)

        assert Path(fname.parent / f"{fname.stem}.{export_format}").exists()

        if export_format == "json":
            with open(fname.parent / f"{fname.stem}.json") as f:
                data_json = json.load(f)
            assert isinstance(data_json, dict)
            assert np.allclose(data_json[keys[0]], data[keys[0]])

        if export_format in {"toml", "lock"}:
            with open(fname.parent / f"{fname.stem}.{export_format}") as f:
                data_toml = toml.load(f)
            assert isinstance(data_toml, dict)
            assert np.allclose(data_toml[keys[0]], data[keys[0]])

        if export_format == "npy":
            data_npy = np.load(fname.parent / f"{fname.stem}.npy", allow_pickle=True)
            assert isinstance(data_npy, np.ndarray)
            assert np.allclose(data_npy.item()[keys[0]], data[keys[0]])

        if export_format == "npz":
            data_npz = np.load(fname.parent / f"{fname.stem}.npz", allow_pickle=True)
            assert isinstance(data_npz, np.lib.npyio.NpzFile)
            assert np.allclose(data_npz[keys[0]], data[keys[0]])

    def test_raise_error_save(
        self, tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]]
    ) -> None:
        """Test the raise error.

        Args:
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
        """
        fname, _ = tmp_list_dict_rixs
        converter = RIXSConverter()
        data = converter.convert(fname, file_format="latin1")
        with pytest.raises(ValueError) as excinfo:
            converter.save(data, fname, export_format="pdf")
        assert "Export format" in str(excinfo.value)

    @pytest.mark.parametrize("mode", ["sum", "mean"])
    def test_create_rixs(
        self, tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]], mode: str
    ) -> None:
        """Test the create rixs.

        Args:
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
            mode (str): Mode for the rixs map.
        """
        fname, keys = tmp_list_dict_rixs
        converter = RIXSConverter()
        data = converter.convert(fname, file_format="latin1")
        rixs_map = converter.create_rixs(data, *keys, mode=mode).dict()

        assert isinstance(rixs_map["rixs_map"], np.ndarray)
        if mode == "mean":
            assert np.allclose(rixs_map["rixs_map"], data[keys[2]].mean(axis=0))
        elif mode == "sum":
            assert np.allclose(rixs_map["rixs_map"], data[keys[2]].sum(axis=0))

    def test_create_rixs_fail_1(
        self, tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]]
    ) -> None:
        """Test the create rixs fail.

        Args:
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
        """
        fname, keys = tmp_list_dict_rixs
        converter = RIXSConverter()
        data = converter.convert(fname, file_format="latin1")

        with pytest.raises(ValueError) as excinfo:
            converter.create_rixs(data, *keys, mode="test")
        assert "Mode" in str(excinfo.value)

    @pytest.mark.parametrize(
        "keys",
        [
            ("wrong_key", "exc_eng", "rixs_map"),
            ("inc_eng", "wrong_key", "rixs_map"),
            ("inc_eng", "exc_eng", "wrong_key"),
        ],
    )
    def test_create_rixs_fail_2(
        self,
        tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]],
        keys: Tuple[str, str, str],
    ) -> None:
        """Test the create rixs fail.

        Args:
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
            keys (Tuple[str, str,str]): Tuple of the three keys, which contains one
                wrong key for each.
        """
        fname, _ = tmp_list_dict_rixs
        converter = RIXSConverter()
        data = converter.convert(fname, file_format="latin1")

        with pytest.raises(KeyError) as excinfo:
            converter.create_rixs(data, *keys, mode="sum")
        assert "Key" in str(excinfo.value)

    @pytest.mark.parametrize(
        "export_format",
        ["npy", "npz", "json", "toml", "lock"],
    )
    def test_cmd_pkl_converter(
        self,
        script_runner: Any,
        tmp_list_dict_rixs: Tuple[Path, Tuple[str, str, str]],
        export_format: str,
    ) -> None:
        """Test the data converter plugin.

        Args:
            script_runner (Any): Script runner.
            tmp_list_dict_rixs (Tuple[Path, Tuple[str, str, str]]): Path to temporary
                file and keys of the list of dictionaries.
            export_format (str): Export format.
        """
        ret = script_runner.run(
            "spectrafit-rixs-converter",
            str(tmp_list_dict_rixs[0]),
            "--export-format",
            export_format,
            "-ie",
            tmp_list_dict_rixs[1][0],
            "-ee",
            tmp_list_dict_rixs[1][1],
            "-rm",
            tmp_list_dict_rixs[1][2],
        )

        assert ret.success
        assert ret.stdout == ""
        assert ret.stderr == ""
        assert Path(
            tmp_list_dict_rixs[0].parent
            / f"{tmp_list_dict_rixs[0].stem}.{export_format}"
        ).exists()

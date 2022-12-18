"""Testing of the command line interface."""
from pathlib import Path
from typing import Any

import pandas as pd

from numpy.testing import assert_almost_equal


class TestCommandLineRunner:
    """Testing the command line interface."""

    def test_version(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing the version command."""
        from spectrafit import __version__

        monkeypatch.setattr("builtins.input", lambda _: "y")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_1.json",
        )

        assert ret.success
        assert f"Currently used version is: {__version__}\n" in ret.stdout
        assert ret.stderr == ""

    def test_extended(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing the extended command."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_2.json",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_extended_verbose(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing the extended with verbose command."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_7.json",
        )
        assert ret.success
        assert ret.stderr == ""


class TestFileFormat:
    """Testing the file formats."""

    def test_json_input(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing json support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_3.json",
            "-o",
            f"{tmp_path}/result_json",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(tmp_path).glob("result_json*.json"))) == 1
        assert len(list(Path(tmp_path).glob("result_json*.csv"))) == 3

    def test_yml_input(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing yml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_3.yml",
            "-o",
            f"{tmp_path}/result_yml",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(tmp_path).glob("result_yml*.json"))) == 1
        assert len(list(Path(tmp_path).glob("result_yml*.csv"))) == 3

    def test_yaml_input(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing yaml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_3.yaml",
            "-o",
            f"{tmp_path}/result_yaml",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(tmp_path).glob("result_yaml*.json"))) == 1
        assert len(list(Path(tmp_path).glob("result_yaml*.csv"))) == 3

    def test_toml_input(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing toml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_3.toml",
            "-o",
            f"{tmp_path}/result_toml",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(tmp_path).glob("result_toml*.json"))) == 1
        assert len(list(Path(tmp_path).glob("result_toml*.csv"))) == 3


class TestFileFormatOutput:
    """Testing the output files and formats."""

    def test_outputs(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing correct number of outputs."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        _ = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_2.json",
        )
        assert (
            len(list(Path(".").glob("spectrafit/test/export/fit_results*.json"))) == 1
        )
        assert len(list(Path(".").glob("spectrafit/test/export/fit_results*.csv"))) == 3


class TestMoreFeatures:
    """Testing more features."""

    def test_default_options(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing verbose support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_4.json",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_energyrange_e0(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing lower energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_5.json",
            "-o",
            f"{tmp_path}/e0_result",
            "-e0",
            "0.0",
        )
        assert ret.success
        assert ret.stderr == ""

        df_test = pd.read_csv(tmp_path / "e0_result_fit.csv")
        assert_almost_equal(df_test["energy"].min(), 0.0, decimal=0)

    def test_energyrange_e1(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing upper energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_5.json",
            "-o",
            f"{tmp_path}/e1_result",
            "--oversampling",
            "-e1",
            "5.0",
        )
        assert ret.success
        assert ret.stderr == ""

        df_test = pd.read_csv(tmp_path / "e1_result_fit.csv")
        assert_almost_equal(df_test["energy"].max(), 5.0, decimal=0)

    def test_energyrange_e0e1(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing lower and upper energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_5.json",
            "-o",
            f"{tmp_path}/e0e1_result",
            "--oversampling",
            "-e0",
            "0",
            "-e1",
            "5.0",
        )
        assert ret.success
        assert ret.stderr == ""

        df_test = pd.read_csv(tmp_path / "e0e1_result_fit.csv")
        assert_almost_equal(df_test["energy"].max(), 5.0, decimal=0)
        assert_almost_equal(df_test["energy"].min(), 0.0, decimal=0)

    def test_all_models(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing test all models of spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_all_models.toml",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_not_allowed_input_1(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing test all models of spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        fname = "spectrafit/test/scripts/test_wrong.pp"
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/import/test_data.csv",
            "-i",
            fname,
        )
        assert not ret.success

        # assert ret.stderr == (
        # f"ERROR: Input file {fname} has not supported file format.\n"
        # "Supported fileformats are: '*.json', '*.yaml', and '*.toml'\n"
        # )

    def test_not_allowed_input_2(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing missing mininizmer parameter in input."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_missing_parameters_1.json",
        )
        assert not ret.success
        # assert ret.stderr == "Missing 'minimizer' in 'parameters'!\n"

    def test_not_allowed_input_3(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing missing optimizer parameter in input."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_missing_parameters_2.json",
        )
        assert not ret.success
        # assert ret.stderr == "Missing key 'optimizer' in 'parameters'!\n"

    def test_no_input(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing no provided input for spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/no_input.pp",
        )
        assert not ret.success

    def test_conf_interval(
        self, monkeypatch: Any, script_runner: Any, tmp_path: Path
    ) -> None:
        """Testing upper energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_6.json",
            "-o",
            f"{tmp_path}/conf_interval_result",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(tmp_path).glob("conf_interval_result*.json"))) == 1

    def test_get_no_errors(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing for no errorbars for spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_8.json",
        )
        assert ret.success

    def test_load_noglobal(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing for no errorbars for spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "_",
            "-i",
            "spectrafit/test/scripts/test_input_8.json",
            "-g",
            "0",
        )
        assert ret.success

    def test_non_numeric_data(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing missing mininizmer parameter in input."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit", "_", "-i", "spectrafit/test/scripts/test_input_9.json"
        )
        assert not ret.success


class TestGlobalFitting:
    """Test class for global fitting."""

    def test_global_fitting_0(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing global fitting."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit", "_", "-i", "spectrafit/test/scripts/test_input_global_0.json"
        )
        assert ret.success
        assert ret.stderr == ""
        assert (
            len(
                list(
                    Path(".").glob("spectrafit/test/export/global_fit_results_0*.json")
                )
            )
            == 1
        )
        assert (
            len(
                list(Path(".").glob("spectrafit/test/export/global_fit_results_0*.csv"))
            )
            == 3
        )

    def test_global_fitting_1(self, monkeypatch: Any, script_runner: Any) -> None:
        """Testing global fitting."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit", "_", "-i", "spectrafit/test/scripts/test_input_global_1.json"
        )
        assert ret.success
        assert ret.stderr == ""
        assert (
            len(
                list(
                    Path(".").glob("spectrafit/test/export/global_fit_results_1*.json")
                )
            )
            == 1
        )
        assert (
            len(
                list(Path(".").glob("spectrafit/test/export/global_fit_results_1*.csv"))
            )
            == 3
        )

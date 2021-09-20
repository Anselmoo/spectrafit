"""Testing of the command line interface."""
from pathlib import Path

import pandas as pd
import pytest

from numpy.testing import assert_almost_equal
from spectrafit import __version__


class TestCommandLineRunner:
    """Testing the command line interface."""

    @pytest.mark.skip("Will be an infinity loop")
    def test_version(self, monkeypatch, script_runner):
        """Testing the version command."""
        monkeypatch.setattr("builtins.input", lambda _: "y")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.txt",
            "-i",
            "spectrafit/test/test_input_1.json",
        )

        assert ret.success
        assert ret.stdout == f"Currently used version is: {__version__}\n"
        assert ret.stderr == ""

    def test_extended(self, monkeypatch, script_runner):
        """Testing the extended command."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.txt",
            "-i",
            "spectrafit/test/test_input_2.json",
        )
        assert ret.success
        assert ret.stderr == ""


class TestFileFormat:
    """Testing the file formats."""

    def test_json_input(self, monkeypatch, script_runner):
        """Testing json support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.json",
            "-o",
            "result_json",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(".").glob("result_json*.json"))) == 1
        assert len(list(Path(".").glob("result_json*.csv"))) == 3

    def test_yml_input(self, monkeypatch, script_runner):
        """Testing yml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.yml",
            "-o",
            "result_yml",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(".").glob("result_yml*.json"))) == 1
        assert len(list(Path(".").glob("result_yml*.csv"))) == 3

    def test_yaml_input(self, monkeypatch, script_runner):
        """Testing yaml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.yaml",
            "-o",
            "result_yaml",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(".").glob("result_yaml*.json"))) == 1
        assert len(list(Path(".").glob("result_yaml*.csv"))) == 3

    def test_toml_input(self, monkeypatch, script_runner):
        """Testing toml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.toml",
            "-o",
            "result_toml",
        )
        assert ret.success
        assert ret.stderr == ""
        assert len(list(Path(".").glob("result_toml*.json"))) == 1
        assert len(list(Path(".").glob("result_toml*.csv"))) == 3


class TestFileFormatOutput:
    """Testing the output files and formats."""

    def test_outputs(self, monkeypatch, script_runner):
        """Testing correct number of outputs."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        _ = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.txt",
            "-i",
            "spectrafit/test/test_input_2.json",
        )
        assert len(list(Path(".").glob("spectrafit/test/fit_results*.json"))) == 1
        assert len(list(Path(".").glob("spectrafit/test/fit_results*.csv"))) == 3


class TestMoreFeatures:
    """Testing more features."""

    def test_default_options(self, monkeypatch, script_runner):
        """Testing verbose support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_4.json",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_energyrange_e0(self, monkeypatch, script_runner):
        """Testing lower energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_5.json",
            "-o",
            "spectrafit/test/e0_result",
            "-e0",
            "0.0",
        )
        assert ret.success
        assert ret.stderr == ""

        df_test = pd.read_csv(Path("./spectrafit/test/e0_result_fit.csv"))
        assert_almost_equal(df_test["energy"].min(), 0.0, decimal=0)

    def test_energyrange_e1(self, monkeypatch, script_runner):
        """Testing upper energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_5.json",
            "-o",
            "spectrafit/test/e1_result",
            "--oversampling",
            "-e1",
            "5.0",
        )
        assert ret.success
        assert ret.stderr == ""

        df_test = pd.read_csv(Path("./spectrafit/test/e1_result_fit.csv"))
        assert_almost_equal(df_test["energy"].max(), 5.0, decimal=0)

    def test_energyrange_e0e1(self, monkeypatch, script_runner):
        """Testing lower and upper energy range cut."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_5.json",
            "-o",
            "spectrafit/test/e0e1_result",
            "--oversampling",
            "-e0",
            "0",
            "-e1",
            "5.0",
        )
        assert ret.success
        assert ret.stderr == ""

        df_test = pd.read_csv(Path("./spectrafit/test/e0e1_result_fit.csv"))
        assert_almost_equal(df_test["energy"].max(), 5.0, decimal=0)
        assert_almost_equal(df_test["energy"].min(), 0.0, decimal=0)

    def test_all_models(self, monkeypatch, script_runner):
        """Testing test all models of spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_all_models.toml",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_not_allowed_input(self, monkeypatch, script_runner):
        """Testing test all models of spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        fname = "spectrafit/test/test_wrong.pp"
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            fname,
        )
        assert not ret.success
        assert ret.stderr == (
            f"ERROR: Input file {fname} has not supported file format.\n"
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'\n"
        )

    def test_no_input(self, monkeypatch, script_runner):
        """Testing test all models of spectrafit."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/no_input.pp",
        )
        assert not ret.success

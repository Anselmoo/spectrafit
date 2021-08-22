"""Testing of the command line interface."""
from pathlib import Path

import pytest

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
        )
        assert ret.success
        assert ret.stderr == ""

    def test_yml_input(self, monkeypatch, script_runner):
        """Testing yml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.yml",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_yaml_input(self, monkeypatch, script_runner):
        """Testing yaml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.yaml",
        )
        assert ret.success
        assert ret.stderr == ""

    def test_toml_input(self, monkeypatch, script_runner):
        """Testing toml support."""
        monkeypatch.setattr("builtins.input", lambda _: "n")
        ret = script_runner.run(
            "spectrafit",
            "spectrafit/test/test_data.csv",
            "-i",
            "spectrafit/test/test_input_3.toml",
        )
        assert ret.success
        assert ret.stderr == ""


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
        assert len(list(Path(".").glob("*.json"))) == 1
        assert len(list(Path(".").glob("*.csv"))) == 3

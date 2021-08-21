"""Testing of the command line interface."""
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

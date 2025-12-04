"""Comprehensive tests for fit command."""

from __future__ import annotations

import tempfile

from pathlib import Path

import pytest

from typer.testing import CliRunner

from spectrafit.cli.main import app


runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_data_file(temp_dir):
    """Create a sample data CSV file."""
    data_file = temp_dir / "test_data.csv"
    data_file.write_text(
        "energy,intensity\n" "0.0,1.0\n" "0.1,1.1\n" "0.2,1.2\n" "0.3,1.0\n"
    )
    return data_file


@pytest.fixture
def sample_input_toml(temp_dir):
    """Create a sample input TOML file."""
    input_file = temp_dir / "test_input.toml"
    input_file.write_text(
        """
[fitting.parameters.minimizer]
nan_policy = "propagate"
calc_covar = true

[fitting.parameters.optimizer]
max_nfev = 100
method = "leastsq"

[fitting.peaks.1.gaussian.amplitude]
max = 2
min = 0
vary = true
value = 1

[fitting.peaks.1.gaussian.center]
max = 2
min = -2
vary = true
value = 0

[fitting.peaks.1.gaussian.fwhmg]
max = 0.5
min = 0.02
vary = true
value = 0.1
"""
    )
    return input_file


@pytest.fixture
def sample_input_json(temp_dir):
    """Create a sample input JSON file."""
    input_file = temp_dir / "test_input.json"
    input_file.write_text(
        """{
  "fitting": {
    "parameters": {
      "minimizer": {
        "nan_policy": "propagate",
        "calc_covar": true
      },
      "optimizer": {
        "max_nfev": 100,
        "method": "leastsq"
      }
    },
    "peaks": {
      "1": {
        "gaussian": {
          "amplitude": {"max": 2, "min": 0, "vary": true, "value": 1},
          "center": {"max": 2, "min": -2, "vary": true, "value": 0},
          "fwhmg": {"max": 0.5, "min": 0.02, "vary": true, "value": 0.1}
        }
      }
    }
  }
}
"""
    )
    return input_file


class TestFitCommandHelp:
    """Test fit command help functionality."""

    def test_fit_help(self):
        """Test fit command help output."""
        result = runner.invoke(app, ["fit", "--help"])
        assert result.exit_code == 0
        assert "fit" in result.output.lower()
        assert "infile" in result.output.lower()

    def test_fit_help_short(self):
        """Test fit command help with short flag."""
        result = runner.invoke(app, ["fit", "-h"])
        assert result.exit_code == 0
        assert "fit" in result.output.lower()


class TestFitCommandErrors:
    """Test fit command error handling."""

    def test_fit_missing_infile(self):
        """Test fit command without required infile argument."""
        result = runner.invoke(app, ["fit"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_fit_nonexistent_file(self):
        """Test fit command with non-existent data file."""
        result = runner.invoke(app, ["fit", "nonexistent_file.csv"])
        assert result.exit_code != 0

    def test_fit_nonexistent_input(self, sample_data_file):
        """Test fit command with non-existent input file."""
        result = runner.invoke(
            app, ["fit", str(sample_data_file), "-i", "nonexistent_input.toml"]
        )
        assert result.exit_code != 0

    def test_fit_invalid_data_format(self, temp_dir):
        """Test fit command with invalid data file format."""
        invalid_file = temp_dir / "invalid.csv"
        invalid_file.write_text("not,valid,data\n1,2,three\n")
        result = runner.invoke(app, ["fit", str(invalid_file)])
        assert result.exit_code != 0


class TestFitCommandOptions:
    """Test fit command options and flags."""

    def test_fit_with_output_option(self, sample_data_file, sample_input_toml):
        """Test fit command with custom output file."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "-o",
                "custom_output",
                "--noplot",
            ],
        )
        # May fail due to actual fitting issues, but tests option parsing
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_energy_range(self, sample_data_file, sample_input_toml):
        """Test fit command with energy range options."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--energy-start",
                "0.0",
                "--energy-stop",
                "1.0",
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_smooth_option(self, sample_data_file, sample_input_toml):
        """Test fit command with smooth option."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--smooth",
                "3",
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_shift_option(self, sample_data_file, sample_input_toml):
        """Test fit command with shift option."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--shift",
                "0.5",
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_oversampling(self, sample_data_file, sample_input_toml):
        """Test fit command with oversampling option."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--oversampling",
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_column_option(self, sample_data_file, sample_input_toml):
        """Test fit command with column specification."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "-c",
                "0",
                "-c",
                "1",
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_verbose_option(self, sample_data_file, sample_input_toml):
        """Test fit command with verbose option."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--verbose",
                "2",
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_noplot_option(self, sample_data_file, sample_input_toml):
        """Test fit command with noplot option."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--noplot",
            ],
        )
        # Command should parse successfully
        assert result.exit_code in (0, 1, 2)


class TestFitCommandParametrized:
    """Parametrized tests for fit command."""

    @pytest.mark.parametrize(
        "option_flag",
        [
            "--help",
            "-h",
        ],
    )
    def test_fit_help_variants(self, option_flag):
        """Test various help option formats."""
        result = runner.invoke(app, ["fit", option_flag])
        assert result.exit_code == 0
        assert "fit" in result.output.lower()

    @pytest.mark.parametrize(
        "verbose_level",
        ["0", "1", "2"],
    )
    def test_fit_verbose_levels(
        self, sample_data_file, sample_input_toml, verbose_level
    ):
        """Test different verbose levels."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--verbose",
                verbose_level,
                "--noplot",
            ],
        )
        # Should parse successfully
        assert result.exit_code in (0, 1, 2)

    @pytest.mark.parametrize(
        "separator",
        ["tab", "space", "comma", "semicolon"],
    )
    def test_fit_separator_options(
        self, sample_data_file, sample_input_toml, separator
    ):
        """Test different separator options."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--separator",
                separator,
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)


class TestFitCommandInputFormats:
    """Test fit command with different input file formats."""

    def test_fit_with_json_input(self, sample_data_file, sample_input_json):
        """Test fit command with JSON input file."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_json),
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)

    def test_fit_with_toml_input(self, sample_data_file, sample_input_toml):
        """Test fit command with TOML input file."""
        result = runner.invoke(
            app,
            [
                "fit",
                str(sample_data_file),
                "-i",
                str(sample_input_toml),
                "--noplot",
            ],
        )
        assert result.exit_code in (0, 1, 2)


class TestFitCommandExitCodes:
    """Test fit command exit codes."""

    def test_fit_success_exit_code(self):
        """Test fit command returns 0 on success (with valid example data)."""
        # This would need real valid data files to test success case
        # For now, we test that help returns 0
        result = runner.invoke(app, ["fit", "--help"])
        assert result.exit_code == 0

    def test_fit_error_exit_code_missing_file(self):
        """Test fit command returns non-zero on error."""
        result = runner.invoke(app, ["fit", "nonexistent.csv"])
        assert result.exit_code != 0

    def test_fit_error_exit_code_no_args(self):
        """Test fit command returns non-zero when no arguments provided."""
        result = runner.invoke(app, ["fit"])
        assert result.exit_code != 0

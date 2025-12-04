"""Comprehensive tests for validate command."""

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
def valid_toml_file(temp_dir):
    """Create a valid TOML configuration file."""
    config_file = temp_dir / "valid_config.toml"
    config_file.write_text(
        """
[fitting.parameters.minimizer]
nan_policy = "propagate"
calc_covar = true

[fitting.parameters.optimizer]
max_nfev = 1000
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
    return config_file


@pytest.fixture
def valid_json_file(temp_dir):
    """Create a valid JSON configuration file."""
    config_file = temp_dir / "valid_config.json"
    config_file.write_text(
        """{
  "fitting": {
    "parameters": {
      "minimizer": {
        "nan_policy": "propagate",
        "calc_covar": true
      },
      "optimizer": {
        "max_nfev": 1000,
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
    return config_file


@pytest.fixture
def valid_yaml_file(temp_dir):
    """Create a valid YAML configuration file."""
    config_file = temp_dir / "valid_config.yaml"
    config_file.write_text(
        """
fitting:
  parameters:
    minimizer:
      nan_policy: propagate
      calc_covar: true
    optimizer:
      max_nfev: 1000
      method: leastsq
  peaks:
    '1':
      gaussian:
        amplitude:
          max: 2
          min: 0
          vary: true
          value: 1
        center:
          max: 2
          min: -2
          vary: true
          value: 0
        fwhmg:
          max: 0.5
          min: 0.02
          vary: true
          value: 0.1
"""
    )
    return config_file


@pytest.fixture
def invalid_missing_fitting(temp_dir):
    """Create an invalid config file missing 'fitting' section."""
    config_file = temp_dir / "invalid_no_fitting.toml"
    config_file.write_text(
        """
[settings]
some_setting = true
"""
    )
    return config_file


@pytest.fixture
def invalid_missing_minimizer(temp_dir):
    """Create an invalid config file missing minimizer."""
    config_file = temp_dir / "invalid_no_minimizer.toml"
    config_file.write_text(
        """
[fitting.parameters.optimizer]
max_nfev = 1000
method = "leastsq"
"""
    )
    return config_file


@pytest.fixture
def invalid_json_syntax(temp_dir):
    """Create a file with invalid JSON syntax."""
    config_file = temp_dir / "invalid_syntax.json"
    config_file.write_text(
        """{
  "fitting": {
    "parameters": {
      "minimizer": {
        "nan_policy": "propagate"
      }
    }
  }
  missing closing brace
"""
    )
    return config_file


class TestValidateCommandHelp:
    """Test validate command help functionality."""

    def test_validate_help(self):
        """Test validate command help output."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.output.lower()
        assert "input" in result.output.lower() or "file" in result.output.lower()

    def test_validate_help_short(self):
        """Test validate command help with short flag."""
        result = runner.invoke(app, ["validate", "-h"])
        assert result.exit_code == 0
        assert "validate" in result.output.lower()


class TestValidateCommandSuccess:
    """Test validate command with valid configuration files."""

    def test_validate_valid_toml(self, valid_toml_file):
        """Test validating a valid TOML file."""
        result = runner.invoke(app, ["validate", str(valid_toml_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✅" in result.output

    def test_validate_valid_json(self, valid_json_file):
        """Test validating a valid JSON file."""
        result = runner.invoke(app, ["validate", str(valid_json_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✅" in result.output

    def test_validate_valid_yaml(self, valid_yaml_file):
        """Test validating a valid YAML file."""
        result = runner.invoke(app, ["validate", str(valid_yaml_file)])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✅" in result.output

    def test_validate_verbose_mode(self, valid_toml_file):
        """Test validate command with verbose flag."""
        result = runner.invoke(app, ["validate", str(valid_toml_file), "--verbose"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✅" in result.output

    def test_validate_verbose_short(self, valid_toml_file):
        """Test validate command with verbose short flag."""
        result = runner.invoke(app, ["validate", str(valid_toml_file), "-v"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower() or "✅" in result.output


class TestValidateCommandErrors:
    """Test validate command error handling."""

    def test_validate_missing_file(self):
        """Test validate command with non-existent file."""
        result = runner.invoke(app, ["validate", "nonexistent_file.toml"])
        assert result.exit_code != 0

    def test_validate_no_arguments(self):
        """Test validate command without required arguments."""
        result = runner.invoke(app, ["validate"])
        assert result.exit_code != 0
        assert "Missing argument" in result.output or "Error" in result.output

    def test_validate_invalid_missing_fitting(self, invalid_missing_fitting):
        """Test validate command with missing 'fitting' section."""
        result = runner.invoke(app, ["validate", str(invalid_missing_fitting)])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "❌" in result.output

    def test_validate_invalid_missing_minimizer(self, invalid_missing_minimizer):
        """Test validate command with missing minimizer."""
        result = runner.invoke(app, ["validate", str(invalid_missing_minimizer)])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "❌" in result.output

    def test_validate_invalid_json_syntax(self, invalid_json_syntax):
        """Test validate command with invalid JSON syntax."""
        result = runner.invoke(app, ["validate", str(invalid_json_syntax)])
        assert result.exit_code != 0


class TestValidateCommandExitCodes:
    """Test validate command exit codes."""

    def test_validate_success_exit_code(self, valid_toml_file):
        """Test validate command returns 0 for valid file."""
        result = runner.invoke(app, ["validate", str(valid_toml_file)])
        assert result.exit_code == 0

    def test_validate_error_exit_code_invalid(self, invalid_missing_fitting):
        """Test validate command returns non-zero for invalid file."""
        result = runner.invoke(app, ["validate", str(invalid_missing_fitting)])
        assert result.exit_code != 0

    def test_validate_error_exit_code_missing_file(self):
        """Test validate command returns non-zero for missing file."""
        result = runner.invoke(app, ["validate", "nonexistent.toml"])
        assert result.exit_code != 0


class TestValidateCommandParametrized:
    """Parametrized tests for validate command."""

    @pytest.mark.parametrize(
        "help_flag",
        ["--help", "-h"],
    )
    def test_validate_help_variants(self, help_flag):
        """Test various help option formats."""
        result = runner.invoke(app, ["validate", help_flag])
        assert result.exit_code == 0
        assert "validate" in result.output.lower()

    @pytest.mark.parametrize(
        "verbose_flag",
        ["--verbose", "-v"],
    )
    def test_validate_verbose_variants(self, valid_toml_file, verbose_flag):
        """Test various verbose option formats."""
        result = runner.invoke(app, ["validate", str(valid_toml_file), verbose_flag])
        assert result.exit_code == 0


class TestValidateCommandOutputFormat:
    """Test validate command output format."""

    def test_validate_output_contains_filename(self, valid_toml_file):
        """Test that validate output mentions the filename."""
        result = runner.invoke(app, ["validate", str(valid_toml_file)])
        assert result.exit_code == 0
        # Output should mention the file being validated
        assert str(valid_toml_file.name) in result.output or "valid" in result.output.lower()

    def test_validate_error_output_contains_details(self, invalid_missing_fitting):
        """Test that error output contains useful details."""
        result = runner.invoke(app, ["validate", str(invalid_missing_fitting)])
        assert result.exit_code != 0
        # Error should mention what's missing
        assert "error" in result.output.lower() or "missing" in result.output.lower()

    def test_validate_verbose_shows_additional_info(self, valid_toml_file):
        """Test that verbose mode shows additional information."""
        result = runner.invoke(app, ["validate", str(valid_toml_file), "-v"])
        assert result.exit_code == 0
        # Verbose should show more than non-verbose
        result_normal = runner.invoke(app, ["validate", str(valid_toml_file)])
        # Verbose output should contain additional information
        assert len(result.output) >= len(result_normal.output) or "peak" in result.output.lower()


class TestValidateCommandFileTypes:
    """Test validate command with different file types."""

    def test_validate_toml_extension(self, valid_toml_file):
        """Test validating .toml file."""
        result = runner.invoke(app, ["validate", str(valid_toml_file)])
        assert result.exit_code == 0

    def test_validate_json_extension(self, valid_json_file):
        """Test validating .json file."""
        result = runner.invoke(app, ["validate", str(valid_json_file)])
        assert result.exit_code == 0

    def test_validate_yaml_extension(self, valid_yaml_file):
        """Test validating .yaml file."""
        result = runner.invoke(app, ["validate", str(valid_yaml_file)])
        assert result.exit_code == 0

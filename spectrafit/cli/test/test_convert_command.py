"""Comprehensive tests for convert command."""

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
def sample_json_config(temp_dir):
    """Create a sample JSON configuration file."""
    config_file = temp_dir / "config.json"
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
          "amplitude": {"max": 2, "min": 0, "vary": true, "value": 1}
        }
      }
    }
  }
}
"""
    )
    return config_file


@pytest.fixture
def sample_toml_config(temp_dir):
    """Create a sample TOML configuration file."""
    config_file = temp_dir / "config.toml"
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
"""
    )
    return config_file


@pytest.fixture
def sample_yaml_config(temp_dir):
    """Create a sample YAML configuration file."""
    config_file = temp_dir / "config.yaml"
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
"""
    )
    return config_file


class TestConvertCommandHelp:
    """Test convert command help functionality."""

    def test_convert_help(self):
        """Test convert command help output."""
        result = runner.invoke(app, ["convert", "--help"])
        assert result.exit_code == 0
        assert "convert" in result.output.lower()
        assert "format" in result.output.lower()

    def test_convert_help_short(self):
        """Test convert command help with short flag."""
        result = runner.invoke(app, ["convert", "-h"])
        assert result.exit_code == 0
        assert "convert" in result.output.lower()


class TestConvertCommandSuccess:
    """Test convert command with valid conversions."""

    def test_convert_json_to_toml(self, sample_json_config, temp_dir):
        """Test converting JSON to TOML."""
        output_file = temp_dir / "output.toml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output
        assert output_file.exists()

    def test_convert_json_to_yaml(self, sample_json_config, temp_dir):
        """Test converting JSON to YAML."""
        output_file = temp_dir / "output.yaml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "yaml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output
        assert output_file.exists()

    def test_convert_toml_to_json(self, sample_toml_config, temp_dir):
        """Test converting TOML to JSON."""
        output_file = temp_dir / "output.json"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_toml_config),
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output
        assert output_file.exists()

    def test_convert_toml_to_yaml(self, sample_toml_config, temp_dir):
        """Test converting TOML to YAML."""
        output_file = temp_dir / "output.yaml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_toml_config),
                "--format",
                "yaml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output
        assert output_file.exists()

    def test_convert_yaml_to_json(self, sample_yaml_config, temp_dir):
        """Test converting YAML to JSON."""
        output_file = temp_dir / "output.json"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_yaml_config),
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output
        assert output_file.exists()

    def test_convert_yaml_to_toml(self, sample_yaml_config, temp_dir):
        """Test converting YAML to TOML."""
        output_file = temp_dir / "output.toml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_yaml_config),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output
        assert output_file.exists()


class TestConvertCommandDefaultBehavior:
    """Test convert command default behavior."""

    def test_convert_default_format_toml(self, sample_json_config):
        """Test that default format is TOML."""
        result = runner.invoke(app, ["convert", str(sample_json_config)])
        # Should create a .toml file with same base name
        assert result.exit_code == 0

    def test_convert_auto_output_filename(self, sample_json_config):
        """Test that output filename is automatically generated."""
        result = runner.invoke(
            app, ["convert", str(sample_json_config), "--format", "yaml"]
        )
        assert result.exit_code == 0
        # Should mention the output file in the message
        assert "yaml" in result.output.lower() or ".yaml" in result.output


class TestConvertCommandErrors:
    """Test convert command error handling."""

    def test_convert_missing_file(self):
        """Test convert command with non-existent file."""
        result = runner.invoke(app, ["convert", "nonexistent_file.json"])
        assert result.exit_code != 0

    def test_convert_no_arguments(self):
        """Test convert command without required arguments."""
        result = runner.invoke(app, ["convert"])
        assert result.exit_code != 0

    def test_convert_output_exists_without_force(self, sample_json_config, temp_dir):
        """Test that convert fails if output exists without --force."""
        output_file = temp_dir / "existing.toml"
        output_file.write_text("[existing]\ndata = true\n")

        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code != 0
        assert "exists" in result.output.lower() or "force" in result.output.lower()

    def test_convert_same_input_output(self, sample_json_config):
        """Test that convert fails if input and output are the same."""
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "json",
                "--output",
                str(sample_json_config),
            ],
        )
        assert result.exit_code != 0
        # Will fail with "exists" error since it checks existence first
        output_lower = result.output.lower()
        assert "same" in output_lower or "cannot" in output_lower or "exists" in output_lower


class TestConvertCommandForceOption:
    """Test convert command --force option."""

    def test_convert_force_overwrite(self, sample_json_config, temp_dir):
        """Test that --force allows overwriting existing files."""
        output_file = temp_dir / "existing.toml"
        output_file.write_text("[existing]\ndata = true\n")

        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "toml",
                "--output",
                str(output_file),
                "--force",
            ],
        )
        assert result.exit_code == 0
        assert "success" in result.output.lower() or "✅" in result.output


class TestConvertCommandExitCodes:
    """Test convert command exit codes."""

    def test_convert_success_exit_code(self, sample_json_config, temp_dir):
        """Test convert command returns 0 on success."""
        output_file = temp_dir / "output.toml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    def test_convert_error_exit_code_missing_file(self):
        """Test convert command returns non-zero for missing file."""
        result = runner.invoke(app, ["convert", "nonexistent.json"])
        assert result.exit_code != 0

    def test_convert_error_exit_code_no_args(self):
        """Test convert command returns non-zero when no arguments provided."""
        result = runner.invoke(app, ["convert"])
        assert result.exit_code != 0


class TestConvertCommandParametrized:
    """Parametrized tests for convert command."""

    @pytest.mark.parametrize(
        "help_flag",
        ["--help", "-h"],
    )
    def test_convert_help_variants(self, help_flag):
        """Test various help option formats."""
        result = runner.invoke(app, ["convert", help_flag])
        assert result.exit_code == 0
        assert "convert" in result.output.lower()

    @pytest.mark.parametrize(
        "output_format",
        ["json", "yaml", "toml"],
    )
    def test_convert_format_options(self, sample_json_config, temp_dir, output_format):
        """Test different output format options."""
        output_file = temp_dir / f"output.{output_format}"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                output_format,
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()

    @pytest.mark.parametrize(
        "format_flag",
        ["--format", "-f"],
    )
    def test_convert_format_flag_variants(
        self, sample_json_config, temp_dir, format_flag
    ):
        """Test various format flag options."""
        output_file = temp_dir / "output.yaml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                format_flag,
                "yaml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "output_flag",
        ["--output", "-o"],
    )
    def test_convert_output_flag_variants(
        self, sample_json_config, temp_dir, output_flag
    ):
        """Test various output flag options."""
        output_file = temp_dir / "output.toml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "toml",
                output_flag,
                str(output_file),
            ],
        )
        assert result.exit_code == 0


class TestConvertCommandOutputFormat:
    """Test convert command output format."""

    def test_convert_output_shows_conversion_info(self, sample_json_config, temp_dir):
        """Test that output shows conversion information."""
        output_file = temp_dir / "output.toml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        # Output should mention both input and output
        assert (
            sample_json_config.name in result.output
            or output_file.name in result.output
        )

    def test_convert_output_mentions_formats(self, sample_json_config, temp_dir):
        """Test that output mentions the conversion formats."""
        output_file = temp_dir / "output.yaml"
        result = runner.invoke(
            app,
            [
                "convert",
                str(sample_json_config),
                "--format",
                "yaml",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        # Output should mention format conversion
        output_lower = result.output.lower()
        assert "yaml" in output_lower or "json" in output_lower

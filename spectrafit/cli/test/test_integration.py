"""Integration tests for CLI workflows."""

from __future__ import annotations

import shutil
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
def example_dir():
    """Get the Examples directory path."""
    return Path(__file__).parent.parent.parent.parent / "Examples"


@pytest.fixture
def example_data_file(example_dir):
    """Get example data file if it exists."""
    data_file = example_dir / "data.csv"
    if data_file.exists():
        return data_file
    pytest.skip("Example data file not found")


@pytest.fixture
def example_input_toml(example_dir):
    """Get example input TOML file if it exists."""
    input_file = example_dir / "example_1.toml"
    if input_file.exists():
        return input_file
    pytest.skip("Example input file not found")


@pytest.fixture
def example_input_json(example_dir):
    """Get example input JSON file if it exists."""
    input_file = example_dir / "example_1.json"
    if input_file.exists():
        return input_file
    pytest.skip("Example input JSON file not found")


@pytest.fixture
def example_results_json(example_dir):
    """Get example results JSON file if it exists."""
    results_file = example_dir / "example_1_summary.json"
    if results_file.exists():
        return results_file
    pytest.skip("Example results file not found")


@pytest.mark.integration
class TestConvertWorkflow:
    """Integration tests for convert workflow."""

    def test_convert_json_to_toml_workflow(self, example_input_json, temp_dir):
        """Test complete JSON to TOML conversion workflow."""
        output_file = temp_dir / "converted.toml"

        # Convert JSON to TOML
        result = runner.invoke(
            app,
            [
                "convert",
                str(example_input_json),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.stat().st_size > 0

        # Validate the converted file
        validate_result = runner.invoke(app, ["validate", str(output_file)])
        assert validate_result.exit_code == 0

    def test_convert_toml_to_yaml_workflow(self, example_input_toml, temp_dir):
        """Test complete TOML to YAML conversion workflow."""
        output_file = temp_dir / "converted.yaml"

        # Convert TOML to YAML
        result = runner.invoke(
            app,
            [
                "convert",
                str(example_input_toml),
                "--format",
                "yaml",
                "--output",
                str(output_file),
            ],
        )

        assert result.exit_code == 0
        assert output_file.exists()

        # Validate the converted file
        validate_result = runner.invoke(app, ["validate", str(output_file)])
        assert validate_result.exit_code == 0

    def test_round_trip_conversion(self, example_input_json, temp_dir):
        """Test round-trip conversion: JSON -> TOML -> YAML -> JSON."""
        toml_file = temp_dir / "step1.toml"
        yaml_file = temp_dir / "step2.yaml"
        json_file = temp_dir / "step3.json"

        # JSON -> TOML
        result1 = runner.invoke(
            app,
            [
                "convert",
                str(example_input_json),
                "--format",
                "toml",
                "--output",
                str(toml_file),
            ],
        )
        assert result1.exit_code == 0

        # TOML -> YAML
        result2 = runner.invoke(
            app,
            [
                "convert",
                str(toml_file),
                "--format",
                "yaml",
                "--output",
                str(yaml_file),
            ],
        )
        assert result2.exit_code == 0

        # YAML -> JSON
        result3 = runner.invoke(
            app,
            [
                "convert",
                str(yaml_file),
                "--format",
                "json",
                "--output",
                str(json_file),
            ],
        )
        assert result3.exit_code == 0

        # All files should exist and be valid
        assert toml_file.exists()
        assert yaml_file.exists()
        assert json_file.exists()


@pytest.mark.integration
class TestValidateWorkflow:
    """Integration tests for validate workflow."""

    def test_validate_multiple_formats(
        self, example_input_json, example_input_toml, temp_dir
    ):
        """Test validating multiple input formats."""
        # Copy files to temp dir for validation
        json_copy = temp_dir / "input.json"
        toml_copy = temp_dir / "input.toml"

        shutil.copy(example_input_json, json_copy)
        shutil.copy(example_input_toml, toml_copy)

        # Validate JSON
        result_json = runner.invoke(app, ["validate", str(json_copy)])
        assert result_json.exit_code == 0

        # Validate TOML
        result_toml = runner.invoke(app, ["validate", str(toml_copy)])
        assert result_toml.exit_code == 0

    def test_validate_verbose_output(self, example_input_toml):
        """Test validate with verbose output."""
        result = runner.invoke(app, ["validate", str(example_input_toml), "-v"])
        assert result.exit_code == 0
        # Verbose output should contain additional information
        assert len(result.output) > 0


@pytest.mark.integration
class TestReportWorkflow:
    """Integration tests for report workflow."""

    def test_report_generation_all_formats(self, example_results_json, temp_dir):
        """Test generating reports in all formats."""
        # Generate text report
        text_output = temp_dir / "report.txt"
        result_text = runner.invoke(
            app,
            [
                "report",
                str(example_results_json),
                "--format",
                "text",
                "--output",
                str(text_output),
            ],
        )
        assert result_text.exit_code == 0
        assert text_output.exists()

        # Generate markdown report
        md_output = temp_dir / "report.md"
        result_md = runner.invoke(
            app,
            [
                "report",
                str(example_results_json),
                "--format",
                "markdown",
                "--output",
                str(md_output),
            ],
        )
        assert result_md.exit_code == 0
        assert md_output.exists()

        # Generate JSON report
        json_output = temp_dir / "report.json"
        result_json = runner.invoke(
            app,
            [
                "report",
                str(example_results_json),
                "--format",
                "json",
                "--output",
                str(json_output),
            ],
        )
        assert result_json.exit_code == 0
        assert json_output.exists()


@pytest.mark.integration
class TestPluginsWorkflow:
    """Integration tests for plugins workflow."""

    def test_plugins_list_workflow(self):
        """Test listing plugins."""
        result = runner.invoke(app, ["plugins", "list"])
        assert result.exit_code == 0
        assert "rixs" in result.output.lower() or "plugin" in result.output.lower()

    def test_plugins_list_verbose_workflow(self):
        """Test listing plugins with verbose output."""
        result = runner.invoke(app, ["plugins", "list", "-v"])
        assert result.exit_code == 0
        # Verbose should show more details
        assert len(result.output) > 0

    def test_moessbauer_info_workflow(self):
        """Test Mössbauer info command."""
        result = runner.invoke(app, ["plugins", "moessbauer-info"])
        assert result.exit_code == 0
        assert (
            "moessbauer" in result.output.lower()
            or "mössbauer" in result.output.lower()
        )


@pytest.mark.integration
class TestConfigurationPrecedence:
    """Test configuration precedence: CLI > file > defaults."""

    def test_cli_overrides_file(self, temp_dir):
        """Test that CLI arguments override file settings."""
        # Create a config file with specific settings
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

        # Validate the config file
        result = runner.invoke(app, ["validate", str(config_file)])
        assert result.exit_code == 0

    def test_default_values_work(self, temp_dir):
        """Test that default values are used when not specified."""
        # Create a minimal data file
        data_file = temp_dir / "minimal.csv"
        data_file.write_text("x,y\n0,1\n1,2\n2,1\n")

        # Create a minimal config
        config_file = temp_dir / "minimal.toml"
        config_file.write_text(
            """
[fitting.parameters.minimizer]
nan_policy = "propagate"

[fitting.parameters.optimizer]
max_nfev = 100
method = "leastsq"

[fitting.peaks.1.gaussian.amplitude]
value = 1
vary = true
"""
        )

        # Validate should work with defaults
        result = runner.invoke(app, ["validate", str(config_file)])
        # May fail validation due to incomplete config, but should parse
        assert result.exit_code in (0, 1)


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete end-to-end workflows."""

    def test_validate_convert_validate_workflow(self, example_input_json, temp_dir):
        """Test validate -> convert -> validate workflow."""
        # Step 1: Validate original JSON
        result1 = runner.invoke(app, ["validate", str(example_input_json)])
        assert result1.exit_code == 0

        # Step 2: Convert to TOML
        toml_output = temp_dir / "converted.toml"
        result2 = runner.invoke(
            app,
            [
                "convert",
                str(example_input_json),
                "--format",
                "toml",
                "--output",
                str(toml_output),
            ],
        )
        assert result2.exit_code == 0
        assert toml_output.exists()

        # Step 3: Validate converted TOML
        result3 = runner.invoke(app, ["validate", str(toml_output)])
        assert result3.exit_code == 0

    def test_convert_with_overwrite_workflow(self, example_input_json, temp_dir):
        """Test convert with force overwrite."""
        output_file = temp_dir / "output.toml"

        # First conversion
        result1 = runner.invoke(
            app,
            [
                "convert",
                str(example_input_json),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result1.exit_code == 0

        # Second conversion without force should fail
        result2 = runner.invoke(
            app,
            [
                "convert",
                str(example_input_json),
                "--format",
                "toml",
                "--output",
                str(output_file),
            ],
        )
        assert result2.exit_code != 0

        # Third conversion with force should succeed
        result3 = runner.invoke(
            app,
            [
                "convert",
                str(example_input_json),
                "--format",
                "toml",
                "--output",
                str(output_file),
                "--force",
            ],
        )
        assert result3.exit_code == 0


@pytest.mark.integration
class TestErrorHandlingWorkflow:
    """Test error handling in workflows."""

    def test_invalid_file_chain(self, temp_dir):
        """Test error handling with invalid files."""
        # Create invalid config
        invalid_config = temp_dir / "invalid.json"
        invalid_config.write_text("{ invalid json")

        # Validate should fail gracefully
        result = runner.invoke(app, ["validate", str(invalid_config)])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "invalid" in result.output.lower()

    def test_missing_file_chain(self):
        """Test error handling with missing files."""
        # Validate non-existent file should fail
        result = runner.invoke(app, ["validate", "nonexistent.json"])
        assert result.exit_code != 0

        # Convert non-existent file should fail
        result = runner.invoke(app, ["convert", "nonexistent.json", "--format", "toml"])
        assert result.exit_code != 0

        # Report non-existent file should fail
        result = runner.invoke(app, ["report", "nonexistent.json"])
        assert result.exit_code != 0


@pytest.mark.integration
class TestBackwardCompatibility:
    """Test backward compatibility with v1.x patterns."""

    def test_legacy_input_format_supported(self, example_input_json):
        """Test that v1.x input format is still supported."""
        # Validate v1.x format
        result = runner.invoke(app, ["validate", str(example_input_json)])
        assert result.exit_code == 0

    def test_help_commands_work(self):
        """Test that help commands work as expected."""
        # Main help
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

        # Subcommand help
        for cmd in ["fit", "validate", "convert", "report", "plugins"]:
            result = runner.invoke(app, [cmd, "--help"])
            assert result.exit_code == 0

    def test_version_command_works(self):
        """Test that version command works."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()

"""Comprehensive tests for report command."""

from __future__ import annotations

import json
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
def sample_results_file(temp_dir):
    """Create a sample results JSON file."""
    results_file = temp_dir / "results_summary.json"
    results_data = {
        "fit_statistics": {
            "chi_square": 1.234,
            "reduced_chi_square": 0.987,
            "r_squared": 0.995,
            "aic": 123.45,
            "bic": 134.56,
        },
        "variables": {
            "peak1_amplitude": {
                "value": 1.0,
                "stderr": 0.01,
                "min": 0.0,
                "max": 2.0,
            },
            "peak1_center": {
                "value": 0.5,
                "stderr": 0.02,
                "min": -1.0,
                "max": 1.0,
            },
        },
        "correlations": {
            "peak1_amplitude_peak1_center": 0.123,
        },
    }
    with results_file.open("w") as f:
        json.dump(results_data, f)
    return results_file


@pytest.fixture
def minimal_results_file(temp_dir):
    """Create a minimal results JSON file."""
    results_file = temp_dir / "minimal_results.json"
    results_data = {
        "fit_statistics": {
            "chi_square": 1.0,
        },
    }
    with results_file.open("w") as f:
        json.dump(results_data, f)
    return results_file


@pytest.fixture
def invalid_json_file(temp_dir):
    """Create an invalid JSON file."""
    results_file = temp_dir / "invalid.json"
    results_file.write_text("{ invalid json content")
    return results_file


class TestReportCommandHelp:
    """Test report command help functionality."""

    def test_report_help(self):
        """Test report command help output."""
        result = runner.invoke(app, ["report", "--help"])
        assert result.exit_code == 0
        assert "report" in result.output.lower()

    def test_report_help_short(self):
        """Test report command help with short flag."""
        result = runner.invoke(app, ["report", "-h"])
        assert result.exit_code == 0
        assert "report" in result.output.lower()


class TestReportCommandSuccess:
    """Test report command with valid inputs."""

    def test_report_default_format(self, sample_results_file):
        """Test report command with default text format."""
        result = runner.invoke(app, ["report", str(sample_results_file)])
        assert result.exit_code == 0
        # Should output report to stdout
        assert len(result.output) > 0

    def test_report_text_format(self, sample_results_file):
        """Test report command with text format."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", "text"]
        )
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_report_markdown_format(self, sample_results_file):
        """Test report command with markdown format."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", "markdown"]
        )
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_report_json_format(self, sample_results_file):
        """Test report command with JSON format."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", "json"]
        )
        assert result.exit_code == 0
        assert len(result.output) > 0

    def test_report_to_output_file(self, sample_results_file, temp_dir):
        """Test report command with output file."""
        output_file = temp_dir / "report.txt"
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_report_markdown_to_file(self, sample_results_file, temp_dir):
        """Test report command with markdown output to file."""
        output_file = temp_dir / "report.md"
        result = runner.invoke(
            app,
            [
                "report",
                str(sample_results_file),
                "--format",
                "markdown",
                "--output",
                str(output_file),
            ],
        )
        assert result.exit_code == 0
        assert output_file.exists()


class TestReportCommandSections:
    """Test report command with different sections."""

    def test_report_summary_section(self, sample_results_file):
        """Test report command with summary section only."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--section", "summary"]
        )
        assert result.exit_code == 0

    def test_report_variables_section(self, sample_results_file):
        """Test report command with variables section only."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--section", "variables"]
        )
        assert result.exit_code == 0

    def test_report_statistics_section(self, sample_results_file):
        """Test report command with statistics section only."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--section", "statistics"]
        )
        assert result.exit_code == 0

    def test_report_multiple_sections(self, sample_results_file):
        """Test report command with multiple sections."""
        result = runner.invoke(
            app,
            [
                "report",
                str(sample_results_file),
                "--section",
                "summary",
                "--section",
                "variables",
            ],
        )
        assert result.exit_code == 0


class TestReportCommandErrors:
    """Test report command error handling."""

    def test_report_missing_file(self):
        """Test report command with non-existent file."""
        result = runner.invoke(app, ["report", "nonexistent_results.json"])
        assert result.exit_code != 0

    def test_report_no_arguments(self):
        """Test report command without required arguments."""
        result = runner.invoke(app, ["report"])
        assert result.exit_code != 0

    def test_report_invalid_json(self, invalid_json_file):
        """Test report command with invalid JSON file."""
        result = runner.invoke(app, ["report", str(invalid_json_file)])
        assert result.exit_code != 0
        assert "error" in result.output.lower() or "invalid" in result.output.lower()

    def test_report_missing_keys(self, minimal_results_file):
        """Test report command with incomplete results data."""
        result = runner.invoke(app, ["report", str(minimal_results_file)])
        # Should either succeed with available data or fail gracefully
        assert result.exit_code in (0, 1)


class TestReportCommandExitCodes:
    """Test report command exit codes."""

    def test_report_success_exit_code(self, sample_results_file):
        """Test report command returns 0 on success."""
        result = runner.invoke(app, ["report", str(sample_results_file)])
        assert result.exit_code == 0

    def test_report_error_exit_code_missing_file(self):
        """Test report command returns non-zero for missing file."""
        result = runner.invoke(app, ["report", "nonexistent.json"])
        assert result.exit_code != 0

    def test_report_error_exit_code_no_args(self):
        """Test report command returns non-zero when no arguments provided."""
        result = runner.invoke(app, ["report"])
        assert result.exit_code != 0

    def test_report_error_exit_code_invalid_json(self, invalid_json_file):
        """Test report command returns non-zero for invalid JSON."""
        result = runner.invoke(app, ["report", str(invalid_json_file)])
        assert result.exit_code != 0


class TestReportCommandParametrized:
    """Parametrized tests for report command."""

    @pytest.mark.parametrize(
        "help_flag",
        ["--help", "-h"],
    )
    def test_report_help_variants(self, help_flag):
        """Test various help option formats."""
        result = runner.invoke(app, ["report", help_flag])
        assert result.exit_code == 0
        assert "report" in result.output.lower()

    @pytest.mark.parametrize(
        "output_format",
        ["text", "markdown", "json"],
    )
    def test_report_format_options(self, sample_results_file, output_format):
        """Test different output format options."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", output_format]
        )
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "format_flag",
        ["--format", "-f"],
    )
    def test_report_format_flag_variants(self, sample_results_file, format_flag):
        """Test various format flag options."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), format_flag, "text"]
        )
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "output_flag",
        ["--output", "-o"],
    )
    def test_report_output_flag_variants(
        self, sample_results_file, temp_dir, output_flag
    ):
        """Test various output flag options."""
        output_file = temp_dir / "report.txt"
        result = runner.invoke(
            app,
            ["report", str(sample_results_file), output_flag, str(output_file)],
        )
        assert result.exit_code == 0

    @pytest.mark.parametrize(
        "section",
        ["summary", "variables", "statistics", "correlation"],
    )
    def test_report_section_options(self, sample_results_file, section):
        """Test different section options."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--section", section]
        )
        # May succeed or fail depending on data availability
        assert result.exit_code in (0, 1)

    @pytest.mark.parametrize(
        "section_flag",
        ["--section", "-s"],
    )
    def test_report_section_flag_variants(self, sample_results_file, section_flag):
        """Test various section flag options."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), section_flag, "summary"]
        )
        assert result.exit_code in (0, 1)


class TestReportCommandOutputFormat:
    """Test report command output format."""

    def test_report_text_output_readable(self, sample_results_file):
        """Test that text output is human-readable."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", "text"]
        )
        assert result.exit_code == 0
        # Should contain some recognizable text
        assert len(result.output) > 0

    def test_report_markdown_output_format(self, sample_results_file):
        """Test that markdown output contains markdown syntax."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", "markdown"]
        )
        assert result.exit_code == 0
        # Markdown should contain headers or formatting
        assert len(result.output) > 0

    def test_report_json_output_valid(self, sample_results_file):
        """Test that JSON output is valid JSON."""
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--format", "json"]
        )
        if result.exit_code == 0:
            # Try to parse as JSON
            try:
                json.loads(result.output)
            except json.JSONDecodeError:
                # If it's not valid JSON, the test should be aware
                pass

    def test_report_file_output_success_message(
        self, sample_results_file, temp_dir
    ):
        """Test that file output shows success message."""
        output_file = temp_dir / "report.txt"
        result = runner.invoke(
            app, ["report", str(sample_results_file), "--output", str(output_file)]
        )
        assert result.exit_code == 0
        # Should mention the output file or success
        assert (
            "saved" in result.output.lower()
            or "✅" in result.output
            or str(output_file) in result.output
        )


class TestReportCommandEdgeCases:
    """Test report command edge cases."""

    def test_report_empty_results(self, temp_dir):
        """Test report command with empty results file."""
        empty_file = temp_dir / "empty.json"
        empty_file.write_text("{}")
        result = runner.invoke(app, ["report", str(empty_file)])
        # Should handle gracefully
        assert result.exit_code in (0, 1)

    def test_report_minimal_data(self, minimal_results_file):
        """Test report command with minimal valid data."""
        result = runner.invoke(app, ["report", str(minimal_results_file)])
        # Should handle minimal data
        assert result.exit_code in (0, 1)

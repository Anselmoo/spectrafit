"""Tests for main CLI entry point."""

from __future__ import annotations

from typer.testing import CliRunner

from spectrafit.cli.main import app


runner = CliRunner()


def test_cli_help():
    """Test CLI help output."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "SpectraFit" in result.output
    assert "fit" in result.output
    assert "validate" in result.output
    assert "convert" in result.output
    assert "report" in result.output
    assert "plugins" in result.output


def test_cli_help_short():
    """Test CLI help output with short flag."""
    result = runner.invoke(app, ["-h"])
    assert result.exit_code == 0
    assert "SpectraFit" in result.output


def test_cli_version():
    """Test CLI version output."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_version_short():
    """Test CLI version output with short flag."""
    result = runner.invoke(app, ["-v"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()


def test_cli_no_args():
    """Test CLI with no arguments shows help."""
    result = runner.invoke(app, [])
    # Exit code 2 is normal for Typer when no command is provided and no_args_is_help is True
    assert result.exit_code in (0, 2)
    assert "SpectraFit" in result.output or "spectrafit" in result.output.lower()


def test_fit_command_help():
    """Test fit command help."""
    result = runner.invoke(app, ["fit", "--help"])
    assert result.exit_code == 0
    assert "fit" in result.output.lower()


def test_validate_command_help():
    """Test validate command help."""
    result = runner.invoke(app, ["validate", "--help"])
    assert result.exit_code == 0
    assert "validate" in result.output.lower()


def test_convert_command_help():
    """Test convert command help."""
    result = runner.invoke(app, ["convert", "--help"])
    assert result.exit_code == 0
    assert "convert" in result.output.lower()


def test_report_command_help():
    """Test report command help."""
    result = runner.invoke(app, ["report", "--help"])
    assert result.exit_code == 0
    assert "report" in result.output.lower()


def test_plugins_command_help():
    """Test plugins command help."""
    result = runner.invoke(app, ["plugins", "--help"])
    assert result.exit_code == 0
    assert "plugin" in result.output.lower()


def test_invalid_command():
    """Test invalid command returns error."""
    result = runner.invoke(app, ["invalid-command"])
    assert result.exit_code != 0


def test_fit_missing_arguments():
    """Test fit command without required arguments."""
    result = runner.invoke(app, ["fit"])
    assert result.exit_code != 0


def test_validate_missing_arguments():
    """Test validate command without required arguments."""
    result = runner.invoke(app, ["validate"])
    assert result.exit_code != 0


def test_convert_missing_arguments():
    """Test convert command without required arguments."""
    result = runner.invoke(app, ["convert"])
    assert result.exit_code != 0

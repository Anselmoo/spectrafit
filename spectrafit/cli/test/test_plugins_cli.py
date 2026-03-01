"""Tests for plugin CLI commands."""

from __future__ import annotations

import pytest

from typer.testing import CliRunner

from spectrafit.cli.main import app


pytestmark = pytest.mark.integration


runner = CliRunner()


def test_plugins_list():
    """Test plugins list command."""
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0
    assert "Available SpectraFit Plugins" in result.output
    # Should have jupyter plugin
    assert "jupyter" in result.output


def test_plugins_list_verbose():
    """Test plugins list command with verbose flag."""
    result = runner.invoke(app, ["plugins", "list", "-v"])
    assert result.exit_code == 0
    assert "Available SpectraFit Plugins" in result.output
    assert "Version:" in result.output
    assert "Description:" in result.output


def test_plugins_list_verbose_long():
    """Test plugins list command with verbose long flag."""
    result = runner.invoke(app, ["plugins", "list", "--verbose"])
    assert result.exit_code == 0
    assert "Available SpectraFit Plugins" in result.output


def test_jupyter_help():
    """Test Jupyter plugin help."""
    result = runner.invoke(app, ["plugins", "jupyter", "--help"])
    assert result.exit_code == 0
    assert "jupyter" in result.output.lower() or "Jupyter" in result.output

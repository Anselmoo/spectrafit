"""Tests for built-in plugins."""

from __future__ import annotations

import pytest
import typer

from spectrafit.plugins.jupyter_plugin import JupyterPlugin
from spectrafit.plugins.protocol import SpectraFitPlugin


pytestmark = pytest.mark.integration


def test_jupyter_plugin_attributes():
    """Test Jupyter plugin attributes."""
    plugin = JupyterPlugin()
    assert plugin.name == "jupyter"
    assert plugin.version == "1.0.0"
    assert isinstance(plugin.description, str)


def test_jupyter_plugin_implements_protocol():
    """Test Jupyter plugin implements SpectraFitPlugin protocol."""
    plugin = JupyterPlugin()
    assert isinstance(plugin, SpectraFitPlugin)


def test_jupyter_plugin_register_commands():
    """Test Jupyter plugin can register commands."""
    plugin = JupyterPlugin()
    app = typer.Typer()

    # Should not raise
    plugin.register_commands(app)

    # Check command was registered
    commands = [cmd.name for cmd in app.registered_commands]
    assert "jupyter" in commands


def test_jupyter_plugin_register_models():
    """Test Jupyter plugin can register models."""
    plugin = JupyterPlugin()
    models = plugin.register_models()
    assert isinstance(models, list)

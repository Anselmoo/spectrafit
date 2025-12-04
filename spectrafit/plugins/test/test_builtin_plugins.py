"""Tests for built-in plugins."""

from __future__ import annotations

import typer

from spectrafit.plugins.jupyter_plugin import JupyterPlugin
from spectrafit.plugins.moessbauer_plugin import MoessbauerPlugin
from spectrafit.plugins.protocol import SpectraFitPlugin
from spectrafit.plugins.rixs_plugin import RIXSPlugin


def test_rixs_plugin_attributes():
    """Test RIXS plugin attributes."""
    plugin = RIXSPlugin()
    assert plugin.name == "rixs"
    assert plugin.version == "1.0.0"
    assert isinstance(plugin.description, str)
    assert len(plugin.description) > 0


def test_rixs_plugin_implements_protocol():
    """Test RIXS plugin implements SpectraFitPlugin protocol."""
    plugin = RIXSPlugin()
    assert isinstance(plugin, SpectraFitPlugin)


def test_rixs_plugin_register_commands():
    """Test RIXS plugin can register commands."""
    plugin = RIXSPlugin()
    app = typer.Typer()

    # Should not raise
    plugin.register_commands(app)

    # Check command was registered
    commands = [cmd.name for cmd in app.registered_commands]
    assert "rixs" in commands


def test_rixs_plugin_register_models():
    """Test RIXS plugin can register models."""
    plugin = RIXSPlugin()
    models = plugin.register_models()
    assert isinstance(models, list)


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


def test_moessbauer_plugin_attributes():
    """Test Mössbauer plugin attributes."""
    plugin = MoessbauerPlugin()
    assert plugin.name == "moessbauer"
    assert plugin.version == "1.0.0"
    assert isinstance(plugin.description, str)


def test_moessbauer_plugin_implements_protocol():
    """Test Mössbauer plugin implements SpectraFitPlugin protocol."""
    plugin = MoessbauerPlugin()
    assert isinstance(plugin, SpectraFitPlugin)


def test_moessbauer_plugin_register_commands():
    """Test Mössbauer plugin can register commands."""
    plugin = MoessbauerPlugin()
    app = typer.Typer()

    # Should not raise
    plugin.register_commands(app)

    # Check command was registered
    commands = [cmd.name for cmd in app.registered_commands]
    assert "moessbauer-info" in commands


def test_moessbauer_plugin_register_models():
    """Test Mössbauer plugin can register models."""
    plugin = MoessbauerPlugin()
    models = plugin.register_models()
    assert isinstance(models, list)

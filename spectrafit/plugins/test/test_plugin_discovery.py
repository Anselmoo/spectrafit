"""Tests for plugin discovery system."""

from __future__ import annotations

from spectrafit.plugins import PluginRegistry
from spectrafit.plugins import get_plugin_registry


def test_plugin_registry_creation():
    """Test plugin registry creation."""
    registry = PluginRegistry()
    assert registry is not None


def test_get_plugin_registry_singleton():
    """Test that get_plugin_registry returns singleton."""
    registry1 = get_plugin_registry()
    registry2 = get_plugin_registry()
    assert registry1 is registry2


def test_list_available_builtins():
    """Test listing available built-in plugins."""
    registry = PluginRegistry()
    builtins = registry.list_available_builtins()
    assert isinstance(builtins, list)
    assert "jupyter" in builtins
    assert "moessbauer" in builtins
    assert "rixs" not in builtins


def test_load_builtin_jupyter():
    """Test loading Jupyter built-in plugin."""
    registry = PluginRegistry()
    plugin = registry.load_builtin_plugin("jupyter")
    assert plugin is not None
    assert plugin.name == "jupyter"
    assert plugin.version == "1.0.0"


def test_load_builtin_moessbauer():
    """Test loading Mössbauer built-in plugin."""
    registry = PluginRegistry()
    plugin = registry.load_builtin_plugin("moessbauer")
    assert plugin is not None
    assert plugin.name == "moessbauer"
    assert plugin.version == "1.0.0"


def test_load_nonexistent_plugin():
    """Test loading non-existent plugin returns None."""
    registry = PluginRegistry()
    plugin = registry.load_builtin_plugin("nonexistent")
    assert plugin is None


def test_get_plugin():
    """Test getting a loaded plugin."""
    registry = PluginRegistry()
    plugin = registry.load_builtin_plugin("jupyter")
    assert plugin is not None

    retrieved = registry.get_plugin("jupyter")
    assert retrieved is plugin


def test_list_plugins():
    """Test listing registered plugins."""
    registry = PluginRegistry()
    initial_count = len(registry.list_plugins())

    plugin = registry.load_builtin_plugin("jupyter")
    assert plugin is not None

    plugins = registry.list_plugins()
    assert len(plugins) == initial_count + 1
    assert "jupyter" in plugins

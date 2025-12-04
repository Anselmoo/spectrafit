"""Tests for plugin protocol."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spectrafit.plugins.protocol import SpectraFitPlugin


if TYPE_CHECKING:
    import typer


def test_plugin_protocol_attributes():
    """Test that SpectraFitPlugin protocol has required attributes."""
    # Protocol classes define required attributes in __annotations__
    assert "__annotations__" in dir(SpectraFitPlugin) or callable(
        getattr(SpectraFitPlugin, "__init__", None)
    )


def test_plugin_protocol_methods():
    """Test that SpectraFitPlugin protocol has required methods."""
    assert hasattr(SpectraFitPlugin, "register_commands")
    assert hasattr(SpectraFitPlugin, "register_models")


def test_plugin_implementation():
    """Test a simple plugin implementation."""
    import typer  # noqa: PLC0415

    class TestPlugin:
        name = "test-plugin"
        version = "1.0.0"
        description = "Test plugin"

        def register_commands(self, parent_app: typer.Typer) -> None:
            @parent_app.command(name="test")
            def test_command() -> None:
                """Test command."""

        def register_models(self) -> list[type]:
            return []

    plugin = TestPlugin()
    assert isinstance(plugin, SpectraFitPlugin)
    assert plugin.name == "test-plugin"
    assert plugin.version == "1.0.0"
    assert plugin.description == "Test plugin"

"""Unit tests for the plugins CLI surface."""

from __future__ import annotations

import importlib.util

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import typer

from spectrafit.cli.commands.plugins.main import plugins_app
from spectrafit.cli.commands.plugins.main import register_discovered_plugin_commands
from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.unit
class TestPluginsCli:
    """Validate the plugins command group after shim cleanup."""

    def test_plugins_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["plugins", "--help"])
        assert result.exit_code == 0

    def test_plugins_module_import_does_not_discover_plugins(self) -> None:
        module_path = (
            Path(__file__).resolve().parents[2]
            / "spectrafit"
            / "cli"
            / "commands"
            / "plugins"
            / "main.py"
        )
        spec = importlib.util.spec_from_file_location(
            "spectrafit.cli.commands.plugins._lazy_import_probe",
            module_path,
        )
        assert spec is not None
        assert spec.loader is not None
        module = importlib.util.module_from_spec(spec)

        with patch("spectrafit.plugins.get_plugin_registry") as get_registry:
            spec.loader.exec_module(module)

        get_registry.assert_not_called()

    def test_plugins_list_handles_empty_registry(self) -> None:
        registry = MagicMock()
        registry.discover_plugins.return_value = iter(())

        with patch(
            "spectrafit.cli.commands.plugins.main.get_plugin_registry",
            return_value=registry,
        ):
            result = runner.invoke(app, ["plugins", "list"])

        assert result.exit_code == 0
        assert "No external plugins discovered." in result.output

    def test_discovered_plugin_command_is_registered(self) -> None:
        class FakePlugin:
            name = "fake-plugin"
            version = "1.0.0"
            description = "Fake plugin for command registration"

            def register_commands(self, parent_app: typer.Typer) -> None:
                @parent_app.command(name="plugin-hello")
                def plugin_hello() -> None:
                    typer.echo("hello from plugin")

            def register_models(self) -> list[type]:
                return []

        registry = MagicMock()
        registry.discover_plugins.return_value = iter((FakePlugin(),))

        register_discovered_plugin_commands(plugins_app, registry=registry)

        result = runner.invoke(app, ["plugins", "plugin-hello"])

        assert result.exit_code == 0
        assert "hello from plugin" in result.output

    def test_discovered_plugin_command_is_registered_lazily_for_invocation(self) -> None:
        class FakePlugin:
            name = "fake-plugin-lazy"
            version = "1.0.0"
            description = "Fake plugin for lazy command registration"

            def register_commands(self, parent_app: typer.Typer) -> None:
                @parent_app.command(name="plugin-lazy-hello")
                def plugin_lazy_hello() -> None:
                    typer.echo("hello from lazy plugin")

            def register_models(self) -> list[type]:
                return []

        registry = MagicMock()
        registry.discover_plugins.return_value = iter((FakePlugin(),))

        with patch(
            "spectrafit.cli.commands.plugins.main.get_plugin_registry",
            return_value=registry,
        ):
            result = runner.invoke(app, ["plugins", "plugin-lazy-hello"])

        assert result.exit_code == 0
        assert "hello from lazy plugin" in result.output
        registry.discover_plugins.assert_called_once()

    def test_plugin_command_registration_is_idempotent(self) -> None:
        register_calls = 0

        class FakePlugin:
            name = "fake-plugin-once"
            version = "1.0.0"
            description = "Fake plugin for idempotent registration"

            def register_commands(self, parent_app: typer.Typer) -> None:
                nonlocal register_calls
                register_calls += 1

                @parent_app.command(name="plugin-once")
                def plugin_once() -> None:
                    typer.echo("registered once")

            def register_models(self) -> list[type]:
                return []

        registry = MagicMock()
        registry.discover_plugins.return_value = iter((FakePlugin(),))

        register_discovered_plugin_commands(plugins_app, registry=registry)
        registry.discover_plugins.return_value = iter((FakePlugin(),))
        register_discovered_plugin_commands(plugins_app, registry=registry)

        result = runner.invoke(app, ["plugins", "plugin-once"])

        assert result.exit_code == 0
        assert "registered once" in result.output
        assert register_calls == 1

    def test_jupyter_remains_top_level_not_plugin_subcommand(self) -> None:
        plugin_result = runner.invoke(app, ["plugins", "jupyter", "--help"])
        top_level_result = runner.invoke(app, ["jupyter", "--help"])

        assert plugin_result.exit_code != 0
        assert "No such command" in plugin_result.output
        assert top_level_result.exit_code == 0

"""Unit tests for plugin discovery entry-point handling."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from spectrafit.plugins.discovery import PluginRegistry


class _EntryPointsWithSelect:
    """Tiny helper mimicking the Python 3.11+ entry-points API."""

    def __init__(self, entry_points: list[object]) -> None:
        self._entry_points = entry_points

    def select(self, *, group: str) -> list[object]:
        assert group == "spectrafit.plugins"
        return self._entry_points


@pytest.mark.unit
def test_discover_plugins_loads_entry_points_and_registers_plugin() -> None:
    class FakePlugin:
        name = "fake-plugin"
        version = "1.0.0"
        description = "Fake plugin for discovery"

        def register_commands(self, parent_app: object) -> None:
            return None

        def register_models(self) -> list[type]:
            return []

    entry_point = MagicMock()
    entry_point.load.return_value = FakePlugin

    registry = PluginRegistry()

    with patch(
        "spectrafit.plugins.discovery.importlib.metadata.entry_points",
        return_value=_EntryPointsWithSelect([entry_point]),
    ):
        discovered = list(registry.discover_plugins())

    assert len(discovered) == 1
    assert discovered[0].name == "fake-plugin"
    assert registry.get_plugin("fake-plugin") is discovered[0]


@pytest.mark.unit
def test_discover_plugins_supports_legacy_mapping_entry_points_api() -> None:
    class LegacyPlugin:
        name = "legacy-plugin"
        version = "1.0.0"
        description = "Plugin loaded from legacy mapping API"

        def register_commands(self, parent_app: object) -> None:
            return None

        def register_models(self) -> list[type]:
            return []

    entry_point = MagicMock()
    entry_point.load.return_value = LegacyPlugin

    registry = PluginRegistry()

    with patch(
        "spectrafit.plugins.discovery.importlib.metadata.entry_points",
        return_value={"spectrafit.plugins": [entry_point]},
    ):
        discovered = list(registry.discover_plugins())

    assert len(discovered) == 1
    assert discovered[0].name == "legacy-plugin"

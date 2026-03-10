"""Unit tests for plugin entry-point discovery."""

from __future__ import annotations

import pytest

from spectrafit.plugins.discovery import PluginRegistry


class _ValidPlugin:
    """Minimal runtime-checkable plugin implementation for tests."""

    name = "demo"
    version = "1.0.0"
    description = "demo plugin"

    def register_commands(self, _parent_app: object) -> None:
        pass

    def register_models(self) -> list[type]:
        return []


class _FakeEntryPoint:
    """Simple test double for ``importlib.metadata.EntryPoint``."""

    def __init__(self, name: str, plugin_class: type[object]) -> None:
        self.name = name
        self._plugin_class = plugin_class

    def load(self) -> type[object]:
        return self._plugin_class


class _FakeEntryPoints:
    """Simple test double for ``entry_points().select(...)``."""

    def __init__(self, values: list[_FakeEntryPoint]) -> None:
        self._values = values

    def select(self, *, group: str) -> list[_FakeEntryPoint]:
        _ = group
        return self._values


@pytest.mark.unit
def test_discover_plugins_uses_select_api(monkeypatch: pytest.MonkeyPatch) -> None:
    """Entry-point discovery uses Python 3.12 ``select`` API."""
    fake_entry_points = _FakeEntryPoints(
        [_FakeEntryPoint(name="demo", plugin_class=_ValidPlugin)]
    )

    monkeypatch.setattr(
        "spectrafit.plugins.discovery.importlib.metadata.entry_points",
        lambda: fake_entry_points,
    )

    registry = PluginRegistry()
    discovered = list(registry.discover_plugins())

    assert len(discovered) == 1
    assert discovered[0].name == "demo"
    assert registry.get_plugin("demo") is not None

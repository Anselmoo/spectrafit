"""Plugin discovery and loading system for SpectraFit.

This module provides utilities for discovering, loading, and managing plugins
using entry points and dynamic imports.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import logging

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from spectrafit.plugins.protocol import SpectraFitPlugin


if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Registry for managing SpectraFit plugins.

    This class handles plugin discovery, loading, and management using
    entry points and dynamic imports.

    Example:
        ```python
        registry = PluginRegistry()
        plugins = registry.discover_plugins()
        for plugin in plugins:
            print(f"Found plugin: {plugin.name}")
        ```
    """

    def __init__(self) -> None:
        """Initialize the plugin registry."""
        self._plugins: dict[str, SpectraFitPlugin] = {}
        self._builtin_plugins: dict[str, str] = {
            "rixs": "spectrafit.plugins.rixs_plugin",
            "jupyter": "spectrafit.plugins.jupyter_plugin",
            "moessbauer": "spectrafit.plugins.moessbauer_plugin",
        }

    def discover_plugins(
        self,
        entry_point_group: str = "spectrafit.plugins",
    ) -> Iterator[SpectraFitPlugin]:
        """Discover plugins using entry points.

        Args:
            entry_point_group: Entry point group name to search for plugins.
                Defaults to "spectrafit.plugins".

        Yields:
            Discovered plugin instances that implement SpectraFitPlugin protocol.

        Example:
            ```python
            registry = PluginRegistry()
            for plugin in registry.discover_plugins():
                print(f"Discovered: {plugin.name} v{plugin.version}")
            ```
        """
        # Discover plugins via entry points
        try:
            entry_points = cast("Any", importlib.metadata.entry_points())
            # Handle both Python 3.10+ and older versions
            plugins_eps: Any
            if hasattr(entry_points, "select"):
                plugins_eps = entry_points.select(group=entry_point_group)
            else:
                # For older Python versions, entry_points returns dict
                # Access as dict for backward compatibility
                plugins_eps = entry_points.get(entry_point_group, [])

            for entry_point in plugins_eps:
                try:
                    plugin_class = entry_point.load()
                    plugin = plugin_class()
                    if isinstance(plugin, SpectraFitPlugin):
                        self._plugins[plugin.name] = plugin
                        yield plugin
                    else:
                        logger.warning(
                            "Plugin %s does not implement SpectraFitPlugin protocol",
                            entry_point.name,
                        )
                except (ImportError, AttributeError, TypeError):
                    logger.exception("Failed to load plugin %s", entry_point.name)
        except (ImportError, AttributeError):
            logger.exception("Failed to discover plugins")

    def load_builtin_plugin(self, plugin_name: str) -> SpectraFitPlugin | None:
        """Load a built-in plugin by name.

        Args:
            plugin_name: Name of the built-in plugin to load.

        Returns:
            Plugin instance if successfully loaded, None otherwise.

        Example:
            ```python
            registry = PluginRegistry()
            rixs_plugin = registry.load_builtin_plugin("rixs")
            if rixs_plugin:
                print(f"Loaded {rixs_plugin.name}")
            ```
        """
        if plugin_name in self._plugins:
            return self._plugins[plugin_name]

        module_path = self._builtin_plugins.get(plugin_name)
        if not module_path:
            logger.error("Unknown built-in plugin: %s", plugin_name)
            return None

        try:
            module = importlib.import_module(module_path)
            # Look for a class that implements SpectraFitPlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and attr_name.endswith("Plugin")
                    and hasattr(attr, "name")
                ):
                    try:
                        plugin = attr()
                        if isinstance(plugin, SpectraFitPlugin):
                            self._plugins[plugin.name] = plugin
                            return plugin
                    except (TypeError, AttributeError):
                        # Plugin class instantiation failed, try next
                        continue
        except ImportError as e:
            logger.warning("Failed to import plugin %s: %s", plugin_name, e)
        except (AttributeError, TypeError):
            logger.exception("Failed to load plugin %s", plugin_name)

        return None

    def get_plugin(self, plugin_name: str) -> SpectraFitPlugin | None:
        """Get a plugin by name.

        Args:
            plugin_name: Name of the plugin to retrieve.

        Returns:
            Plugin instance if found, None otherwise.
        """
        return self._plugins.get(plugin_name)

    def list_plugins(self) -> list[str]:
        """List all registered plugin names.

        Returns:
            List of registered plugin names.
        """
        return list(self._plugins.keys())

    def list_available_builtins(self) -> list[str]:
        """List all available built-in plugin names.

        Returns:
            List of built-in plugin names.
        """
        return list(self._builtin_plugins.keys())


# Global plugin registry instance
_registry: PluginRegistry | None = None


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry instance.

    Returns:
        Global PluginRegistry instance (singleton).
    """
    global _registry  # noqa: PLW0603
    if _registry is None:
        _registry = PluginRegistry()
    return _registry

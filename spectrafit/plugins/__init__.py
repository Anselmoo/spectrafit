"""Plugin module for SpectraFit.

This module provides the external plugin architecture for SpectraFit,
including the plugin protocol definition and entry-point discovery helpers.
"""

from __future__ import annotations

from spectrafit.plugins.discovery import PluginRegistry
from spectrafit.plugins.discovery import get_plugin_registry
from spectrafit.plugins.protocol import SpectraFitPlugin


__all__ = [
    "PluginRegistry",
    "SpectraFitPlugin",
    "get_plugin_registry",
]

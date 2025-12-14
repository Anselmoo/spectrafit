"""Plugin module for SpectraFit.

This module provides the plugin architecture for SpectraFit, including:
- Plugin protocol definition
- Plugin discovery and loading
- Built-in plugins (Jupyter, Mössbauer)
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

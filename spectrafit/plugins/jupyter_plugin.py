"""Jupyter Notebook plugin for SpectraFit — deprecated tombstone.

!!! warning "Deprecated"
    The Jupyter plugin has been promoted to a top-level CLI command.
    Use ``spectrafit jupyter`` instead of ``spectrafit plugins jupyter``.
    This module is retained for backward compatibility with any code that
    imports from it but will be removed in a future release.
"""

from __future__ import annotations

import warnings


warnings.warn(
    "spectrafit.plugins.jupyter_plugin is deprecated. "
    "Use 'spectrafit jupyter' CLI command directly. "
    "This module will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)


class JupyterPlugin:
    """Deprecated stub — Jupyter is now a top-level CLI command.

    !!! warning "Deprecated"
        Use ``spectrafit jupyter`` instead.
    """

    name = "jupyter"
    version = "1.0.0"
    description = "Jupyter notebook integration (deprecated — use 'spectrafit jupyter')"

    def register_commands(self, parent_app: object) -> None:
        """No-op — Jupyter is now a top-level command."""

    def register_models(self) -> list[type]:
        """Return empty list — no models to register."""
        return []

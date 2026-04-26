"""Legacy notebook compatibility surface.

This shim preserves the plugin-era import path during the v2 transition.
New code should prefer :mod:`spectrafit.notebook` for the typed notebook-first
API or :mod:`spectrafit.jupyter` for advanced runtime integrations.
"""

from __future__ import annotations

import warnings

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from spectrafit.jupyter import SpectraFitNotebook


__all__ = ["SpectraFitNotebook"]


def __getattr__(name: str) -> object:
    """Resolve deprecated notebook compatibility exports lazily."""
    if name != "SpectraFitNotebook":
        msg = f"module {__name__!r} has no attribute {name!r}"
        raise AttributeError(msg)

    warnings.warn(
        "spectrafit.plugins.notebook is deprecated and will be removed in v3.0.0; "
        "use spectrafit.notebook for the public typed facade or spectrafit.jupyter "
        "for advanced notebook runtime access.",
        FutureWarning,
        stacklevel=2,
    )

    from spectrafit.jupyter import SpectraFitNotebook  # noqa: PLC0415

    return SpectraFitNotebook

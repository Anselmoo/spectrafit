"""Frozen compatibility re-exports for legacy fitting-mode adapters.

This module keeps historical imports working at the adapter boundary while the
canonical v2 runtime surface lives in ``spectrafit.models.fitting_context``.
Do not grow new runtime behavior here; keep this file as a narrow quarantine
layer for compatibility callers only.
"""

from __future__ import annotations

from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.fitting_context import coerce_legacy_fitting_context
from spectrafit.models.fitting_context import coerce_legacy_fitting_mode


__all__ = [
    "FittingContext",
    "FittingMode",
    "coerce_legacy_fitting_context",
    "coerce_legacy_fitting_mode",
]

"""Thin import-compat aliases for report metric entry points.

Canonical metric behavior is owned by :mod:`spectrafit.core.regression_metrics`.
This compatibility module remains import-only so the frozen report package does
not reclaim runtime ownership.
"""

from __future__ import annotations

from spectrafit.core.regression_metrics import RegressionMetrics
from spectrafit.core.regression_metrics import warn_meassage


__all__ = ["RegressionMetrics", "warn_meassage"]

"""Frozen compatibility package for legacy report imports.

Canonical CLI and notebook rendering now lives under :mod:`spectrafit.reporting`.
This package remains as a stable import surface for callers that still import
the historical report modules directly during the v2.x line. Keep new runtime
code out of this package so the quarantine boundary stays explicit.

The compatibility package is deprecated for new callers and is targeted for
removal in v3.0.0 after the v2.x transition window. Importing this package
emits a ``FutureWarning`` so runtime callers can detect the frozen boundary.
"""

from __future__ import annotations

from spectrafit.report._compat import warn_legacy_report_import
from spectrafit.report._warnings import warn_meassage
from spectrafit.report.confidence import CIReport
from spectrafit.report.confidence import FitReport
from spectrafit.report.formatter import _extracted_gof_from_results
from spectrafit.report.formatter import fit_report_as_dict
from spectrafit.report.formatter import get_init_value
from spectrafit.report.metrics import RegressionMetrics
from spectrafit.report.printer import CORREL_HEAD
from spectrafit.report.printer import VERBOSE_DETAILED
from spectrafit.report.printer import VERBOSE_REGULAR
from spectrafit.report.printer import PrintingResults
from spectrafit.report.printer import PrintingStatus


warn_legacy_report_import()


__all__ = [
    "CORREL_HEAD",
    "VERBOSE_DETAILED",
    "VERBOSE_REGULAR",
    "CIReport",
    "FitReport",
    "PrintingResults",
    "PrintingStatus",
    "RegressionMetrics",
    "_extracted_gof_from_results",
    "fit_report_as_dict",
    "get_init_value",
    "warn_meassage",
]

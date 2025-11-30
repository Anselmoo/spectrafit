"""Report package for SpectraFit.

This package contains modules for generating fit reports, printing results,
and calculating regression metrics.
"""

from __future__ import annotations

from spectrafit.report.confidence import CIReport
from spectrafit.report.confidence import FitReport
from spectrafit.report.formatter import _extracted_gof_from_results
from spectrafit.report.formatter import fit_report_as_dict
from spectrafit.report.formatter import get_init_value
from spectrafit.report.metrics import RegressionMetrics
from spectrafit.report.metrics import warn_meassage
from spectrafit.report.printer import CORREL_HEAD
from spectrafit.report.printer import VERBOSE_DETAILED
from spectrafit.report.printer import VERBOSE_REGULAR
from spectrafit.report.printer import PrintingResults
from spectrafit.report.printer import PrintingStatus


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

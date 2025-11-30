"""Fit-Results as Report.

This module re-exports from split modules for backward compatibility.
The implementation has been refactored into:
- report/metrics.py - RegressionMetrics class
- report/formatter.py - fit_report_as_dict and formatting functions
- report/printer.py - PrintingResults, PrintingStatus classes
- report/confidence.py - CIReport, FitReport classes
"""

from __future__ import annotations

# Re-export all classes and functions for backward compatibility
from spectrafit.report import CORREL_HEAD
from spectrafit.report import VERBOSE_DETAILED
from spectrafit.report import VERBOSE_REGULAR
from spectrafit.report import CIReport
from spectrafit.report import FitReport
from spectrafit.report import PrintingResults
from spectrafit.report import PrintingStatus
from spectrafit.report import RegressionMetrics
from spectrafit.report import _extracted_gof_from_results
from spectrafit.report import fit_report_as_dict
from spectrafit.report import get_init_value
from spectrafit.report import warn_meassage


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

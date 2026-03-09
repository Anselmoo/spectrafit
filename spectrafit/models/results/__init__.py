"""Fitting result models — typed output containers.

This sub-package contains the Pydantic models that represent the complete,
authoritative output of a SpectraFit fitting run.  Separating these from the
input/configuration models keeps the top-level ``spectrafit.models`` directory
focused on pipeline configuration.

Public re-exports are available from ``spectrafit.models.results``.
"""

from __future__ import annotations

from spectrafit.models.results.diagnostics import FitDiagnostics
from spectrafit.models.results.diagnostics import compute_diagnostics
from spectrafit.models.results.diagnostics import validate_result
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import FitStatistics
from spectrafit.models.results.fit_result import ParameterResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.results.fit_summary import FitInsightsReport
from spectrafit.models.results.fit_summary import FitStatisticsReport
from spectrafit.models.results.fit_summary import FitSummaryReport
from spectrafit.models.results.fit_summary import FitVariableReport
from spectrafit.models.results.fit_summary import SplitOrientFrame


__all__ = [
    "ConfidenceResults",
    "DataSummary",
    "FitConfigurations",
    "FitDiagnostics",
    "FitInsights",
    "FitInsightsReport",
    "FitResult",
    "FitStatistics",
    "FitStatisticsReport",
    "FitSummaryReport",
    "FitVariableReport",
    "ParameterResult",
    "SplitOrientFrame",
    "VariableFitResult",
    "compute_diagnostics",
    "validate_result",
]

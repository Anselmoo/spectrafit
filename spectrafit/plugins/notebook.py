"""Jupyter Notebook plugin for SpectraFit.

This module re-exports from split modules for backward compatibility.
The implementation has been refactored into:
- plugins/notebook/display.py - DataFrameDisplay class
- plugins/notebook/plotting.py - DataFramePlot class
- plugins/notebook/export.py - ExportResults, ExportReport classes
- plugins/notebook/solver.py - SolverResults class
- plugins/notebook/core.py - SpectraFitNotebook class
"""

from __future__ import annotations

# Re-export all classes for backward compatibility
from spectrafit.plugins.notebook import DataFrameDisplay
from spectrafit.plugins.notebook import DataFramePlot
from spectrafit.plugins.notebook import ExportReport
from spectrafit.plugins.notebook import ExportResults
from spectrafit.plugins.notebook import SolverResults
from spectrafit.plugins.notebook import SpectraFitNotebook


__all__ = [
    "DataFrameDisplay",
    "DataFramePlot",
    "ExportReport",
    "ExportResults",
    "SolverResults",
    "SpectraFitNotebook",
]

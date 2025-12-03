"""Notebook package for SpectraFit.

This package contains utilities for using SpectraFit in Jupyter notebooks.
"""

from __future__ import annotations

from spectrafit.plugins.notebook.core import SpectraFitNotebook
from spectrafit.plugins.notebook.display import DataFrameDisplay
from spectrafit.plugins.notebook.export import ExportReport
from spectrafit.plugins.notebook.export import ExportResults
from spectrafit.plugins.notebook.plotting import DataFramePlot
from spectrafit.plugins.notebook.solver import SolverResults


__all__ = [
    "DataFrameDisplay",
    "DataFramePlot",
    "ExportReport",
    "ExportResults",
    "SolverResults",
    "SpectraFitNotebook",
]

"""Core Jupyter integration for SpectraFit.

This package contains the active Jupyter notebook functionality for SpectraFit,
providing interactive data analysis, fitting, and visualization capabilities.
"""

from __future__ import annotations

from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.jupyter.display import DataFrameDisplay
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.materializer import materialize_notebook_from_config
from spectrafit.jupyter.plotting import DataFramePlot
from spectrafit.jupyter.solver import SolverResults


__all__ = [
    "DataFrameDisplay",
    "DataFramePlot",
    "ExportReport",
    "ExportResults",
    "SolverResults",
    "SpectraFitNotebook",
    "materialize_notebook_from_config",
]

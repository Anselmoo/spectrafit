"""Core Jupyter integration for SpectraFit.

This package contains the core Jupyter notebook functionality for SpectraFit,
providing interactive data analysis, fitting, and visualization capabilities.

!!! note "Migration from plugins"
    In v2.0.0, the notebook functionality has been moved from
    ``spectrafit.plugins.notebook`` into this core package. The old import paths
    remain available but are deprecated and will be removed in v3.0.0.
"""

from __future__ import annotations

from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.jupyter.display import DataFrameDisplay
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.plotting import DataFramePlot
from spectrafit.jupyter.solver import SolverResults


__all__ = [
    "DataFrameDisplay",
    "DataFramePlot",
    "ExportReport",
    "ExportResults",
    "SolverResults",
    "SpectraFitNotebook",
]

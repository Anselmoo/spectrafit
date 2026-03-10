"""Notebook package for SpectraFit — deprecated re-export shim.

!!! warning "Deprecated"
    Import from ``spectrafit.jupyter`` instead.  This shim will be removed in v3.0.0.
"""

from __future__ import annotations

import warnings

from spectrafit.jupyter.core import SpectraFitNotebook
from spectrafit.jupyter.display import DataFrameDisplay
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.plotting import DataFramePlot
from spectrafit.jupyter.solver import SolverResults


warnings.warn(
    "Importing from 'spectrafit.plugins.notebook' is deprecated and will be removed "
    "in v3.0.0. Use 'spectrafit.jupyter' instead.",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "DataFrameDisplay",
    "DataFramePlot",
    "ExportReport",
    "ExportResults",
    "SolverResults",
    "SpectraFitNotebook",
]

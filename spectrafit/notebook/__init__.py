"""Notebook-first SpectraFit facade with progressive escape hatches."""

from __future__ import annotations

from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.meta_config import MetaConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig
from spectrafit.notebook._api import background
from spectrafit.notebook._api import fit
from spectrafit.notebook._api import fixed
from spectrafit.notebook._api import peak
from spectrafit.notebook._api import read
from spectrafit.notebook._api import tie
from spectrafit.notebook._result import FitSession


__all__ = [
    "Component",
    "ConfIntervalConfig",
    "DataConfig",
    "FitParameter",
    "FitSession",
    "FittingContext",
    "FittingMode",
    "MetaConfig",
    "MinimizerConfig",
    "OptimizerConfig",
    "PreprocessingConfig",
    "background",
    "fit",
    "fixed",
    "peak",
    "read",
    "tie",
]

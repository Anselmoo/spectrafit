"""Core package for SpectraFit.

This package contains core utilities for data loading, preprocessing,
postprocessing, exporting, configuration management, and the fitting pipeline.
"""

from __future__ import annotations

from spectrafit.core.data_loader import load_data
from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FitStatistics
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.core.pipeline import FittingResult
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.core.postprocessing import PostProcessing
from spectrafit.core.postprocessing import PostProcessingResult
from spectrafit.core.preprocessing import PreProcessing


__all__ = [
    "ColumnConfig",
    "FitStatistics",
    "FittingPipeline",
    "FittingResult",
    "PostProcessing",
    "PostProcessingResult",
    "PreProcessing",
    "UnifiedFittingConfig",
    "fitting_routine_pipeline",
    "load_data",
]

"""Core package for SpectraFit.

This package contains core utilities for data loading, preprocessing,
postprocessing, exporting, configuration management, and the fitting pipeline.
"""

from __future__ import annotations

from spectrafit.core.config import ConfigLoader
from spectrafit.core.config import FittingConfig
from spectrafit.core.config import load_config
from spectrafit.core.data_loader import check_keywords_consistency
from spectrafit.core.data_loader import load_data
from spectrafit.core.data_loader import pkl2any
from spectrafit.core.data_loader import pure_fname
from spectrafit.core.data_loader import read_input_file
from spectrafit.core.data_loader import unicode_check
from spectrafit.core.export import SaveResult
from spectrafit.core.export import exclude_none_dictionary
from spectrafit.core.export import transform_nested_types
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.core.pipeline import FittingResult
from spectrafit.core.pipeline import fitting_routine_pipeline
from spectrafit.core.postprocessing import PostProcessing
from spectrafit.core.preprocessing import PreProcessing


__all__ = [
    "ConfigLoader",
    "FittingConfig",
    "FittingPipeline",
    "FittingResult",
    "PostProcessing",
    "PreProcessing",
    "SaveResult",
    "check_keywords_consistency",
    "exclude_none_dictionary",
    "fitting_routine_pipeline",
    "load_config",
    "load_data",
    "pkl2any",
    "pure_fname",
    "read_input_file",
    "transform_nested_types",
    "unicode_check",
]

"""Collection of essential tools for running SpectraFit.

This module re-exports from split modules for backward compatibility.
The implementation has been refactored into:
- core/data_loader.py - load_data, read_input_file
- core/preprocessing.py - PreProcessing class
- core/postprocessing.py - PostProcessing class
- core/export.py - SaveResult class
"""

from __future__ import annotations

# Re-export all classes and functions for backward compatibility
from spectrafit.core import PostProcessing
from spectrafit.core import PreProcessing
from spectrafit.core import SaveResult
from spectrafit.core import check_keywords_consistency
from spectrafit.core import exclude_none_dictionary
from spectrafit.core import load_data
from spectrafit.core import pkl2any
from spectrafit.core import pure_fname
from spectrafit.core import read_input_file
from spectrafit.core import transform_nested_types
from spectrafit.core import unicode_check


__all__ = [
    "PostProcessing",
    "PreProcessing",
    "SaveResult",
    "check_keywords_consistency",
    "exclude_none_dictionary",
    "load_data",
    "pkl2any",
    "pure_fname",
    "read_input_file",
    "transform_nested_types",
    "unicode_check",
]

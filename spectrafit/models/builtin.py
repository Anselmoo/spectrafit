"""Minimization models for curve fitting.

This module re-exports from split modules for backward compatibility.
The implementation has been refactored into:
- models/distributions.py - Distribution models
- models/solver.py - Solver models
"""

from __future__ import annotations

# Re-export all classes and functions for backward compatibility
from spectrafit.models.distributions import DistributionModels
from spectrafit.models.model_parameters import ModelParameters
from spectrafit.models.model_parameters import ReferenceKeys
from spectrafit.models.solver import Constants
from spectrafit.models.solver import SolverModels
from spectrafit.models.solver import calculated_model
from spectrafit.models.types import FittingArgs
from spectrafit.models.types import ModelParameterSpec
from spectrafit.models.types import ParameterConstraint
from spectrafit.models.types import PeakModelSpec
from spectrafit.models.types import PeaksDict


GLOBAL_NONE = 0  # Formerly GlobalMode.NONE — standard single-dataset fit
GLOBAL_STANDARD = 1  # Formerly GlobalMode.STANDARD — multi-dataset global fit
GLOBAL_WITH_PRE = 2  # Formerly GlobalMode.WITH_PRE — global fit with pre-defined params


__all__ = [
    "GLOBAL_NONE",
    "GLOBAL_STANDARD",
    "GLOBAL_WITH_PRE",
    "Constants",
    "DistributionModels",
    "FittingArgs",
    "ModelParameterSpec",
    "ModelParameters",
    "ParameterConstraint",
    "PeakModelSpec",
    "PeaksDict",
    "ReferenceKeys",
    "SolverModels",
    "calculated_model",
]

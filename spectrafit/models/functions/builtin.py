"""Minimization models for curve fitting.

This module re-exports from split modules for backward compatibility.
The implementation has been refactored into:
- models/distributions.py - Distribution models
- models/solver.py - Solver models
"""

from __future__ import annotations

# Re-export all classes and functions for backward compatibility
from spectrafit.models.functions.distributions import DistributionModels
from spectrafit.models.model_parameters import ModelParameters
from spectrafit.models.model_parameters import ReferenceKeys
from spectrafit.models.solver import Constants
from spectrafit.models.solver import SolverModels
from spectrafit.models.solver import calculated_model
from spectrafit.models.types import ModelParameterSpec
from spectrafit.models.types import ParameterConstraint


__all__ = [
    "Constants",
    "DistributionModels",
    "ModelParameterSpec",
    "ModelParameters",
    "ParameterConstraint",
    "ReferenceKeys",
    "SolverModels",
    "calculated_model",
]

"""Minimization models for curve fitting.

This module re-exports from split modules for backward compatibility.
The implementation has been refactored into:
- models/distributions.py - Distribution models
- models/autopeak.py - Auto-peak detection
- models/solver.py - Solver models
"""

from __future__ import annotations

# Re-export all classes and functions for backward compatibility
from spectrafit.models.autopeak import GLOBAL_NONE
from spectrafit.models.autopeak import GLOBAL_STANDARD
from spectrafit.models.autopeak import GLOBAL_WITH_PRE
from spectrafit.models.autopeak import AutoPeakDetection
from spectrafit.models.autopeak import ModelParameters
from spectrafit.models.autopeak import ReferenceKeys
from spectrafit.models.distributions import DistributionModels
from spectrafit.models.solver import Constants
from spectrafit.models.solver import SolverModels
from spectrafit.models.solver import calculated_model


__all__ = [
    "GLOBAL_NONE",
    "GLOBAL_STANDARD",
    "GLOBAL_WITH_PRE",
    "AutoPeakDetection",
    "Constants",
    "DistributionModels",
    "ModelParameters",
    "ReferenceKeys",
    "SolverModels",
    "calculated_model",
]

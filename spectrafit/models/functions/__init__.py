"""Peak-function and distribution implementations.

This sub-package contains the raw NumPy/SciPy math functions used by the
lmfit model registry.  They are intentionally separated from the Pydantic
data models to keep the top-level ``spectrafit.models`` directory focused on
configuration and result types.

Public re-exports are available from ``spectrafit.models.functions``.
"""

from __future__ import annotations

from spectrafit.models.functions.distributions import DistributionModels
from spectrafit.models.functions.regular import gaussian
from spectrafit.models.functions.regular import lorentzian
from spectrafit.models.functions.regular import pseudovoigt
from spectrafit.models.functions.regular import voigt


__all__ = [
    "DistributionModels",
    "gaussian",
    "lorentzian",
    "pseudovoigt",
    "voigt",
]

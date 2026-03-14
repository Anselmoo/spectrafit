"""Compatibility distribution facade over the canonical regular-function kernel."""

from __future__ import annotations

from spectrafit.models.functions.regular import atan_step
from spectrafit.models.functions.regular import cgaussian
from spectrafit.models.functions.regular import clorentzian
from spectrafit.models.functions.regular import constant
from spectrafit.models.functions.regular import cvoigt
from spectrafit.models.functions.regular import erf_step
from spectrafit.models.functions.regular import exponential
from spectrafit.models.functions.regular import gaussian
from spectrafit.models.functions.regular import heaviside
from spectrafit.models.functions.regular import linear
from spectrafit.models.functions.regular import log_step
from spectrafit.models.functions.regular import lorentzian
from spectrafit.models.functions.regular import orcagaussian
from spectrafit.models.functions.regular import pearson1
from spectrafit.models.functions.regular import pearson2
from spectrafit.models.functions.regular import pearson3
from spectrafit.models.functions.regular import pearson4
from spectrafit.models.functions.regular import polynom2
from spectrafit.models.functions.regular import polynom3
from spectrafit.models.functions.regular import power
from spectrafit.models.functions.regular import pseudovoigt
from spectrafit.models.functions.regular import voigt


class DistributionModels:
    """Compatibility class preserving the historical distribution-method surface.

    The canonical numerical implementations live in ``regular.py`` and are used by the
    lmfit registry directly. This facade exists only to preserve the older
    ``DistributionModels.<name>`` API without maintaining a duplicate wrapper method body
    for every model.
    """

    gaussian = staticmethod(gaussian)
    orcagaussian = staticmethod(orcagaussian)
    lorentzian = staticmethod(lorentzian)
    voigt = staticmethod(voigt)
    pseudovoigt = staticmethod(pseudovoigt)
    exponential = staticmethod(exponential)
    power = staticmethod(power)
    linear = staticmethod(linear)
    constant = staticmethod(constant)
    heaviside = staticmethod(heaviside)
    erf = staticmethod(erf_step)
    atan = staticmethod(atan_step)
    log = staticmethod(log_step)
    cgaussian = staticmethod(cgaussian)
    clorentzian = staticmethod(clorentzian)
    cvoigt = staticmethod(cvoigt)
    polynom2 = staticmethod(polynom2)
    polynom3 = staticmethod(polynom3)
    pearson1 = staticmethod(pearson1)
    pearson2 = staticmethod(pearson2)
    pearson3 = staticmethod(pearson3)
    pearson4 = staticmethod(pearson4)


__all__ = ["DistributionModels"]

"""Regression tests for the public model-function compatibility surface."""

from __future__ import annotations

from spectrafit.models.functions import DistributionModels
from spectrafit.models.functions import gaussian
from spectrafit.models.functions import lorentzian
from spectrafit.models.functions import pseudovoigt
from spectrafit.models.functions import voigt
from spectrafit.models.functions.regular import atan_step
from spectrafit.models.functions.regular import erf_step
from spectrafit.models.functions.regular import log_step
from spectrafit.models.registry import REGISTRY


def test_distribution_models_facade_reuses_canonical_regular_functions() -> None:
    """Compatibility facade methods should alias the canonical regular kernel."""
    assert DistributionModels.gaussian is gaussian
    assert DistributionModels.lorentzian is lorentzian
    assert DistributionModels.pseudovoigt is pseudovoigt
    assert DistributionModels.voigt is voigt
    assert DistributionModels.erf is erf_step
    assert DistributionModels.atan is atan_step
    assert DistributionModels.log is log_step


def test_registry_names_remain_in_sync_with_distribution_facade() -> None:
    """Registry inventory should stay aligned with the historical facade surface."""
    expected_names = {
        "gaussian",
        "orcagaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
        "exponential",
        "power",
        "linear",
        "constant",
        "heaviside",
        "erf",
        "atan",
        "log",
        "cgaussian",
        "clorentzian",
        "cvoigt",
        "polynom2",
        "polynom3",
        "pearson1",
        "pearson2",
        "pearson3",
        "pearson4",
    }
    assert set(REGISTRY.names()) == expected_names

"""Synthetic data generators for testing and validation."""

from __future__ import annotations

from spectrafit.generators.scenarios import SyntheticScenario
from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.generators.scenarios import iter_example_scenarios
from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum


__all__ = [
    "PeakDefinition",
    "SyntheticScenario",
    "SyntheticSpectrum",
    "get_synthetic_scenario",
    "iter_example_scenarios",
]

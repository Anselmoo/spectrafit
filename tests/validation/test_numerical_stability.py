"""Numerical-stability trust-anchor tests for local spectral fitting."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING
from typing import Any

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum


if TYPE_CHECKING:
    from lmfit.model import ModelResult
    from numpy.typing import NDArray


pytestmark = pytest.mark.validation


def _fit_local_spectrum(
    *,
    x: NDArray[Any],
    y: NDArray[Any],
    components: list[Mapping[str, object]],
) -> ModelResult:
    config = UnifiedFittingConfig.model_validate({"components": components})
    bundle = config.build_composite_model()
    result = bundle.composite.fit(y, bundle.params, x=x)
    assert result.success, result.message
    return result


def test_zero_noise_gaussian_plus_linear_recovers_ground_truth() -> None:
    """A noise-free fit should recover the known synthetic parameters."""
    spectrum = SyntheticSpectrum(
        x_min=-2.0,
        x_max=2.0,
        num_points=1001,
        noise_level=0.0,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.2, "center": 0.15, "fwhmg": 0.45},
            ),
            PeakDefinition(
                model="linear",
                params={"slope": 0.02, "intercept": 0.05},
            ),
        ],
        seed=7,
    )
    x, y, _ = spectrum.generate()

    result = _fit_local_spectrum(
        x=x,
        y=y,
        components=[
            {
                "id": "peak",
                "model": "gaussian",
                "parameters": {
                    "amplitude": {"value": 0.9, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.0, "min": -0.5, "max": 0.5},
                    "fwhmg": {"value": 0.6, "min": 0.1, "max": 1.0},
                },
            },
            {
                "id": "bg",
                "model": "linear",
                "parameters": {
                    "slope": {"value": 0.0, "min": -0.1, "max": 0.1},
                    "intercept": {"value": 0.0, "min": 0.0, "max": 0.2},
                },
            },
        ],
    )

    assert result.params["peak_amplitude"].value == pytest.approx(1.2, abs=1e-9)
    assert result.params["peak_center"].value == pytest.approx(0.15, abs=1e-9)
    assert result.params["peak_fwhmg"].value == pytest.approx(0.45, abs=1e-9)
    assert result.params["bg_slope"].value == pytest.approx(0.02, abs=1e-9)
    assert result.params["bg_intercept"].value == pytest.approx(0.05, abs=2e-6)


def test_close_gaussian_peaks_remain_resolvable_under_noise() -> None:
    """Moderately overlapping peaks should still recover ordered centers."""
    spectrum = SyntheticSpectrum(
        x_min=-1.5,
        x_max=1.5,
        num_points=1501,
        noise_level=0.003,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 0.9, "center": -0.18, "fwhmg": 0.32},
            ),
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 0.7, "center": 0.17, "fwhmg": 0.28},
            ),
        ],
        seed=123,
    )
    x, y, _ = spectrum.generate()

    result = _fit_local_spectrum(
        x=x,
        y=y,
        components=[
            {
                "id": "p1",
                "model": "gaussian",
                "parameters": {
                    "amplitude": {"value": 0.7, "min": 0.0, "max": 2.0},
                    "center": {"value": -0.10, "min": -0.5, "max": 0.0},
                    "fwhmg": {"value": 0.25, "min": 0.1, "max": 0.6},
                },
            },
            {
                "id": "p2",
                "model": "gaussian",
                "parameters": {
                    "amplitude": {"value": 0.6, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.10, "min": 0.0, "max": 0.5},
                    "fwhmg": {"value": 0.35, "min": 0.1, "max": 0.6},
                },
            },
        ],
    )

    p1_center = result.params["p1_center"].value
    p2_center = result.params["p2_center"].value

    assert p1_center < p2_center
    assert p1_center == pytest.approx(-0.18, abs=0.01)
    assert p2_center == pytest.approx(0.17, abs=0.01)
    assert result.params["p1_amplitude"].value == pytest.approx(0.9, rel=0.02)
    assert result.params["p2_amplitude"].value == pytest.approx(0.7, rel=0.02)


def test_constraints_fixed_parameters_and_bounds_hold_during_fit() -> None:
    """Constrained scenario parameters should remain consistent after fitting."""
    scenario = get_synthetic_scenario("two-peak-constrained")
    x, y, _ = scenario.spectrum.generate()
    bundle = scenario.config.build_composite_model()
    result = bundle.composite.fit(y, bundle.params, x=x)

    assert result.success, result.message
    assert result.params["p2_center"].value == pytest.approx(
        result.params["p1_center"].value + 1.0,
        abs=1e-9,
    )
    assert result.params["p2_fwhml"].value == pytest.approx(
        result.params["p2_fwhmg"].value,
        abs=1e-9,
    )
    assert result.params["bg_slope"].value == pytest.approx(0.0, abs=1e-12)

    for name in ("p1_amplitude", "p1_center", "p1_fwhmg", "p2_amplitude", "bg_intercept"):
        parameter = result.params[name]
        assert parameter.min <= parameter.value <= parameter.max

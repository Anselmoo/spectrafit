"""Analytical trust-anchor tests for supported peak models."""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pytest

from spectrafit.models.functions import gaussian
from spectrafit.models.functions import lorentzian
from spectrafit.models.functions import pseudovoigt


pytestmark = pytest.mark.validation


def test_gaussian_area_matches_amplitude() -> None:
    """The Gaussian implementation is area-normalized by ``amplitude``."""
    x = np.linspace(-10.0, 10.0, 20_001)

    profile = gaussian(
        x=x,
        amplitude=2.5,
        center=0.2,
        fwhmg=0.8,
    )

    area = np.trapezoid(profile, x)

    assert area == pytest.approx(2.5, rel=1e-6, abs=1e-8)


def test_lorentzian_area_matches_amplitude_on_wide_domain() -> None:
    """The Lorentzian implementation conserves area over a wide finite grid."""
    x = np.linspace(-200.0, 200.0, 400_001)

    profile = lorentzian(
        x=x,
        amplitude=1.75,
        center=-1.0,
        fwhml=0.9,
    )

    area = np.trapezoid(profile, x)

    assert area == pytest.approx(1.75, rel=2e-3)


@pytest.mark.parametrize(
    ("model_fn", "width_key", "width"),
    [
        pytest.param(gaussian, "fwhmg", 1.2, id="gaussian"),
        pytest.param(lorentzian, "fwhml", 0.9, id="lorentzian"),
    ],
)
def test_peak_profiles_hit_half_maximum_at_half_fwhm(
    model_fn: Callable[..., np.ndarray],
    width_key: str,
    width: float,
) -> None:
    """Gaussian and Lorentzian widths follow the documented FWHM semantics."""
    center = 0.3 if width_key == "fwhmg" else -0.4
    peak_height = model_fn(
        np.array([center]),
        amplitude=1.7,
        center=center,
        **{width_key: width},
    )[0]
    half_max_height = model_fn(
        np.array([center + (width / 2.0)]),
        amplitude=1.7,
        center=center,
        **{width_key: width},
    )[0]

    assert half_max_height == pytest.approx(peak_height / 2.0, rel=1e-12, abs=1e-12)


def test_pseudovoigt_is_symmetric_and_centered() -> None:
    """Pseudo-Voigt should remain symmetric with its maximum at the center."""
    center = 1.3
    offsets = np.array([0.2, 0.7, 1.3])

    left = pseudovoigt(
        center - offsets,
        amplitude=1.4,
        center=center,
        fwhmg=0.8,
        fwhml=0.6,
    )
    right = pseudovoigt(
        center + offsets,
        amplitude=1.4,
        center=center,
        fwhmg=0.8,
        fwhml=0.6,
    )
    grid = np.linspace(center - 4.0, center + 4.0, 4001)
    profile = pseudovoigt(
        grid,
        amplitude=1.4,
        center=center,
        fwhmg=0.8,
        fwhml=0.6,
    )

    np.testing.assert_allclose(left, right, rtol=0.0, atol=1e-12)
    assert profile.argmax() == len(grid) // 2

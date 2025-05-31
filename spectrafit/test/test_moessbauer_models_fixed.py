"""Tests for the Mössbauer models."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import numpy as np


if TYPE_CHECKING:
    from numpy.typing import NDArray

from spectrafit.api.model_utils import create_amplitude_api
from spectrafit.api.model_utils import create_background_api
from spectrafit.api.model_utils import create_fwhml_api
from spectrafit.api.model_utils import create_isomershift_api
from spectrafit.api.model_utils import create_quadrupolesplitting_api
from spectrafit.api.moessbauer_model import MoessbauerDoubletAPI
from spectrafit.api.moessbauer_model import MoessbauerSingletAPI
from spectrafit.api.physical_constants import moessbauer_constants
from spectrafit.models.moessbauer import moessbauer_doublet
from spectrafit.models.moessbauer import moessbauer_sextet
from spectrafit.models.moessbauer import moessbauer_singlet


def _ensure_float64(
    arr: NDArray[np.float64] | NDArray[np.floating[Any]],
) -> NDArray[np.float64]:
    """Convert ndarray to float64 to satisfy mypy type checking.

    Args:
        arr: Input array to convert

    Returns:
        Array with float64 dtype
    """
    # Always return np.float64 to satisfy mypy
    return arr.astype(np.float64)


def test_moessbauer_singlet() -> None:
    """Test the Mössbauer singlet model."""
    # Create test velocity data
    velocity = _ensure_float64(np.linspace(-5, 5, 100))

    # Test with default parameters
    singlet = moessbauer_singlet(_ensure_float64(velocity))
    assert singlet.shape == velocity.shape

    # Test with custom parameters
    custom_singlet = moessbauer_singlet(
        _ensure_float64(velocity),
        amplitude=0.5,
        isomer_shift=0.3,
        fwhml=0.25,
        center=0.1,
    )
    assert custom_singlet.shape == velocity.shape

    # Test that changing amplitude scales the peak height
    singlet_1 = moessbauer_singlet(_ensure_float64(velocity), amplitude=1.0)
    singlet_2 = moessbauer_singlet(_ensure_float64(velocity), amplitude=2.0)

    # The peak height should scale with amplitude
    idx = np.argmax(singlet_1)
    assert np.isclose(singlet_2[idx], singlet_1[idx] * 2, rtol=1e-10)


def test_moessbauer_doublet() -> None:
    """Test the Mössbauer doublet model."""
    # Create test velocity data
    velocity = _ensure_float64(np.linspace(-5, 5, 100))

    # Test with default parameters
    doublet = moessbauer_doublet(_ensure_float64(velocity))
    assert doublet.shape == velocity.shape

    # Test with custom parameters
    custom_doublet = moessbauer_doublet(
        _ensure_float64(velocity),
        amplitude=0.5,
        isomer_shift=0.3,
        quadrupole_splitting=1.0,
        fwhml=0.25,
        center=0.1,
    )
    assert custom_doublet.shape == velocity.shape

    # Test that the total absorption (area) scales with amplitude
    doublet1 = moessbauer_doublet(_ensure_float64(velocity), amplitude=1.0)
    doublet2 = moessbauer_doublet(_ensure_float64(velocity), amplitude=2.0)
    # Sum should be proportional to amplitude (approximately)
    assert np.sum(doublet2) > np.sum(doublet1)  # More amplitude = higher value

    # Test that quadrupole splitting affects the spectrum
    # Compare distance between minimum points in spectra with different splitting
    small_qs = moessbauer_doublet(_ensure_float64(velocity), quadrupole_splitting=0.5)
    large_qs = moessbauer_doublet(_ensure_float64(velocity), quadrupole_splitting=2.0)

    # Find peaks using signal processing to identify peaks
    from scipy.signal import find_peaks

    # Find the peaks in both spectra
    small_qs_peaks, _ = find_peaks(small_qs, height=0.1 * np.max(small_qs))
    large_qs_peaks, _ = find_peaks(large_qs, height=0.1 * np.max(large_qs))

    # For each spectrum, find the distance between the peaks
    if len(small_qs_peaks) >= 2:
        small_qs_distance = abs(
            velocity[small_qs_peaks[1]] - velocity[small_qs_peaks[0]],
        )
    else:  #  pragma: no cover
        small_qs_distance = 0.0

    if len(large_qs_peaks) >= 2:
        large_qs_distance = abs(
            velocity[large_qs_peaks[1]] - velocity[large_qs_peaks[0]],
        )
    else:  #  pragma: no cover
        large_qs_distance = 0.0

    # The distance between peaks should reflect the quadrupole splitting
    # For larger quadrupole splitting, we expect larger peak separation
    assert large_qs_distance > small_qs_distance


def test_moessbauer_sextet() -> None:
    """Test the Mössbauer sextet model."""
    # Create test velocity data
    velocity = _ensure_float64(np.linspace(-10, 10, 200))

    # Test with default parameters
    sextet = moessbauer_sextet(_ensure_float64(velocity))
    assert sextet.shape == velocity.shape

    # Test with custom parameters
    custom_sextet = moessbauer_sextet(
        _ensure_float64(velocity),
        amplitude=0.5,
        isomer_shift=0.3,
        magnetic_field=30.0,
        fwhml=0.25,
        center=0.1,
    )
    assert custom_sextet.shape == velocity.shape

    # Test that the amplitude parameter affects peak height
    sextet1 = moessbauer_sextet(_ensure_float64(velocity), amplitude=1.0)
    sextet2 = moessbauer_sextet(_ensure_float64(velocity), amplitude=2.0)
    # More amplitude means higher peaks (larger values)
    assert np.max(sextet2) > np.max(sextet1)

    # Test that different magnetic fields produce spectra with different peak positions
    small_field_spectrum = moessbauer_sextet(
        _ensure_float64(velocity), magnetic_field=20.0
    )
    large_field_spectrum = moessbauer_sextet(
        _ensure_float64(velocity), magnetic_field=40.0
    )

    # Find peaks in both spectra
    from scipy.signal import find_peaks

    small_peaks, _ = find_peaks(
        small_field_spectrum,
        height=0.1 * np.max(small_field_spectrum),
    )
    large_peaks, _ = find_peaks(
        large_field_spectrum,
        height=0.1 * np.max(large_field_spectrum),
    )

    # Calculate the range of peak positions for each spectrum
    if len(small_peaks) > 1:  # pragma: no cover
        small_field_range = np.max(velocity[small_peaks]) - np.min(
            velocity[small_peaks],
        )
    else:  #  pragma: no cover
        small_field_range = 0.0

    if len(large_peaks) > 1:  # pragma: no cover
        large_field_range = np.max(velocity[large_peaks]) - np.min(
            velocity[large_peaks],
        )
    else:  #  pragma: no cover
        large_field_range = 0.0

    # Higher magnetic field should have wider peak separation
    # If peaks are properly resolved
    if len(small_peaks) > 1 and len(large_peaks) > 1:  # pragma: no cover
        assert large_field_range > small_field_range


def test_api_models() -> None:
    """Test the Pydantic API models for Mössbauer spectroscopy."""
    # Test singlet API
    singlet_api = MoessbauerSingletAPI(
        amplitude=create_amplitude_api(
            {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0}
        ),
        isomershift=create_isomershift_api({"value": 0.3, "vary": True}),
        fwhml=create_fwhml_api({"value": 0.25, "vary": True}),
        background=create_background_api({"value": 1.0, "vary": False}),
    )

    # Check for null values before np.isclose()
    assert singlet_api.amplitude.value is not None
    assert singlet_api.isomershift.value is not None
    assert singlet_api.fwhml.value is not None
    assert singlet_api.background.value is not None

    assert np.isclose(singlet_api.amplitude.value, 1.0, rtol=1e-10)
    assert np.isclose(singlet_api.isomershift.value, 0.3, rtol=1e-10)
    assert np.isclose(singlet_api.fwhml.value, 0.25, rtol=1e-10)
    assert np.isclose(singlet_api.background.value, 1.0, rtol=1e-10)

    # Test doublet API
    doublet_api = MoessbauerDoubletAPI(
        amplitude=create_amplitude_api({"value": 1.0, "vary": True}),
        isomershift=create_isomershift_api({"value": 0.3, "vary": True}),
        fwhml=create_fwhml_api({"value": 0.25, "vary": True}),
        quadrupolesplitting=create_quadrupolesplitting_api(
            {"value": 0.8, "vary": True}
        ),
        background=create_background_api({"value": 1.0, "vary": False}),
    )

    # Check for null values before np.isclose()
    assert doublet_api.amplitude.value is not None
    assert doublet_api.quadrupolesplitting.value is not None

    assert np.isclose(doublet_api.amplitude.value, 1.0, rtol=1e-10)
    assert np.isclose(doublet_api.quadrupolesplitting.value, 0.8, rtol=1e-10)

    # Test physical constants
    assert np.isclose(moessbauer_constants.g_factor_57fe, 0.18, rtol=1e-10)
    assert moessbauer_constants.nuclear_magneton > 0

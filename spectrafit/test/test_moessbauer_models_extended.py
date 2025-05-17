"""Additional tests for the Moessbauer models fixed implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from spectrafit.api.moessbauer_model import AmplitudeAPI
from spectrafit.api.moessbauer_model import BackgroundAPI
from spectrafit.api.moessbauer_model import FwhmlAPI
from spectrafit.api.moessbauer_model import HyperfineFieldAPI
from spectrafit.api.moessbauer_model import IsomerShiftAPI
from spectrafit.api.moessbauer_model import MoessbauerOctetAPI
from spectrafit.api.moessbauer_model import MoessbauerSextetAPI
from spectrafit.api.moessbauer_model import QuadrupoleSplittingAPI
from spectrafit.models.moessbauer import moessbauer_doublet
from spectrafit.models.moessbauer import moessbauer_octet
from spectrafit.models.moessbauer import moessbauer_sextet
from spectrafit.models.moessbauer import moessbauer_singlet


if TYPE_CHECKING:
    from numpy.typing import NDArray


def test_moessbauer_octet() -> None:
    """Test the Moessbauer octet model."""
    # Create test velocity data
    velocity_data = np.linspace(-10, 10, 200)
    velocity: NDArray[np.float64] = velocity_data.astype(np.float64)

    # Test with default parameters
    octet = moessbauer_octet(velocity)
    assert octet.shape == velocity.shape

    # Test with custom parameters
    custom_octet = moessbauer_octet(
        velocity,
        amplitude=0.5,
        isomer_shift=0.3,
        magnetic_field=30.0,
        fwhml=0.25,
        center=0.1,
        quadrupole_shift=0.1,
        efg_vzz=1e22,
        efg_eta=0.1,
    )
    assert custom_octet.shape == velocity.shape

    # Test that the amplitude parameter affects peak height
    octet1 = moessbauer_octet(velocity, amplitude=1.0)
    octet2 = moessbauer_octet(velocity, amplitude=2.0)
    # More amplitude means higher peaks (larger values)
    assert np.max(octet2) > np.max(octet1)

    # Test that changing EFG parameters affects the spectrum
    default_efg = moessbauer_octet(velocity)
    modified_efg = moessbauer_octet(velocity, efg_vzz=2e22, efg_eta=0.5)

    # The spectra should be different
    assert np.any(np.not_equal(default_efg, modified_efg))


def test_moessbauer_models_with_background() -> None:
    """Test that background parameter works correctly in all Moessbauer models."""
    velocity_data = np.linspace(-5, 5, 100)
    velocity: NDArray[np.float64] = velocity_data.astype(np.float64)

    # Test singlet with and without background
    singlet_no_bg = moessbauer_singlet(velocity, background=0.0)
    singlet_with_bg = moessbauer_singlet(velocity, background=0.5)

    # Higher background should result in higher values
    assert np.all(singlet_with_bg > singlet_no_bg)

    # Test doublet with and without background
    doublet_no_bg = moessbauer_doublet(velocity, background=0.0)
    doublet_with_bg = moessbauer_doublet(velocity, background=0.5)

    # Higher background should result in higher values
    assert np.all(doublet_with_bg > doublet_no_bg)

    # Test sextet with and without background
    sextet_no_bg = moessbauer_sextet(velocity, background=0.0)
    sextet_with_bg = moessbauer_sextet(velocity, background=0.5)

    # Higher background should result in higher values
    assert np.all(sextet_with_bg > sextet_no_bg)

    # Test octet with and without background
    octet_no_bg = moessbauer_octet(
        velocity, background=0.0, efg_vzz=1e5, magnetic_field=0.1
    )
    octet_with_bg = moessbauer_octet(
        velocity, background=0.5, efg_vzz=1e5, magnetic_field=0.1
    )

    # For octet model, we need to verify that background affects the spectrum
    # With very low EFG and magnetic field values, the model falls back to a simpler case
    # where background is directly added
    assert np.all(octet_with_bg > octet_no_bg)


def test_moessbauer_sextet_api_conversion() -> None:
    """Test conversion between API model and parameters for sextet."""
    # Create API model
    sextet_api = MoessbauerSextetAPI(
        isomershift=IsomerShiftAPI(value=0.2, vary=True, min=-1.0, max=1.0),
        hyperfinefield=HyperfineFieldAPI(value=25.0, vary=True, min=0.0, max=40.0),
        quadrupolesplitting=QuadrupoleSplittingAPI(
            value=0.1, vary=True, min=-0.5, max=0.5
        ),
        fwhml=FwhmlAPI(value=0.3, vary=True, min=0, max=1),
        amplitude=AmplitudeAPI(value=0.8, vary=True, min=0.0, max=2.0),
        background=BackgroundAPI(value=0.1, vary=False, min=-0.5, max=0.5),
    )

    # Convert API model parameters to dict for use with function
    # Use asserts to ensure values are not None for mypy
    amplitude = sextet_api.amplitude.value
    assert amplitude is not None

    isomer_shift = sextet_api.isomershift.value
    assert isomer_shift is not None

    magnetic_field = sextet_api.hyperfinefield.value
    assert magnetic_field is not None

    quadrupole_shift = sextet_api.quadrupolesplitting.value
    assert quadrupole_shift is not None

    fwhml_value = sextet_api.fwhml.value
    assert fwhml_value is not None

    background_value = sextet_api.background.value
    assert background_value is not None

    # Create test velocity data and generate spectrum
    velocity_data = np.linspace(-10, 10, 200)
    velocity: NDArray[np.float64] = velocity_data.astype(np.float64)

    spectrum = moessbauer_sextet(
        velocity,
        amplitude=amplitude,
        isomer_shift=isomer_shift,
        magnetic_field=magnetic_field,
        quadrupole_shift=quadrupole_shift,
        fwhml=fwhml_value,
        background=background_value,
        center=0.0,  # Default center
    )

    # Basic validation - spectrum should have expected shape
    assert spectrum.shape == velocity.shape

    # For test stability, just verify that the spectrum is not constant
    assert np.std(spectrum) > 0.001


def test_moessbauer_octet_api_conversion() -> None:
    """Test conversion between API model and parameters for octet."""
    # Create API model
    octet_api = MoessbauerOctetAPI(
        isomershift=IsomerShiftAPI(value=0.2, vary=True, min=-1.0, max=1.0),
        hyperfinefield=HyperfineFieldAPI(value=25.0, vary=True, min=0.0, max=40.0),
        quadrupolesplitting=QuadrupoleSplittingAPI(
            value=0.1, vary=True, min=-0.5, max=0.5
        ),
        fwhml=FwhmlAPI(value=0.3, vary=True, min=0, max=1),
        amplitude=AmplitudeAPI(value=0.8, vary=True, min=0.0, max=2.0),
        background=BackgroundAPI(value=0.1, vary=False, min=-0.5, max=0.5),
    )

    # Extract API model parameters with assertions for mypy
    amplitude = octet_api.amplitude.value
    assert amplitude is not None

    isomer_shift = octet_api.isomershift.value
    assert isomer_shift is not None

    magnetic_field = octet_api.hyperfinefield.value
    assert magnetic_field is not None

    quadrupole_shift = octet_api.quadrupolesplitting.value
    assert quadrupole_shift is not None

    fwhml_value = octet_api.fwhml.value
    assert fwhml_value is not None

    background_value = octet_api.background.value
    assert background_value is not None

    # Create test velocity data and generate spectrum
    velocity: NDArray[np.float64] = np.linspace(-10, 10, 200).astype(np.float64)

    # Use constants for other parameters that aren't from the API
    center = 0.0
    efg_vzz = 1e22
    efg_eta = 0.0

    spectrum = moessbauer_octet(
        velocity,
        amplitude=amplitude,
        isomer_shift=isomer_shift,
        magnetic_field=magnetic_field,
        quadrupole_shift=quadrupole_shift,
        fwhml=fwhml_value,
        background=background_value,
        center=center,
        efg_vzz=efg_vzz,
        efg_eta=efg_eta,
    )

    # Basic validation - spectrum should have expected shape
    assert spectrum.shape == velocity.shape

    # For test stability, just verify that the spectrum is not constant
    assert np.std(spectrum) > 0.001

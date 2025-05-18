"""Test the API models for Mössbauer spectroscopy."""

from __future__ import annotations

import numpy as np
import pytest

from pydantic import ValidationError

from spectrafit.api.model_utils import create_amplitude_api
from spectrafit.api.model_utils import create_background_api
from spectrafit.api.model_utils import create_fwhml_api
from spectrafit.api.model_utils import create_isomershift_api
from spectrafit.api.moessbauer_model import MoessbauerDoubletAPI
from spectrafit.api.moessbauer_model import MoessbauerOctetAPI
from spectrafit.api.moessbauer_model import MoessbauerSextetAPI
from spectrafit.api.moessbauer_model import MoessbauerSingletAPI
from spectrafit.api.physical_constants import moessbauer_constants


@pytest.mark.api
@pytest.mark.moessbauer
def test_moessbauer_singlet_api_valid(
    moessbauer_singlet_api: MoessbauerSingletAPI,
) -> None:
    """Test that a valid MoessbauerSingletAPI can be created.

    Args:
        moessbauer_singlet_api: A fixture providing a valid MoessbauerSingletAPI instance
    """
    # The fixture should have successfully created a valid model
    assert isinstance(moessbauer_singlet_api, MoessbauerSingletAPI)

    # Check that the model has the expected fields
    assert moessbauer_singlet_api.isomershift is not None
    assert moessbauer_singlet_api.fwhml is not None
    assert moessbauer_singlet_api.amplitude is not None

    # Check that the values are as expected
    assert moessbauer_singlet_api.isomershift.value is not None
    assert np.isclose(moessbauer_singlet_api.isomershift.value, 0.3, rtol=1e-10)
    assert moessbauer_singlet_api.isomershift.vary is True
    assert moessbauer_singlet_api.fwhml.value is not None
    assert np.isclose(moessbauer_singlet_api.fwhml.value, 0.2, rtol=1e-10)


@pytest.mark.api
@pytest.mark.moessbauer
def test_moessbauer_singlet_api_invalid() -> None:
    """Test that invalid values raise ValidationError."""
    # Test with invalid isomershift value - here we can use the raw dict
    # since we're testing the validation itself
    with pytest.raises(ValidationError):
        MoessbauerSingletAPI(
            isomershift=create_isomershift_api(
                {"min": -2.0, "max": 2.0, "value": "invalid", "vary": True}  # type: ignore
            ),
            fwhml=create_fwhml_api(
                {"min": 0.05, "max": 0.5, "value": 0.2, "vary": True}
            ),
            amplitude=create_amplitude_api(
                {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True}
            ),
            background=create_background_api(
                {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
            ),
        )


@pytest.mark.api
@pytest.mark.moessbauer
def test_moessbauer_doublet_api_valid(
    moessbauer_doublet_api: MoessbauerDoubletAPI,
) -> None:
    """Test that a valid MoessbauerDoubletAPI can be created.

    Args:
        moessbauer_doublet_api: A fixture providing a valid MoessbauerDoubletAPI instance
    """
    # The fixture should have successfully created a valid model
    assert isinstance(moessbauer_doublet_api, MoessbauerDoubletAPI)

    # Check that the model has the expected fields
    assert moessbauer_doublet_api.isomershift is not None
    assert moessbauer_doublet_api.quadrupolesplitting is not None
    assert moessbauer_doublet_api.fwhml is not None

    # Check that the values are as expected
    assert moessbauer_doublet_api.isomershift.value is not None
    assert np.isclose(moessbauer_doublet_api.isomershift.value, 0.4, rtol=1e-10)
    assert moessbauer_doublet_api.quadrupolesplitting.value is not None
    assert np.isclose(moessbauer_doublet_api.quadrupolesplitting.value, 0.8, rtol=1e-10)
    assert moessbauer_doublet_api.fwhml.value is not None
    assert np.isclose(moessbauer_doublet_api.fwhml.value, 0.2, rtol=1e-10)


@pytest.mark.api
@pytest.mark.moessbauer
def test_moessbauer_sextet_api_valid(
    moessbauer_sextet_api: MoessbauerSextetAPI,
) -> None:
    """Test that a valid MoessbauerSextetAPI can be created.

    Args:
        moessbauer_sextet_api: A fixture providing a valid MoessbauerSextetAPI instance
    """
    # The fixture should have successfully created a valid model
    assert isinstance(moessbauer_sextet_api, MoessbauerSextetAPI)

    # Check that the model has all expected fields
    assert moessbauer_sextet_api.isomershift is not None
    assert moessbauer_sextet_api.hyperfinefield is not None
    assert moessbauer_sextet_api.quadrupolesplitting is not None
    assert moessbauer_sextet_api.fwhml is not None

    # Check specific values
    assert moessbauer_sextet_api.hyperfinefield.value is not None
    assert np.isclose(moessbauer_sextet_api.hyperfinefield.value, 33.0, rtol=1e-10)
    assert moessbauer_sextet_api.hyperfinefield.vary is True


@pytest.mark.api
@pytest.mark.moessbauer
def test_moessbauer_octet_api_valid(moessbauer_octet_api: MoessbauerOctetAPI) -> None:
    """Test that a valid MoessbauerOctetAPI can be created.

    Args:
        moessbauer_octet_api: A fixture providing a valid MoessbauerOctetAPI instance
    """
    # The fixture should have successfully created a valid model
    assert isinstance(moessbauer_octet_api, MoessbauerOctetAPI)

    # Check that the model has all the expected fields
    assert moessbauer_octet_api.isomershift is not None
    assert moessbauer_octet_api.hyperfinefield is not None
    assert moessbauer_octet_api.quadrupolesplitting is not None

    # Check specific values
    assert moessbauer_octet_api.hyperfinefield.value is not None
    assert np.isclose(moessbauer_octet_api.hyperfinefield.value, 33.0, rtol=1e-10)
    # Note: efg_vzz and efg_eta are no longer part of the base octet model


@pytest.mark.api
@pytest.mark.moessbauer
def test_constants_correctness() -> None:
    """Test that physical constants have correct values."""
    # Check that the physical constants are correctly defined
    assert moessbauer_constants.nuclear_magneton > 0
    assert moessbauer_constants.gamma_57fe > 0
    assert 0 < moessbauer_constants.g_factor_57fe < 1
    assert moessbauer_constants.quadrupole_moment_57fe > 0

    # Check that the conversion constants are correct
    assert moessbauer_constants.conversion_mm_s_to_ev > 0
    assert moessbauer_constants.ev_to_mm_s > 0

    # They should be reciprocals of each other
    assert np.isclose(
        moessbauer_constants.conversion_mm_s_to_ev * moessbauer_constants.ev_to_mm_s,
        1.0,
        rtol=1e-10,
    )

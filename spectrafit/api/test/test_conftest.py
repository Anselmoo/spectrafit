"""Test the conftest.py fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np


if TYPE_CHECKING:
    from spectrafit.api.moessbauer_model import MoessbauerDoubletAPI
    from spectrafit.api.moessbauer_model import MoessbauerOctetAPI
    from spectrafit.api.moessbauer_model import MoessbauerSextetAPI
    from spectrafit.api.moessbauer_model import MoessbauerSingletAPI


def test_moessbauer_singlet_api_validation(
    moessbauer_singlet_api: MoessbauerSingletAPI,
) -> None:
    """Test validation in the MoessbauerSingletAPI fixture.

    Args:
        moessbauer_singlet_api: The fixture to test
    """
    # Check parameter boundaries
    assert moessbauer_singlet_api.isomershift.min == -2
    assert moessbauer_singlet_api.isomershift.max == 2
    assert moessbauer_singlet_api.fwhml.min == 1
    assert moessbauer_singlet_api.fwhml.max is not None
    assert moessbauer_singlet_api.fwhml.min is not None
    assert np.isclose(
        moessbauer_singlet_api.fwhml.max, 0.5, rtol=1e-10
    )  # This is intentionally inverted in the fixture

    # Test conversion to dictionary
    model_dict = moessbauer_singlet_api.model_dump()
    assert "isomershift" in model_dict
    assert "fwhml" in model_dict
    assert "amplitude" in model_dict
    assert "background" in model_dict


def test_moessbauer_doublet_api_validation(
    moessbauer_doublet_api: MoessbauerDoubletAPI,
) -> None:
    """Test validation in the MoessbauerDoubletAPI fixture.

    Args:
        moessbauer_doublet_api: The fixture to test
    """
    # Check that quadrupolesplitting is defined correctly
    assert moessbauer_doublet_api.quadrupolesplitting.min is not None
    assert np.isclose(moessbauer_doublet_api.quadrupolesplitting.min, 0.0, rtol=1e-10)
    assert moessbauer_doublet_api.quadrupolesplitting.max is not None
    assert np.isclose(moessbauer_doublet_api.quadrupolesplitting.max, 3.0, rtol=1e-10)
    assert moessbauer_doublet_api.quadrupolesplitting.vary is True

    # Check that all required parameters are present
    assert hasattr(moessbauer_doublet_api, "isomershift")
    assert hasattr(moessbauer_doublet_api, "quadrupolesplitting")
    assert hasattr(moessbauer_doublet_api, "fwhml")
    assert hasattr(moessbauer_doublet_api, "amplitude")
    assert hasattr(moessbauer_doublet_api, "background")


def test_moessbauer_sextet_api_validation(
    moessbauer_sextet_api: MoessbauerSextetAPI,
) -> None:
    """Test validation in the MoessbauerSextetAPI fixture.

    Args:
        moessbauer_sextet_api: The fixture to test
    """
    # Check that hyperfinefield is defined correctly
    assert moessbauer_sextet_api.hyperfinefield.min is not None
    assert np.isclose(moessbauer_sextet_api.hyperfinefield.min, 0.0, rtol=1e-10)
    assert moessbauer_sextet_api.hyperfinefield.max is not None
    assert np.isclose(moessbauer_sextet_api.hyperfinefield.max, 40.0, rtol=1e-10)
    assert moessbauer_sextet_api.hyperfinefield.vary is True

    # Check that quadrupolesplitting is not varying
    assert moessbauer_sextet_api.quadrupolesplitting.vary is False
    assert moessbauer_sextet_api.quadrupolesplitting.value is not None
    assert np.isclose(moessbauer_sextet_api.quadrupolesplitting.value, 0.0, rtol=1e-10)


def test_moessbauer_octet_api_validation(
    moessbauer_octet_api: MoessbauerOctetAPI,
) -> None:
    """Test validation in the MoessbauerOctetAPI fixture.

    Args:
        moessbauer_octet_api: The fixture to test
    """
    # Check that all parameters have the correct values
    assert moessbauer_octet_api.isomershift.value is not None
    assert moessbauer_octet_api.hyperfinefield.value is not None
    assert moessbauer_octet_api.quadrupolesplitting.value is not None
    assert moessbauer_octet_api.fwhml.value is not None
    assert moessbauer_octet_api.amplitude.value is not None
    assert moessbauer_octet_api.background.value is not None

    assert np.isclose(moessbauer_octet_api.isomershift.value, 0.0, rtol=1e-10)
    assert np.isclose(moessbauer_octet_api.hyperfinefield.value, 33.0, rtol=1e-10)
    assert np.isclose(moessbauer_octet_api.quadrupolesplitting.value, 0.0, rtol=1e-10)
    assert np.isclose(moessbauer_octet_api.fwhml.value, 0.25, rtol=1e-10)
    assert np.isclose(moessbauer_octet_api.amplitude.value, 1.0, rtol=1e-10)
    assert np.isclose(moessbauer_octet_api.background.value, 0.0, rtol=1e-10)

    # Check that all parameters have correct vary flags
    assert moessbauer_octet_api.isomershift.vary is True
    assert moessbauer_octet_api.hyperfinefield.vary is True
    assert moessbauer_octet_api.quadrupolesplitting.vary is True
    assert moessbauer_octet_api.fwhml.vary is True
    assert moessbauer_octet_api.amplitude.vary is True
    assert moessbauer_octet_api.background.vary is False

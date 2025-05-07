"""Test configuration for API model testing."""

from __future__ import annotations

import pytest

from spectrafit.api.model_utils import create_amplitude_api
from spectrafit.api.model_utils import create_background_api
from spectrafit.api.model_utils import create_fwhml_api
from spectrafit.api.model_utils import create_hyperfinefield_api
from spectrafit.api.model_utils import create_isomershift_api
from spectrafit.api.model_utils import create_quadrupolesplitting_api
from spectrafit.api.moessbauer_model import MoessbauerDoubletAPI
from spectrafit.api.moessbauer_model import MoessbauerOctetAPI
from spectrafit.api.moessbauer_model import MoessbauerSextetAPI
from spectrafit.api.moessbauer_model import MoessbauerSingletAPI


@pytest.fixture
def moessbauer_singlet_api() -> MoessbauerSingletAPI:
    """Create a MoessbauerSingletAPI instance for testing.

    Returns:
        MoessbauerSingletAPI: A properly configured singlet API model
    """
    return MoessbauerSingletAPI(
        isomershift=create_isomershift_api(
            {"min": -2, "max": 2, "value": 0.3, "vary": True}
        ),
        fwhml=create_fwhml_api({"min": 1, "max": 0.5, "value": 0.2, "vary": True}),
        amplitude=create_amplitude_api(
            {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True}
        ),
        background=create_background_api(
            {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
        ),
    )


@pytest.fixture
def moessbauer_doublet_api() -> MoessbauerDoubletAPI:
    """Create a MoessbauerDoubletAPI instance for testing.

    Returns:
        MoessbauerDoubletAPI: A properly configured doublet API model
    """
    return MoessbauerDoubletAPI(
        isomershift=create_isomershift_api(
            {"min": -2, "max": 2, "value": 0.4, "vary": True}
        ),
        quadrupolesplitting=create_quadrupolesplitting_api(
            {"min": 0.0, "max": 3.0, "value": 0.8, "vary": True}
        ),
        fwhml=create_fwhml_api({"min": 1, "max": 0.5, "value": 0.2, "vary": True}),
        amplitude=create_amplitude_api(
            {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True}
        ),
        background=create_background_api(
            {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
        ),
    )


@pytest.fixture
def moessbauer_sextet_api() -> MoessbauerSextetAPI:
    """Create a MoessbauerSextetAPI instance for testing.

    Returns:
        MoessbauerSextetAPI: A properly configured sextet API model
    """
    return MoessbauerSextetAPI(
        isomershift=create_isomershift_api(
            {"min": -2, "max": 2, "value": 0.0, "vary": True}
        ),
        hyperfinefield=create_hyperfinefield_api(
            {"min": 0.0, "max": 40.0, "value": 33.0, "vary": True}
        ),
        fwhml=create_fwhml_api({"min": 1, "max": 0.5, "value": 0.25, "vary": True}),
        amplitude=create_amplitude_api(
            {"min": 0.5, "max": 2.0, "value": 1.0, "vary": True}
        ),
        background=create_background_api(
            {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
        ),
        quadrupolesplitting=create_quadrupolesplitting_api(
            {"min": -1.0, "max": 1.0, "value": 0.0, "vary": False}
        ),
    )


@pytest.fixture
def moessbauer_octet_api() -> MoessbauerOctetAPI:
    """Create a MoessbauerOctetAPI instance for testing.

    Returns:
        MoessbauerOctetAPI: A properly configured octet API model
    """
    return MoessbauerOctetAPI(
        isomershift=create_isomershift_api(
            {"min": -2.0, "max": 2.0, "vary": True, "value": 0.0}
        ),
        hyperfinefield=create_hyperfinefield_api(
            {"min": 0.0, "max": 40.0, "vary": True, "value": 33.0}
        ),
        quadrupolesplitting=create_quadrupolesplitting_api(
            {"min": -1.0, "max": 1.0, "vary": True, "value": 0.0}
        ),
        fwhml=create_fwhml_api({"min": 1, "max": 0.5, "vary": True, "value": 0.25}),
        amplitude=create_amplitude_api(
            {"min": 0.5, "max": 1.5, "vary": True, "value": 1.0}
        ),
        background=create_background_api(
            {"min": -1.0, "max": 1.0, "vary": False, "value": 0.0}
        ),
    )

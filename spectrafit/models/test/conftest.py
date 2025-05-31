"""Test configuration for models testing."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from spectrafit.models.builtin import DistributionModels


if TYPE_CHECKING:
    from numpy.typing import NDArray


@pytest.fixture
def velocity_data() -> NDArray[np.float64]:
    """Create test velocity data for Mössbauer model testing.

    Returns:
        np.ndarray: Array of velocity values in mm/s, ranging from -10 to 10.
    """
    return np.linspace(-10, 10, 200).astype(np.float64)


@pytest.fixture
def energy_data() -> NDArray[np.float64]:
    """Create test energy data for regular model testing.

    Returns:
        np.ndarray: Array of energy values in eV, ranging from 0 to 10.
    """
    return np.linspace(0, 10, 200).astype(np.float64)


@pytest.fixture
def distribution_model_instance() -> DistributionModels:
    """Create a DistributionModels instance for testing.

    Returns:
        DistributionModels: Instance of the DistributionModels class
    """
    return DistributionModels()


@pytest.fixture
def moessbauer_singlet_params() -> dict[str, float]:
    """Create parameters for testing the Mössbauer singlet model.

    Returns:
        Dict[str, float]: Dictionary of parameter values
    """
    return {
        "amplitude": 1.0,
        "center": 0.0,
        "fwhml": 0.2,
        "background": 0.1,
        "isomer_shift": 0.0,
    }


@pytest.fixture
def moessbauer_doublet_params() -> dict[str, float]:
    """Create parameters for testing the Mössbauer doublet model.

    Returns:
        Dict[str, float]: Dictionary of parameter values
    """
    return {
        "amplitude": 1.0,
        "center": 0.0,
        "fwhml": 0.25,
        "background": 0.1,
        "isomer_shift": 0.3,
        "quadrupole_splitting": 1.0,
    }


@pytest.fixture
def moessbauer_sextet_params() -> dict[str, float]:
    """Create parameters for testing the Mössbauer sextet model.

    Returns:
        Dict[str, float]: Dictionary of parameter values
    """
    return {
        "amplitude": 1.0,
        "center": 0.0,
        "fwhml": 0.25,
        "background": 0.1,
        "isomer_shift": 0.0,
        "magnetic_field": 33.0,
        "quadrupole_shift": 0.0,
    }


@pytest.fixture
def moessbauer_octet_params() -> dict[str, float]:
    """Create parameters for testing the Mössbauer octet model.

    Returns:
        Dict[str, float]: Dictionary of parameter values
    """
    return {
        "amplitude": 1.0,
        "center": 0.0,
        "fwhml": 0.25,
        "background": 0.1,
        "isomer_shift": 0.0,
        "magnetic_field": 33.0,
        "quadrupole_shift": 0.0,
        "efg_vzz": 1e22,
        "efg_eta": 0.0,
    }

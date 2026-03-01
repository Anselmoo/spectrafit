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
    """Create test velocity data for model testing.

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

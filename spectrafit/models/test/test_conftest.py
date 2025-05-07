"""Test the models/test/conftest.py fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Dict

import numpy as np

from spectrafit.models.builtin import DistributionModels


if TYPE_CHECKING:
    from numpy.typing import NDArray


def test_velocity_data(velocity_data: NDArray[np.float64]) -> None:
    """Test that velocity_data fixture returns expected array.

    Args:
        velocity_data: The fixture to test
    """
    assert isinstance(velocity_data, np.ndarray)
    assert len(velocity_data) == 200
    assert velocity_data.min() == -10
    assert velocity_data.max() == 10
    assert np.isclose(velocity_data[0], -10.0, rtol=1e-10)
    assert np.isclose(velocity_data[-1], 10.0, rtol=1e-10)


def test_energy_data(energy_data: NDArray[np.float64]) -> None:
    """Test that energy_data fixture returns expected array.

    Args:
        energy_data: The fixture to test
    """
    assert isinstance(energy_data, np.ndarray)
    assert len(energy_data) == 200
    assert energy_data.min() == 0
    assert energy_data.max() == 10
    assert np.isclose(energy_data[0], 0.0, rtol=1e-10)
    assert np.isclose(energy_data[-1], 10.0, rtol=1e-10)


def test_moessbauer_singlet_params(moessbauer_singlet_params: Dict[str, float]) -> None:
    """Test that moessbauer_singlet_params fixture returns expected dictionary.

    Args:
        moessbauer_singlet_params: The fixture to test
    """
    assert isinstance(moessbauer_singlet_params, dict)

    # Check that all required keys are present
    required_keys = ["amplitude", "center", "fwhml", "background", "isomer_shift"]
    for key in required_keys:
        assert key in moessbauer_singlet_params

    # Check parameter values
    assert np.isclose(moessbauer_singlet_params["amplitude"], 1.0, rtol=1e-10)
    assert np.isclose(moessbauer_singlet_params["center"], 0.0, rtol=1e-10)
    assert np.isclose(moessbauer_singlet_params["fwhml"], 0.2, rtol=1e-10)
    assert np.isclose(moessbauer_singlet_params["background"], 0.1, rtol=1e-10)
    assert np.isclose(moessbauer_singlet_params["isomer_shift"], 0.0, rtol=1e-10)


def test_moessbauer_doublet_params(moessbauer_doublet_params: Dict[str, float]) -> None:
    """Test that moessbauer_doublet_params fixture returns expected dictionary.

    Args:
        moessbauer_doublet_params: The fixture to test
    """
    assert isinstance(moessbauer_doublet_params, dict)

    # Check that all required keys are present
    required_keys = [
        "amplitude",
        "center",
        "fwhml",
        "background",
        "isomer_shift",
        "quadrupole_splitting",
    ]
    for key in required_keys:
        assert key in moessbauer_doublet_params

    # Check parameter values
    assert np.isclose(moessbauer_doublet_params["amplitude"], 1.0, rtol=1e-10)
    assert np.isclose(moessbauer_doublet_params["isomer_shift"], 0.3, rtol=1e-10)
    assert np.isclose(
        moessbauer_doublet_params["quadrupole_splitting"], 1.0, rtol=1e-10
    )


def test_moessbauer_sextet_params(moessbauer_sextet_params: Dict[str, float]) -> None:
    """Test that moessbauer_sextet_params fixture returns expected dictionary.

    Args:
        moessbauer_sextet_params: The fixture to test
    """
    assert isinstance(moessbauer_sextet_params, dict)

    # Check that all required keys are present
    required_keys = [
        "amplitude",
        "center",
        "fwhml",
        "background",
        "isomer_shift",
        "magnetic_field",
        "quadrupole_shift",
    ]
    for key in required_keys:
        assert key in moessbauer_sextet_params

    # Check parameter values
    assert np.isclose(moessbauer_sextet_params["amplitude"], 1.0, rtol=1e-10)
    assert np.isclose(moessbauer_sextet_params["magnetic_field"], 33.0, rtol=1e-10)
    assert np.isclose(moessbauer_sextet_params["quadrupole_shift"], 0.0, rtol=1e-10)


def test_moessbauer_octet_params(moessbauer_octet_params: Dict[str, float]) -> None:
    """Test that moessbauer_octet_params fixture returns expected dictionary.

    Args:
        moessbauer_octet_params: The fixture to test
    """
    assert isinstance(moessbauer_octet_params, dict)

    # Check that all required keys are present
    required_keys = [
        "amplitude",
        "center",
        "fwhml",
        "background",
        "isomer_shift",
        "magnetic_field",
        "quadrupole_shift",
        "efg_vzz",
        "efg_eta",
    ]
    for key in required_keys:
        assert key in moessbauer_octet_params

    # Check parameter values
    assert np.isclose(moessbauer_octet_params["amplitude"], 1.0, rtol=1e-10)
    assert np.isclose(moessbauer_octet_params["magnetic_field"], 33.0, rtol=1e-10)
    assert np.isclose(moessbauer_octet_params["efg_vzz"], 1e22, rtol=1e-10)
    assert np.isclose(moessbauer_octet_params["efg_eta"], 0.0, rtol=1e-10)


def test_distribution_model_instance(
    distribution_model_instance: DistributionModels,
) -> None:
    """Test the distribution_model_instance fixture.

    Args:
        distribution_model_instance: The fixture to test
    """
    assert isinstance(distribution_model_instance, DistributionModels)

    # Test that we can call some methods on the instance
    assert hasattr(distribution_model_instance, "gaussian")
    assert hasattr(distribution_model_instance, "lorentzian")
    assert hasattr(distribution_model_instance, "voigt")

    # Test that the instance can generate spectra correctly
    x_data: NDArray[np.float64] = np.linspace(-5, 5, 100).astype(np.float64)
    y_data = distribution_model_instance.gaussian(
        x_data, amplitude=1.0, center=0.0, fwhmg=1.0
    )
    assert len(y_data) == len(x_data)
    assert np.isclose(
        np.max(y_data), 0.933, rtol=1e-2
    )  # Check amplitude is approximately correct

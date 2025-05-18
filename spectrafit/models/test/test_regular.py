"""Test the regular distribution models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from scipy.signal import find_peaks

from spectrafit.models.regular import FWHMG2SIG
from spectrafit.models.regular import FWHML2SIG
from spectrafit.models.regular import FWHMV2SIG
from spectrafit.models.regular import gaussian
from spectrafit.models.regular import lorentzian


if TYPE_CHECKING:
    from numpy.typing import NDArray

    from spectrafit.models.builtin import DistributionModels


@pytest.mark.models
@pytest.mark.parametrize(
    ("function_name", "expected_peaks"),
    [
        ("gaussian", 1),
        ("lorentzian", 1),
        ("pseudovoigt", 1),
        ("voigt", 1),
        ("pearson1", 1),  # Renamed from pearson7
        # "students_t" function doesn't exist - removing it
    ],
)
def test_peak_functions_produce_single_peak(
    energy_data: NDArray[np.float64],
    distribution_model_instance: DistributionModels,
    function_name: str,
    expected_peaks: int,
) -> None:
    """Test that peak functions produce the expected number of peaks.

    Args:
        energy_data: Array of energy values
        distribution_model_instance: Instance of DistributionModels class
        function_name: Name of the model function to test
        expected_peaks: Expected number of peaks
    """
    # Get the function from the distribution_model_instance
    model_func = getattr(distribution_model_instance, function_name)

    # Parameters dictionary based on function name
    params = {
        "amplitude": 1.0,
        "center": 5.0,  # Center in the middle of the range
    }

    # Add specific parameters based on the function
    if function_name == "gaussian":
        params["fwhmg"] = 0.5
    elif function_name == "lorentzian":
        params["fwhml"] = 0.5
    elif function_name == "pseudovoigt":
        params["fwhmg"] = 0.5
        params["fwhml"] = 0.5
    elif function_name == "voigt":
        params["gamma"] = (
            0.5 * FWHML2SIG
        )  # Convert FWHM to gamma for Lorentzian component
        # drop the "amplitude" parameter
        params.pop("amplitude", None)
    elif function_name == "pearson1":
        params["sigma"] = 0.5
        params["exponent"] = 1.0

    # Call the function with appropriate parameters
    result = model_func(energy_data, **params)

    # Use find_peaks to identify peaks in the result
    peaks, _ = find_peaks(result, height=0.1)

    # Should find exactly the expected number of peaks
    assert len(peaks) == expected_peaks


@pytest.mark.models
@pytest.mark.parametrize("center", [2.0, 5.0, 8.0])
def test_gaussian_peak_location(
    energy_data: NDArray[np.float64], center: float
) -> None:
    """Test that the Gaussian peak is located at the center.

    Args:
        energy_data: Array of energy values
        center: Center position for the peak
    """
    result = gaussian(energy_data, amplitude=1.0, center=center, fwhmg=0.5)
    peak_idx = np.argmax(result)
    peak_position = energy_data[peak_idx]

    # The peak should be at the specified center (within numerical precision)
    assert np.isclose(peak_position, center, atol=0.1)


@pytest.mark.models
@pytest.mark.parametrize("fwhm", [0.2, 0.5, 1.0])
def test_lorentzian_fwhm(energy_data: NDArray[np.float64], fwhm: float) -> None:
    """Test that the Lorentzian FWHM is correctly applied.

    Args:
        energy_data: Array of energy values
        fwhm: Full Width at Half Maximum value to test
    """
    center = 5.0
    result = lorentzian(energy_data, amplitude=1.0, center=center, fwhml=fwhm)

    # Find the peak maximum
    peak_max = np.max(result)
    half_max = peak_max / 2.0

    # Find points where the function crosses half maximum
    crosses_half_max = []
    for i in range(1, len(result)):
        if (result[i - 1] < half_max and result[i] >= half_max) or (
            result[i - 1] >= half_max and result[i] < half_max
        ):
            # Linear interpolation to find more precise crossing point
            x1, x2 = energy_data[i - 1], energy_data[i]
            y1, y2 = result[i - 1], result[i]
            x_interp = x1 + (half_max - y1) * (x2 - x1) / (y2 - y1)
            crosses_half_max.append(x_interp)

    # Should find exactly two crossing points for a peak
    assert len(crosses_half_max) == 2

    # The distance between the crossing points should be the FWHM
    measured_fwhm = abs(crosses_half_max[1] - crosses_half_max[0])
    assert np.isclose(measured_fwhm, fwhm, rtol=0.1)


@pytest.mark.models
def test_constants_values() -> None:
    """Test that the conversion constants have correct values."""
    # Calculate expected values directly from formulas
    expected_fwhmg2sig = 1 / (2.0 * np.sqrt(2.0 * np.log(2.0)))
    expected_fwhml2sig = 0.5
    expected_fwhmv2sig = 1 / (2 * 0.5346 + 2 * np.sqrt(0.2166 + np.log(2) * 2))

    # Verify the values match the constants
    assert np.isclose(FWHMG2SIG, expected_fwhmg2sig, rtol=1e-10)
    assert np.isclose(FWHML2SIG, expected_fwhml2sig, rtol=1e-10)
    assert np.isclose(FWHMV2SIG, expected_fwhmv2sig, rtol=1e-10)

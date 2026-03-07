"""Root-level pytest configuration with shared fixtures and custom markers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pytest

from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum


if TYPE_CHECKING:
    from pathlib import Path

    import pandas as pd

    from numpy.typing import NDArray


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers for the test suite.

    Args:
        config: The pytest configuration object.
    """
    config.addinivalue_line("markers", "unit: fast unit tests (<1s each)")
    config.addinivalue_line(
        "markers", "integration: tests that invoke subprocesses or I/O"
    )
    config.addinivalue_line("markers", "e2e: end-to-end workflow tests")
    config.addinivalue_line("markers", "slow: tests taking >10s")
    config.addinivalue_line(
        "markers", "validation: scientific validation tests (Phase 5)"
    )


@pytest.fixture(scope="session")
def energy_axis() -> NDArray[np.float64]:
    """Provide a standard energy axis for spectrum tests.

    Returns:
        NDArray[np.float64]: 1000-point linspace from -10 to 10.
    """
    return np.linspace(-10, 10, 1000)


@pytest.fixture(scope="session")
def sample_gaussian_spectrum() -> SyntheticSpectrum:
    """Provide a single-Gaussian synthetic spectrum for reuse.

    Returns:
        SyntheticSpectrum: Spectrum with one Gaussian peak (seed=42).
    """
    return SyntheticSpectrum(
        x_min=-10.0,
        x_max=10.0,
        num_points=1000,
        noise_level=0.01,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
            ),
        ],
        seed=42,
    )


@pytest.fixture(scope="session")
def sample_multi_peak_spectrum() -> SyntheticSpectrum:
    """Provide a multi-peak synthetic spectrum for complex fitting tests.

    Returns:
        SyntheticSpectrum: Spectrum with Gaussian + Lorentzian + PseudoVoigt
            peaks (seed=42).
    """
    return SyntheticSpectrum(
        x_min=-10.0,
        x_max=10.0,
        num_points=1000,
        noise_level=0.01,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": -3.0, "fwhmg": 0.8},
            ),
            PeakDefinition(
                model="lorentzian",
                params={"amplitude": 0.8, "center": 0.0, "fwhml": 1.2},
            ),
            PeakDefinition(
                model="pseudovoigt",
                params={
                    "amplitude": 0.6,
                    "center": 3.0,
                    "fwhmg": 0.5,
                    "fwhml": 0.5,
                },
            ),
        ],
        seed=42,
    )


@pytest.fixture
def tmp_output_dir(tmp_path: Path) -> Path:
    """Provide a temporary output directory for test artifacts.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: A freshly created ``output`` subdirectory.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture(scope="session")
def sample_dataframe(
    sample_gaussian_spectrum: SyntheticSpectrum,
) -> pd.DataFrame:
    """Provide a DataFrame from the sample Gaussian spectrum.

    Args:
        sample_gaussian_spectrum: The session-scoped Gaussian spectrum fixture.

    Returns:
        pd.DataFrame: DataFrame with ``energy`` and ``intensity`` columns.
    """
    return sample_gaussian_spectrum.to_dataframe()

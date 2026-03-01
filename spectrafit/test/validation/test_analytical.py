"""Analytical ground-truth validation tests for SpectraFit.

These tests validate that fitting results are mathematically and physically
correct by comparing recovered parameters against known exact solutions
from synthetic spectra.
"""

from __future__ import annotations

from math import log
from math import pi
from math import sqrt
from typing import Any
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from spectrafit.generators.synthetic import ModelName
from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum
from spectrafit.models.solver import SolverModels


def _make_args(
    peaks: dict[str, Any],
    *,
    max_nfev: int = 2000,
    method: str = "leastsq",
) -> dict[str, Any]:
    """Build a standard args dict for SolverModels.

    Args:
        peaks: Peak parameter definitions in SpectraFit format.
        max_nfev: Maximum number of function evaluations.
        method: Optimization method.

    Returns:
        Complete args dictionary ready for SolverModels.
    """
    return {
        "column": ["energy", "intensity"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": True},
        "optimizer": {"max_nfev": max_nfev, "method": method},
        "peaks": peaks,
        "global_": 0,
    }


def _fit_single_peak(
    model: ModelName,
    true_params: dict[str, float],
    guess_peaks: dict[str, Any],
    *,
    x_min: float = -10.0,
    x_max: float = 10.0,
    num_points: int = 1000,
    noise_level: float = 0.0,
    seed: int = 42,
) -> tuple[Any, dict[str, float]]:
    """Generate synthetic data and fit a single peak.

    Args:
        model: Model name (e.g., "gaussian", "lorentzian").
        true_params: True parameter values for spectrum generation.
        guess_peaks: Initial guess in SpectraFit peak format.
        x_min: Lower bound of x-axis.
        x_max: Upper bound of x-axis.
        num_points: Number of data points.
        noise_level: Gaussian noise standard deviation.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (lmfit result, dict of fitted parameter values).
    """
    spectrum = SyntheticSpectrum(
        x_min=x_min,
        x_max=x_max,
        num_points=num_points,
        noise_level=noise_level,
        peaks=[PeakDefinition(model=model, params=true_params)],
        seed=seed,
    )
    x, y, _ = spectrum.generate()
    df = pd.DataFrame({"energy": x, "intensity": y})
    args = _make_args(guess_peaks)
    _, result = SolverModels(df=df, args=args)()

    fitted: dict[str, float] = {
        name: param.value for name, param in result.params.items()
    }
    return result, fitted


@pytest.mark.validation
class TestGaussianAreaRecovery:
    """Validate Gaussian area: area = amplitude * fwhmg * sqrt(pi / (4 ln2))."""

    true_amplitude: ClassVar[float] = 1.5
    true_center: ClassVar[float] = 0.0
    true_fwhmg: ClassVar[float] = 1.2

    def test_gaussian_area_analytical(self) -> None:
        """Fit a single Gaussian and verify the integrated area matches theory."""
        expected_area = self.true_amplitude * self.true_fwhmg * sqrt(pi / (4 * log(2)))

        _, fitted = _fit_single_peak(
            model="gaussian",
            true_params={
                "amplitude": self.true_amplitude,
                "center": self.true_center,
                "fwhmg": self.true_fwhmg,
            },
            guess_peaks={
                "1": {
                    "gaussian": {
                        "amplitude": {
                            "max": 3,
                            "min": 0,
                            "vary": True,
                            "value": 1.0,
                        },
                        "center": {
                            "max": 2,
                            "min": -2,
                            "vary": True,
                            "value": 0.1,
                        },
                        "fwhmg": {
                            "max": 3,
                            "min": 0.1,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                }
            },
        )

        recovered_area = (
            fitted["gaussian_amplitude_1"]
            * fitted["gaussian_fwhmg_1"]
            * sqrt(pi / (4 * log(2)))
        )
        np.testing.assert_allclose(recovered_area, expected_area, rtol=0.05)


@pytest.mark.validation
class TestGaussianFWHMRecovery:
    """Validate that Gaussian FWHM is recovered accurately."""

    def test_fwhmg_recovery(self) -> None:
        """Fit a Gaussian and verify fwhmg matches the true value."""
        true_fwhmg = 0.8

        _, fitted = _fit_single_peak(
            model="gaussian",
            true_params={"amplitude": 1.0, "center": 0.0, "fwhmg": true_fwhmg},
            guess_peaks={
                "1": {
                    "gaussian": {
                        "amplitude": {
                            "max": 2,
                            "min": 0,
                            "vary": True,
                            "value": 0.8,
                        },
                        "center": {
                            "max": 2,
                            "min": -2,
                            "vary": True,
                            "value": 0.1,
                        },
                        "fwhmg": {
                            "max": 3,
                            "min": 0.1,
                            "vary": True,
                            "value": 0.6,
                        },
                    }
                }
            },
        )

        np.testing.assert_allclose(fitted["gaussian_fwhmg_1"], true_fwhmg, rtol=0.05)


@pytest.mark.validation
class TestLorentzianAreaRecovery:
    """Validate Lorentzian area: area = amplitude * pi * fwhml / 2."""

    true_amplitude: ClassVar[float] = 2.0
    true_center: ClassVar[float] = 0.5
    true_fwhml: ClassVar[float] = 0.6

    def test_lorentzian_area_analytical(self) -> None:
        """Fit a Lorentzian and verify integrated area matches theory."""
        expected_area = self.true_amplitude * pi * self.true_fwhml / 2

        _, fitted = _fit_single_peak(
            model="lorentzian",
            true_params={
                "amplitude": self.true_amplitude,
                "center": self.true_center,
                "fwhml": self.true_fwhml,
            },
            guess_peaks={
                "1": {
                    "lorentzian": {
                        "amplitude": {
                            "max": 4,
                            "min": 0,
                            "vary": True,
                            "value": 1.5,
                        },
                        "center": {
                            "max": 2,
                            "min": -2,
                            "vary": True,
                            "value": 0.3,
                        },
                        "fwhml": {
                            "max": 2,
                            "min": 0.1,
                            "vary": True,
                            "value": 0.5,
                        },
                    }
                }
            },
        )

        recovered_area = (
            fitted["lorentzian_amplitude_1"] * pi * fitted["lorentzian_fwhml_1"] / 2
        )
        np.testing.assert_allclose(recovered_area, expected_area, rtol=0.05)


@pytest.mark.validation
class TestCenterRecovery:
    """Validate center parameter recovery across all peak models."""

    @pytest.mark.parametrize(
        ("model", "true_params", "guess_peaks"),
        [
            pytest.param(
                "gaussian",
                {"amplitude": 1.0, "center": 1.5, "fwhmg": 1.0},
                {
                    "1": {
                        "gaussian": {
                            "amplitude": {
                                "max": 3,
                                "min": 0,
                                "vary": True,
                                "value": 0.8,
                            },
                            "center": {
                                "max": 5,
                                "min": -5,
                                "vary": True,
                                "value": 1.0,
                            },
                            "fwhmg": {
                                "max": 3,
                                "min": 0.1,
                                "vary": True,
                                "value": 0.8,
                            },
                        }
                    }
                },
                id="gaussian",
            ),
            pytest.param(
                "lorentzian",
                {"amplitude": 1.0, "center": -0.5, "fwhml": 1.0},
                {
                    "1": {
                        "lorentzian": {
                            "amplitude": {
                                "max": 3,
                                "min": 0,
                                "vary": True,
                                "value": 0.8,
                            },
                            "center": {
                                "max": 5,
                                "min": -5,
                                "vary": True,
                                "value": -0.3,
                            },
                            "fwhml": {
                                "max": 3,
                                "min": 0.1,
                                "vary": True,
                                "value": 0.8,
                            },
                        }
                    }
                },
                id="lorentzian",
            ),
            pytest.param(
                "voigt",
                {"center": 0.8, "fwhmv": 1.0, "gamma": 0.5},
                {
                    "1": {
                        "voigt": {
                            "center": {
                                "max": 5,
                                "min": -5,
                                "vary": True,
                                "value": 0.5,
                            },
                            "fwhmv": {
                                "max": 3,
                                "min": 0.1,
                                "vary": True,
                                "value": 0.8,
                            },
                            "gamma": {
                                "max": 2,
                                "min": 0.01,
                                "vary": True,
                                "value": 0.3,
                            },
                        }
                    }
                },
                id="voigt",
            ),
            pytest.param(
                "pseudovoigt",
                {
                    "amplitude": 1.0,
                    "center": 2.0,
                    "fwhmg": 1.0,
                    "fwhml": 1.0,
                },
                {
                    "1": {
                        "pseudovoigt": {
                            "amplitude": {
                                "max": 3,
                                "min": 0,
                                "vary": True,
                                "value": 0.8,
                            },
                            "center": {
                                "max": 5,
                                "min": -5,
                                "vary": True,
                                "value": 1.5,
                            },
                            "fwhmg": {
                                "max": 3,
                                "min": 0.1,
                                "vary": True,
                                "value": 0.8,
                            },
                            "fwhml": {
                                "max": 3,
                                "min": 0.1,
                                "vary": True,
                                "value": 0.8,
                            },
                        }
                    }
                },
                id="pseudovoigt",
            ),
        ],
    )
    def test_center_recovery(
        self,
        model: str,
        true_params: dict[str, float],
        guess_peaks: dict[str, Any],
    ) -> None:
        """Fit a peak and verify center is recovered within tolerance.

        Args:
            model: Distribution model name.
            true_params: True parameter values for generation.
            guess_peaks: Initial guess peaks dict for fitting.
        """
        true_center = true_params["center"]
        model_name: ModelName = model  # type: ignore[assignment]

        _, fitted = _fit_single_peak(
            model=model_name,
            true_params=true_params,
            guess_peaks=guess_peaks,
        )

        center_key = f"{model}_center_1"
        np.testing.assert_allclose(fitted[center_key], true_center, atol=0.05)


@pytest.mark.validation
class TestMultiPeakDeconvolution:
    """Validate recovery of two overlapping Gaussian peaks."""

    true_peaks: ClassVar[list[dict[str, float]]] = [
        {"amplitude": 1.0, "center": -1.5, "fwhmg": 0.8},
        {"amplitude": 0.7, "center": 1.5, "fwhmg": 1.0},
    ]

    def test_two_gaussian_deconvolution(self) -> None:
        """Fit two Gaussians with known parameters and verify recovery."""
        spectrum = SyntheticSpectrum(
            x_min=-10.0,
            x_max=10.0,
            num_points=1000,
            noise_level=0.0,
            peaks=[PeakDefinition(model="gaussian", params=p) for p in self.true_peaks],
            seed=42,
        )
        x, y, _ = spectrum.generate()
        df = pd.DataFrame({"energy": x, "intensity": y})

        args = _make_args(
            peaks={
                "1": {
                    "gaussian": {
                        "amplitude": {
                            "max": 3,
                            "min": 0,
                            "vary": True,
                            "value": 0.8,
                        },
                        "center": {
                            "max": 0,
                            "min": -5,
                            "vary": True,
                            "value": -1.0,
                        },
                        "fwhmg": {
                            "max": 3,
                            "min": 0.1,
                            "vary": True,
                            "value": 0.6,
                        },
                    }
                },
                "2": {
                    "gaussian": {
                        "amplitude": {
                            "max": 3,
                            "min": 0,
                            "vary": True,
                            "value": 0.5,
                        },
                        "center": {
                            "max": 5,
                            "min": 0,
                            "vary": True,
                            "value": 1.0,
                        },
                        "fwhmg": {
                            "max": 3,
                            "min": 0.1,
                            "vary": True,
                            "value": 0.8,
                        },
                    }
                },
            }
        )

        _, result = SolverModels(df=df, args=args)()
        fitted = {name: p.value for name, p in result.params.items()}

        # Peak 1
        np.testing.assert_allclose(
            fitted["gaussian_center_1"],
            self.true_peaks[0]["center"],
            atol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_amplitude_1"],
            self.true_peaks[0]["amplitude"],
            rtol=0.02,
        )

        # Peak 2
        np.testing.assert_allclose(
            fitted["gaussian_center_2"],
            self.true_peaks[1]["center"],
            atol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_amplitude_2"],
            self.true_peaks[1]["amplitude"],
            rtol=0.02,
        )


@pytest.mark.validation
class TestNoiseResilience:
    """Validate parameter recovery under realistic noise conditions."""

    true_amplitude: ClassVar[float] = 1.0
    true_center: ClassVar[float] = 0.0
    true_fwhmg: ClassVar[float] = 1.0

    def test_gaussian_with_noise(self) -> None:
        """Fit a noisy Gaussian and verify parameters within confidence."""
        result, fitted = _fit_single_peak(
            model="gaussian",
            true_params={
                "amplitude": self.true_amplitude,
                "center": self.true_center,
                "fwhmg": self.true_fwhmg,
            },
            guess_peaks={
                "1": {
                    "gaussian": {
                        "amplitude": {
                            "max": 3,
                            "min": 0,
                            "vary": True,
                            "value": 0.8,
                        },
                        "center": {
                            "max": 2,
                            "min": -2,
                            "vary": True,
                            "value": 0.1,
                        },
                        "fwhmg": {
                            "max": 3,
                            "min": 0.1,
                            "vary": True,
                            "value": 0.8,
                        },
                    }
                }
            },
            noise_level=0.01,
        )

        np.testing.assert_allclose(
            fitted["gaussian_amplitude_1"],
            self.true_amplitude,
            rtol=0.02,
        )
        np.testing.assert_allclose(
            fitted["gaussian_center_1"],
            self.true_center,
            atol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_fwhmg_1"],
            self.true_fwhmg,
            rtol=0.05,
        )

        # Verify covariance was computed (fit quality indicator)
        assert result.covar is not None, "Covariance matrix should be computed"
        assert result.success, "Fit should converge successfully"

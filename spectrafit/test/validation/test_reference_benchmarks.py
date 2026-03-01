"""Reference data benchmark tests for SpectraFit scientific validation.

These tests validate multi-peak deconvolution, mixed-model fitting,
convergence robustness, intensity ratio preservation, and baseline
recovery against known synthetic ground truths.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

import numpy as np
import pandas as pd
import pytest

from spectrafit.generators.synthetic import ModelName
from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum
from spectrafit.models.solver import SolverModels


if TYPE_CHECKING:
    from lmfit.minimizer import MinimizerResult


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


def _generate_and_fit(
    peaks_def: list[PeakDefinition],
    guess_peaks: dict[str, Any],
    *,
    x_min: float = -10.0,
    x_max: float = 10.0,
    num_points: int = 1000,
    noise_level: float = 0.01,
    seed: int = 42,
    max_nfev: int = 2000,
) -> tuple[MinimizerResult, dict[str, float]]:
    """Generate a synthetic spectrum and fit it.

    Args:
        peaks_def: List of peak definitions for spectrum generation.
        guess_peaks: Initial guess peaks in SpectraFit format.
        x_min: Lower bound of x-axis.
        x_max: Upper bound of x-axis.
        num_points: Number of data points.
        noise_level: Gaussian noise standard deviation.
        seed: Random seed for reproducibility.
        max_nfev: Maximum number of function evaluations.

    Returns:
        Tuple of (lmfit MinimizerResult, dict of fitted parameter values).
    """
    spectrum = SyntheticSpectrum(
        x_min=x_min,
        x_max=x_max,
        num_points=num_points,
        noise_level=noise_level,
        peaks=peaks_def,
        seed=seed,
    )
    x, y, _ = spectrum.generate()
    df = pd.DataFrame({"energy": x, "intensity": y})
    args = _make_args(guess_peaks, max_nfev=max_nfev)
    _, result = SolverModels(df=df, args=args)()
    fitted: dict[str, float] = {
        name: param.value for name, param in result.params.items()
    }
    return result, fitted


@pytest.mark.validation
class TestTwoPeakOverlap:
    """Validate recovery of two partially overlapping Gaussians."""

    true_peaks: ClassVar[list[dict[str, float]]] = [
        {"amplitude": 1.0, "center": -1.5, "fwhmg": 1.0},
        {"amplitude": 0.8, "center": 1.5, "fwhmg": 1.0},
    ]

    def test_two_peak_overlap_recovery(self) -> None:
        """Fit two overlapping Gaussians and verify all parameters recovered."""
        model: ModelName = "gaussian"
        peaks_def = [PeakDefinition(model=model, params=p) for p in self.true_peaks]
        guess_peaks = {
            "1": {
                "gaussian": {
                    "amplitude": {
                        "max": 2,
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
                        "value": 0.8,
                    },
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {
                        "max": 2,
                        "min": 0,
                        "vary": True,
                        "value": 0.6,
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

        _, fitted = _generate_and_fit(peaks_def, guess_peaks)

        for i, true in enumerate(self.true_peaks, start=1):
            np.testing.assert_allclose(
                fitted[f"gaussian_amplitude_{i}"],
                true["amplitude"],
                rtol=0.05,
            )
            np.testing.assert_allclose(
                fitted[f"gaussian_center_{i}"],
                true["center"],
                rtol=0.05,
            )
            np.testing.assert_allclose(
                fitted[f"gaussian_fwhmg_{i}"],
                true["fwhmg"],
                rtol=0.05,
            )


@pytest.mark.validation
class TestThreePeakDeconvolution:
    """Validate deconvolution of three well-separated Gaussians."""

    true_peaks: ClassVar[list[dict[str, float]]] = [
        {"amplitude": 1.0, "center": -4.0, "fwhmg": 0.8},
        {"amplitude": 1.2, "center": 0.0, "fwhmg": 1.0},
        {"amplitude": 0.6, "center": 4.0, "fwhmg": 0.9},
    ]

    def test_three_peak_resolution(self) -> None:
        """Fit three Gaussians and verify all peaks resolved correctly."""
        model: ModelName = "gaussian"
        peaks_def = [PeakDefinition(model=model, params=p) for p in self.true_peaks]
        guess_peaks = {
            "1": {
                "gaussian": {
                    "amplitude": {
                        "max": 2,
                        "min": 0,
                        "vary": True,
                        "value": 0.8,
                    },
                    "center": {
                        "max": -2,
                        "min": -7,
                        "vary": True,
                        "value": -3.5,
                    },
                    "fwhmg": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": 1.0,
                    },
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {
                        "max": 2,
                        "min": 0,
                        "vary": True,
                        "value": 1.0,
                    },
                    "center": {
                        "max": 2,
                        "min": -2,
                        "vary": True,
                        "value": 0.5,
                    },
                    "fwhmg": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": 1.0,
                    },
                }
            },
            "3": {
                "gaussian": {
                    "amplitude": {
                        "max": 2,
                        "min": 0,
                        "vary": True,
                        "value": 0.5,
                    },
                    "center": {
                        "max": 7,
                        "min": 2,
                        "vary": True,
                        "value": 3.5,
                    },
                    "fwhmg": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": 1.0,
                    },
                }
            },
        }

        _, fitted = _generate_and_fit(peaks_def, guess_peaks)

        for i, true in enumerate(self.true_peaks, start=1):
            np.testing.assert_allclose(
                fitted[f"gaussian_amplitude_{i}"],
                true["amplitude"],
                rtol=0.05,
            )
            np.testing.assert_allclose(
                fitted[f"gaussian_center_{i}"],
                true["center"],
                atol=0.05,
            )
            np.testing.assert_allclose(
                fitted[f"gaussian_fwhmg_{i}"],
                true["fwhmg"],
                rtol=0.05,
            )


@pytest.mark.validation
class TestMixedModelDeconvolution:
    """Validate fitting a Gaussian + Lorentzian mixed spectrum."""

    true_gaussian: ClassVar[dict[str, float]] = {
        "amplitude": 1.0,
        "center": -2.0,
        "fwhmg": 0.8,
    }
    true_lorentzian: ClassVar[dict[str, float]] = {
        "amplitude": 0.8,
        "center": 2.5,
        "fwhml": 1.0,
    }

    def test_mixed_model_recovery(self) -> None:
        """Fit Gaussian + Lorentzian and verify each model's parameters."""
        gauss_model: ModelName = "gaussian"
        lor_model: ModelName = "lorentzian"
        peaks_def = [
            PeakDefinition(model=gauss_model, params=self.true_gaussian),
            PeakDefinition(model=lor_model, params=self.true_lorentzian),
        ]
        guess_peaks = {
            "1": {
                "gaussian": {
                    "amplitude": {
                        "max": 2,
                        "min": 0,
                        "vary": True,
                        "value": 0.8,
                    },
                    "center": {
                        "max": 0,
                        "min": -5,
                        "vary": True,
                        "value": -1.5,
                    },
                    "fwhmg": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": 1.0,
                    },
                }
            },
            "2": {
                "lorentzian": {
                    "amplitude": {
                        "max": 2,
                        "min": 0,
                        "vary": True,
                        "value": 0.6,
                    },
                    "center": {
                        "max": 5,
                        "min": 0,
                        "vary": True,
                        "value": 2.0,
                    },
                    "fwhml": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": 0.8,
                    },
                }
            },
        }

        _, fitted = _generate_and_fit(peaks_def, guess_peaks)

        # Gaussian recovery
        np.testing.assert_allclose(
            fitted["gaussian_amplitude_1"],
            self.true_gaussian["amplitude"],
            rtol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_center_1"],
            self.true_gaussian["center"],
            rtol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_fwhmg_1"],
            self.true_gaussian["fwhmg"],
            rtol=0.05,
        )

        # Lorentzian recovery
        np.testing.assert_allclose(
            fitted["lorentzian_amplitude_2"],
            self.true_lorentzian["amplitude"],
            rtol=0.05,
        )
        np.testing.assert_allclose(
            fitted["lorentzian_center_2"],
            self.true_lorentzian["center"],
            rtol=0.05,
        )
        np.testing.assert_allclose(
            fitted["lorentzian_fwhml_2"],
            self.true_lorentzian["fwhml"],
            rtol=0.05,
        )


@pytest.mark.validation
class TestConvergenceMultipleInitialGuesses:
    """Validate convergence from different initial guesses to same solution."""

    true_peaks: ClassVar[list[dict[str, float]]] = [
        {"amplitude": 1.0, "center": -2.0, "fwhmg": 1.0},
        {"amplitude": 0.7, "center": 2.0, "fwhmg": 1.2},
    ]

    initial_guesses: ClassVar[list[dict[str, Any]]] = [
        {
            "1": {
                "gaussian": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.5},
                    "center": {"max": 0, "min": -5, "vary": True, "value": -1.0},
                    "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 0.5},
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.4},
                    "center": {"max": 5, "min": 0, "vary": True, "value": 1.0},
                    "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 0.8},
                }
            },
        },
        {
            "1": {
                "gaussian": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1.2},
                    "center": {"max": 0, "min": -5, "vary": True, "value": -2.5},
                    "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 1.5},
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.9},
                    "center": {"max": 5, "min": 0, "vary": True, "value": 2.5},
                    "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 1.5},
                }
            },
        },
        {
            "1": {
                "gaussian": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.8},
                    "center": {"max": 0, "min": -5, "vary": True, "value": -1.5},
                    "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 1.2},
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 0.6},
                    "center": {"max": 5, "min": 0, "vary": True, "value": 1.5},
                    "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 1.0},
                }
            },
        },
    ]

    def test_convergence_consistency(self) -> None:
        """All initial guesses must converge to the same solution."""
        model: ModelName = "gaussian"
        peaks_def = [PeakDefinition(model=model, params=p) for p in self.true_peaks]

        # Generate spectrum once
        spectrum = SyntheticSpectrum(
            x_min=-10.0,
            x_max=10.0,
            num_points=1000,
            noise_level=0.01,
            peaks=peaks_def,
            seed=42,
        )
        x, y, _ = spectrum.generate()
        df = pd.DataFrame({"energy": x, "intensity": y})

        results: list[dict[str, float]] = []
        for guess in self.initial_guesses:
            args = _make_args(guess)
            _, result = SolverModels(df=df, args=args)()
            fitted = {name: p.value for name, p in result.params.items()}
            results.append(fitted)

        # All runs should agree with the first within 2% relative tolerance
        params_to_check = [
            "gaussian_amplitude_1",
            "gaussian_center_1",
            "gaussian_fwhmg_1",
            "gaussian_amplitude_2",
            "gaussian_center_2",
            "gaussian_fwhmg_2",
        ]
        reference = results[0]
        for i, fitted in enumerate(results[1:], start=2):
            for param in params_to_check:
                np.testing.assert_allclose(
                    fitted[param],
                    reference[param],
                    rtol=0.02,
                    err_msg=f"Run {i} param '{param}' diverged from run 1",
                )


@pytest.mark.validation
class TestPeakIntensityRatioPreservation:
    """Validate that fitted amplitude ratio matches the known 2:1 ratio."""

    true_peaks: ClassVar[list[dict[str, float]]] = [
        {"amplitude": 2.0, "center": -2.0, "fwhmg": 1.0},
        {"amplitude": 1.0, "center": 3.0, "fwhmg": 1.0},
    ]
    expected_ratio: ClassVar[float] = 2.0

    def test_amplitude_ratio(self) -> None:
        """Fit two Gaussians and verify amplitude ratio is preserved."""
        model: ModelName = "gaussian"
        peaks_def = [PeakDefinition(model=model, params=p) for p in self.true_peaks]
        guess_peaks = {
            "1": {
                "gaussian": {
                    "amplitude": {
                        "max": 4,
                        "min": 0,
                        "vary": True,
                        "value": 1.5,
                    },
                    "center": {
                        "max": 0,
                        "min": -5,
                        "vary": True,
                        "value": -1.5,
                    },
                    "fwhmg": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": 0.8,
                    },
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {
                        "max": 4,
                        "min": 0,
                        "vary": True,
                        "value": 0.8,
                    },
                    "center": {
                        "max": 6,
                        "min": 0,
                        "vary": True,
                        "value": 2.5,
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

        _, fitted = _generate_and_fit(peaks_def, guess_peaks)

        recovered_ratio = (
            fitted["gaussian_amplitude_1"] / fitted["gaussian_amplitude_2"]
        )
        np.testing.assert_allclose(recovered_ratio, self.expected_ratio, rtol=0.05)


@pytest.mark.validation
class TestBaselinePlusGaussian:
    """Validate recovery of a linear background plus a Gaussian peak."""

    true_slope: ClassVar[float] = 0.1
    true_intercept: ClassVar[float] = 0.5
    true_gaussian: ClassVar[dict[str, float]] = {
        "amplitude": 1.5,
        "center": 0.0,
        "fwhmg": 1.0,
    }

    def test_baseline_and_peak_recovery(self) -> None:
        """Fit linear background + Gaussian and verify both recovered."""
        gauss_model: ModelName = "gaussian"
        linear_model: ModelName = "linear"
        peaks_def = [
            PeakDefinition(
                model=linear_model,
                params={
                    "slope": self.true_slope,
                    "intercept": self.true_intercept,
                },
            ),
            PeakDefinition(model=gauss_model, params=self.true_gaussian),
        ]
        guess_peaks = {
            "1": {
                "linear": {
                    "slope": {
                        "max": 1,
                        "min": -1,
                        "vary": True,
                        "value": 0.05,
                    },
                    "intercept": {
                        "max": 2,
                        "min": -1,
                        "vary": True,
                        "value": 0.3,
                    },
                }
            },
            "2": {
                "gaussian": {
                    "amplitude": {
                        "max": 3,
                        "min": 0,
                        "vary": True,
                        "value": 1.0,
                    },
                    "center": {
                        "max": 3,
                        "min": -3,
                        "vary": True,
                        "value": 0.5,
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

        _, fitted = _generate_and_fit(peaks_def, guess_peaks)

        # Linear background recovery
        np.testing.assert_allclose(fitted["linear_slope_1"], self.true_slope, rtol=0.05)
        np.testing.assert_allclose(
            fitted["linear_intercept_1"], self.true_intercept, rtol=0.05
        )

        # Gaussian peak recovery
        np.testing.assert_allclose(
            fitted["gaussian_amplitude_2"],
            self.true_gaussian["amplitude"],
            rtol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_center_2"],
            self.true_gaussian["center"],
            atol=0.05,
        )
        np.testing.assert_allclose(
            fitted["gaussian_fwhmg_2"],
            self.true_gaussian["fwhmg"],
            rtol=0.05,
        )

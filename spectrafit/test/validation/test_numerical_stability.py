"""Numerical stability tests for SpectraFit's scientific validation framework.

These tests verify that the fitting pipeline is robust against noise, initial
guess variation, edge-case peak shapes, parameter perturbation, and that
residuals exhibit expected symmetry properties.
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
    from numpy.typing import NDArray


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


# ---------------------------------------------------------------------------
# 1. Noise injection
# ---------------------------------------------------------------------------


@pytest.mark.validation
class TestNoiseInjection:
    """Verify parameter recovery degrades gracefully with increasing noise."""

    true_amplitude: ClassVar[float] = 1.0
    true_center: ClassVar[float] = 0.0
    true_fwhmg: ClassVar[float] = 1.0

    _guess_peaks: ClassVar[dict[str, Any]] = {
        "1": {
            "gaussian": {
                "amplitude": {"max": 3, "min": 0, "vary": True, "value": 0.8},
                "center": {"max": 2, "min": -2, "vary": True, "value": 0.1},
                "fwhmg": {"max": 3, "min": 0.1, "vary": True, "value": 0.8},
            }
        }
    }

    @pytest.mark.parametrize(
        "noise_level",
        [0.001, 0.01, 0.05, 0.1],
        ids=["noise_0.001", "noise_0.01", "noise_0.05", "noise_0.1"],
    )
    def test_gaussian_noise_recovery(self, noise_level: float) -> None:
        """Fit a Gaussian under noise and check parameter recovery.

        Tolerance scales linearly with the noise level so that stricter
        checks apply to cleaner data.

        Args:
            noise_level: Standard deviation of additive Gaussian noise.
        """
        rtol = max(0.02, 5.0 * noise_level)

        _, fitted = _fit_single_peak(
            model="gaussian",
            true_params={
                "amplitude": self.true_amplitude,
                "center": self.true_center,
                "fwhmg": self.true_fwhmg,
            },
            guess_peaks=self._guess_peaks,
            noise_level=noise_level,
        )

        np.testing.assert_allclose(
            fitted["gaussian_amplitude_1"],
            self.true_amplitude,
            rtol=rtol,
            err_msg=f"Amplitude recovery failed at noise={noise_level}",
        )
        np.testing.assert_allclose(
            fitted["gaussian_center_1"],
            self.true_center,
            atol=rtol,
            err_msg=f"Center recovery failed at noise={noise_level}",
        )
        np.testing.assert_allclose(
            fitted["gaussian_fwhmg_1"],
            self.true_fwhmg,
            rtol=rtol,
            err_msg=f"FWHM recovery failed at noise={noise_level}",
        )


# ---------------------------------------------------------------------------
# 2. Initial guess robustness
# ---------------------------------------------------------------------------


@pytest.mark.validation
class TestInitialGuessRobustness:
    """Verify that different initial amplitude guesses converge to the same result."""

    true_amplitude: ClassVar[float] = 1.0
    true_center: ClassVar[float] = 0.0
    true_fwhmg: ClassVar[float] = 1.0

    initial_amplitudes: ClassVar[list[float]] = [0.5, 0.8, 1.2, 1.5, 2.0]

    def test_all_guesses_converge(self) -> None:
        """Fit from five different amplitude guesses and compare results."""
        results: list[dict[str, float]] = []

        for amp_guess in self.initial_amplitudes:
            guess_peaks: dict[str, Any] = {
                "1": {
                    "gaussian": {
                        "amplitude": {
                            "max": 3,
                            "min": 0,
                            "vary": True,
                            "value": amp_guess,
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
            }
            _, fitted = _fit_single_peak(
                model="gaussian",
                true_params={
                    "amplitude": self.true_amplitude,
                    "center": self.true_center,
                    "fwhmg": self.true_fwhmg,
                },
                guess_peaks=guess_peaks,
            )
            results.append(fitted)

        # All runs must agree within 2 % relative tolerance
        ref = results[0]
        for idx, fitted in enumerate(results[1:], start=1):
            np.testing.assert_allclose(
                fitted["gaussian_amplitude_1"],
                ref["gaussian_amplitude_1"],
                rtol=0.02,
                err_msg=f"Amplitude diverged for guess index {idx}",
            )
            np.testing.assert_allclose(
                fitted["gaussian_center_1"],
                ref["gaussian_center_1"],
                atol=0.02,
                err_msg=f"Center diverged for guess index {idx}",
            )
            np.testing.assert_allclose(
                fitted["gaussian_fwhmg_1"],
                ref["gaussian_fwhmg_1"],
                rtol=0.02,
                err_msg=f"FWHM diverged for guess index {idx}",
            )


# ---------------------------------------------------------------------------
# 3. Edge cases — no NaN or Inf
# ---------------------------------------------------------------------------


@pytest.mark.validation
class TestEdgeCasesNoNaN:
    """Ensure fits produce finite values for extreme peak configurations."""

    @pytest.mark.parametrize(
        ("label", "true_params", "guess_peaks"),
        [
            pytest.param(
                "narrow_peak",
                {"amplitude": 1.0, "center": 0.0, "fwhmg": 0.1},
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
                                "max": 2,
                                "min": -2,
                                "vary": True,
                                "value": 0.0,
                            },
                            "fwhmg": {
                                "max": 1,
                                "min": 0.01,
                                "vary": True,
                                "value": 0.15,
                            },
                        }
                    }
                },
                id="narrow_peak",
            ),
            pytest.param(
                "broad_peak",
                {"amplitude": 1.0, "center": 0.0, "fwhmg": 5.0},
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
                                "max": 2,
                                "min": -2,
                                "vary": True,
                                "value": 0.0,
                            },
                            "fwhmg": {
                                "max": 10,
                                "min": 0.1,
                                "vary": True,
                                "value": 4.0,
                            },
                        }
                    }
                },
                id="broad_peak",
            ),
            pytest.param(
                "edge_center",
                {"amplitude": 1.0, "center": -9.5, "fwhmg": 1.0},
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
                                "max": 0,
                                "min": -10,
                                "vary": True,
                                "value": -9.0,
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
                id="edge_center",
            ),
            pytest.param(
                "small_amplitude",
                {"amplitude": 0.01, "center": 0.0, "fwhmg": 1.0},
                {
                    "1": {
                        "gaussian": {
                            "amplitude": {
                                "max": 0.1,
                                "min": 0,
                                "vary": True,
                                "value": 0.02,
                            },
                            "center": {
                                "max": 2,
                                "min": -2,
                                "vary": True,
                                "value": 0.0,
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
                id="small_amplitude",
            ),
        ],
    )
    def test_no_nan_inf(
        self,
        label: str,
        true_params: dict[str, float],
        guess_peaks: dict[str, Any],
    ) -> None:
        """Fit an edge-case Gaussian and assert all results are finite.

        Args:
            label: Human-readable case description.
            true_params: True parameter values for generation.
            guess_peaks: Initial guess peaks dict for fitting.
        """
        _, fitted = _fit_single_peak(
            model="gaussian",
            true_params=true_params,
            guess_peaks=guess_peaks,
        )

        for param_name, value in fitted.items():
            assert np.isfinite(value), (
                f"Parameter {param_name} is not finite ({value}) for case '{label}'"
            )


# ---------------------------------------------------------------------------
# 4. Convergence under perturbation
# ---------------------------------------------------------------------------


@pytest.mark.validation
class TestConvergenceUnderPerturbation:
    """Verify that ±10 % perturbation of initial guesses still converges."""

    true_amplitude: ClassVar[float] = 1.0
    true_center: ClassVar[float] = 0.0
    true_fwhmg: ClassVar[float] = 1.0

    def _make_perturbed_guess(self, factor: float) -> dict[str, Any]:
        """Return guess peaks with values scaled by *factor*.

        Args:
            factor: Multiplicative perturbation factor (e.g. 0.9 or 1.1).

        Returns:
            Guess peaks dictionary with perturbed values.
        """
        return {
            "1": {
                "gaussian": {
                    "amplitude": {
                        "max": 3,
                        "min": 0,
                        "vary": True,
                        "value": self.true_amplitude * factor,
                    },
                    "center": {
                        "max": 2,
                        "min": -2,
                        "vary": True,
                        "value": self.true_center + 0.1 * (factor - 1.0),
                    },
                    "fwhmg": {
                        "max": 3,
                        "min": 0.1,
                        "vary": True,
                        "value": self.true_fwhmg * factor,
                    },
                }
            }
        }

    @pytest.mark.parametrize(
        "factor",
        [0.9, 1.1],
        ids=["minus_10pct", "plus_10pct"],
    )
    def test_perturbed_convergence(self, factor: float) -> None:
        """Fit with a perturbed initial guess and verify convergence.

        Args:
            factor: Perturbation multiplier applied to true values.
        """
        _, fitted = _fit_single_peak(
            model="gaussian",
            true_params={
                "amplitude": self.true_amplitude,
                "center": self.true_center,
                "fwhmg": self.true_fwhmg,
            },
            guess_peaks=self._make_perturbed_guess(factor),
        )

        np.testing.assert_allclose(
            fitted["gaussian_amplitude_1"], self.true_amplitude, rtol=0.02
        )
        np.testing.assert_allclose(
            fitted["gaussian_center_1"], self.true_center, atol=0.02
        )
        np.testing.assert_allclose(
            fitted["gaussian_fwhmg_1"], self.true_fwhmg, rtol=0.02
        )


# ---------------------------------------------------------------------------
# 5. Residual symmetry
# ---------------------------------------------------------------------------


@pytest.mark.validation
class TestResidualSymmetry:
    """For symmetric models the fit residuals must be symmetric about center."""

    @pytest.mark.parametrize(
        ("model", "true_params", "guess_peaks"),
        [
            pytest.param(
                "gaussian",
                {"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
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
                id="gaussian",
            ),
            pytest.param(
                "lorentzian",
                {"amplitude": 1.0, "center": 0.0, "fwhml": 1.0},
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
                                "max": 2,
                                "min": -2,
                                "vary": True,
                                "value": 0.1,
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
        ],
    )
    def test_residual_mirror_symmetry(
        self,
        model: str,
        true_params: dict[str, float],
        guess_peaks: dict[str, Any],
    ) -> None:
        """Verify that residuals are mirror-symmetric around center.

        For a noiseless symmetric peak centred at zero the left and right
        halves of the residual vector should be highly correlated when one
        half is reversed.

        Args:
            model: Distribution model name.
            true_params: True parameter values for generation.
            guess_peaks: Initial guess peaks dict for fitting.
        """
        model_name: ModelName = model  # type: ignore[assignment]

        spectrum = SyntheticSpectrum(
            x_min=-10.0,
            x_max=10.0,
            num_points=1000,
            noise_level=0.0,
            peaks=[PeakDefinition(model=model_name, params=true_params)],
            seed=42,
        )
        x, y, _ = spectrum.generate()
        df = pd.DataFrame({"energy": x, "intensity": y})

        args = _make_args(guess_peaks)
        _, result = SolverModels(df=df, args=args)()

        residual: NDArray[np.floating[Any]] = result.residual
        n = len(residual)
        left = residual[: n // 2]
        right = residual[n // 2 :][::-1]

        # Trim to equal length in case n is odd
        min_len = min(len(left), len(right))
        left = left[:min_len]
        right = right[:min_len]

        # For a near-perfect fit the residuals are tiny; correlation may be
        # undefined if variance ≈ 0.  Fall back to checking that the
        # element-wise difference is negligible.
        max_residual = np.max(np.abs(residual))
        if max_residual < 1e-10:
            np.testing.assert_allclose(
                left,
                right,
                atol=1e-10,
                err_msg=f"Residual halves differ for {model} (near-zero residual)",
            )
        else:
            corr = np.corrcoef(left, right)[0, 1]
            assert corr > 0.99, (
                f"Residual symmetry correlation too low for {model}: {corr:.6f}"
            )

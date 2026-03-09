"""Convergence diagnostics and result validation for fitting results.

This module provides Pydantic models and utility functions to evaluate
the quality and convergence of curve-fitting results produced by lmfit.
"""

from __future__ import annotations

import warnings

from typing import TYPE_CHECKING
from typing import ClassVar

import numpy as np

from pydantic import BaseModel


if TYPE_CHECKING:
    from lmfit.minimizer import MinimizerResult
    from numpy.typing import NDArray


class FitDiagnostics(BaseModel):
    """Convergence and quality diagnostics for a fitting result.

    Attributes:
        converged: Whether the optimizer reported successful convergence.
        num_function_evals: Number of function evaluations performed.
        num_data_points: Number of data points in the fit.
        num_variables: Number of free parameters.
        degrees_of_freedom: Degrees of freedom (data points - variables).
        chi_squared: Chi-squared statistic.
        reduced_chi_squared: Reduced chi-squared (chi² / dof).
        r_squared: Coefficient of determination (R²).
        residual_rms: Root mean square of the residuals.
        residual_max: Maximum absolute residual.
        parameter_at_bound: Names of parameters hitting their min/max bounds.
        nan_in_result: Whether NaN or Inf values were found in the residuals.
        message: Optimizer exit message.
        REDUCED_CHI_SQUARED_THRESHOLD: Threshold for poor fit warning.

    """

    REDUCED_CHI_SQUARED_THRESHOLD: ClassVar[float] = 10.0

    converged: bool
    num_function_evals: int
    num_data_points: int
    num_variables: int
    degrees_of_freedom: int
    chi_squared: float
    reduced_chi_squared: float
    r_squared: float
    residual_rms: float
    residual_max: float
    parameter_at_bound: list[str]
    nan_in_result: bool
    message: str


def _check_parameters_at_bound(
    result: MinimizerResult,
    tolerance: float = 0.01,
) -> list[str]:
    """Check if any fitted parameters are within tolerance of their bounds.

    Args:
        result: The lmfit MinimizerResult containing optimized parameters.
        tolerance: Fractional tolerance for bound proximity (default 1%).

    Returns:
        list[str]: Names of parameters that are near their min or max bound.

    """
    at_bound: list[str] = []
    for name, param in result.params.items():
        if not param.vary:
            continue
        value = param.value
        if param.min is not None and param.min != -np.inf:
            bound_range = (
                abs(param.max - param.min)
                if (param.max is not None and param.max != np.inf)
                else abs(param.min)
            )
            if bound_range > 0 and abs(value - param.min) < tolerance * bound_range:
                at_bound.append(name)
                continue
        if param.max is not None and param.max != np.inf:
            bound_range = (
                abs(param.max - param.min)
                if (param.min is not None and param.min != -np.inf)
                else abs(param.max)
            )
            if bound_range > 0 and abs(value - param.max) < tolerance * bound_range:
                at_bound.append(name)
    return at_bound


def compute_diagnostics(
    result: MinimizerResult,
    data: NDArray[np.float64],
    bound_tolerance: float = 0.01,
) -> FitDiagnostics:
    """Compute convergence diagnostics from an lmfit MinimizerResult.

    Args:
        result: The lmfit MinimizerResult after minimization.
        data: Original observed data array (1-D).
        bound_tolerance: Fractional tolerance for parameter-at-bound check.

    Returns:
        FitDiagnostics: Populated diagnostics instance.

    """
    residual = np.asarray(result.residual, dtype=np.float64)
    nan_in_result = bool(np.any(~np.isfinite(residual)))

    safe_residual = np.where(np.isfinite(residual), residual, 0.0)
    residual_rms = float(np.sqrt(np.mean(safe_residual**2)))
    residual_max = float(np.max(np.abs(safe_residual)))

    ss_res = float(np.sum(safe_residual**2))
    data_arr = np.asarray(data, dtype=np.float64)
    ss_tot = float(np.sum((data_arr - np.mean(data_arr)) ** 2))
    r_squared = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    at_bound = _check_parameters_at_bound(result, tolerance=bound_tolerance)

    return FitDiagnostics(
        converged=bool(result.success),
        num_function_evals=int(result.nfev),
        num_data_points=int(result.ndata),
        num_variables=int(result.nvarys),
        degrees_of_freedom=int(result.nfree),
        chi_squared=float(result.chisqr),
        reduced_chi_squared=float(result.redchi),
        r_squared=r_squared,
        residual_rms=residual_rms,
        residual_max=residual_max,
        parameter_at_bound=at_bound,
        nan_in_result=nan_in_result,
        message=str(result.message),
    )


def validate_result(diagnostics: FitDiagnostics) -> list[str]:
    """Validate fitting diagnostics and return warning strings.

    Args:
        diagnostics: A FitDiagnostics instance to validate.

    Returns:
        list[str]: List of human-readable warning strings. Empty if no issues.

    """
    warns: list[str] = []

    if diagnostics.reduced_chi_squared > FitDiagnostics.REDUCED_CHI_SQUARED_THRESHOLD:
        warns.append(
            f"Poor fit: reduced chi-squared = {diagnostics.reduced_chi_squared:.4f} "
            f"(> 10)",
        )

    if diagnostics.parameter_at_bound:
        names = ", ".join(diagnostics.parameter_at_bound)
        warns.append(f"Parameters at bound: {names}")

    if diagnostics.nan_in_result:
        warns.append("NaN or Inf detected in residuals")

    for msg in warns:
        warnings.warn(msg, UserWarning, stacklevel=2)

    return warns

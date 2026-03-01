"""Tests for convergence diagnostics and result validation."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import numpy as np
import pytest

from spectrafit.models.diagnostics import FitDiagnostics
from spectrafit.models.diagnostics import compute_diagnostics
from spectrafit.models.diagnostics import validate_result


pytestmark = pytest.mark.unit


def _make_mock_result(
    *,
    success: bool = True,
    nfev: int = 42,
    ndata: int = 100,
    nvarys: int = 3,
    nfree: int = 97,
    chisqr: float = 10.0,
    redchi: float = 0.103,
    residual: Any = None,
    params: dict[str, Any] | None = None,
    message: str = "Fit converged",
) -> MagicMock:
    """Build a mock lmfit MinimizerResult for testing.

    Args:
        success: Whether the optimizer reported convergence.
        nfev: Number of function evaluations.
        ndata: Number of data points.
        nvarys: Number of variables.
        nfree: Degrees of freedom.
        chisqr: Chi-squared value.
        redchi: Reduced chi-squared value.
        residual: Residual array. Defaults to small random noise.
        params: Dictionary of mock parameters.
        message: Optimizer exit message.

    Returns:
        MagicMock: A mock MinimizerResult object.

    """
    mock = MagicMock()
    mock.success = success
    mock.nfev = nfev
    mock.ndata = ndata
    mock.nvarys = nvarys
    mock.nfree = nfree
    mock.chisqr = chisqr
    mock.redchi = redchi
    mock.message = message

    if residual is None:
        rng = np.random.default_rng(42)
        residual = rng.normal(0, 0.1, ndata)
    mock.residual = residual

    if params is None:
        params = {}
    mock.params = params
    return mock


def _make_mock_param(
    value: float,
    vary: bool = True,
    min_val: float = -np.inf,
    max_val: float = np.inf,
) -> MagicMock:
    """Build a mock lmfit Parameter.

    Args:
        value: Current parameter value.
        vary: Whether this parameter is free.
        min_val: Lower bound.
        max_val: Upper bound.

    Returns:
        MagicMock: A mock Parameter object.

    """
    p = MagicMock()
    p.value = value
    p.vary = vary
    p.min = min_val
    p.max = max_val
    return p


class TestFitDiagnostics:
    """Tests for FitDiagnostics Pydantic model."""

    def test_creation_and_fields(self) -> None:
        """Test that FitDiagnostics can be created with all fields."""
        diag = FitDiagnostics(
            converged=True,
            num_function_evals=50,
            num_data_points=200,
            num_variables=4,
            degrees_of_freedom=196,
            chi_squared=12.5,
            reduced_chi_squared=0.0638,
            r_squared=0.998,
            residual_rms=0.01,
            residual_max=0.03,
            parameter_at_bound=[],
            nan_in_result=False,
            message="Fit converged",
        )
        assert diag.converged is True
        assert diag.num_function_evals == 50
        assert diag.degrees_of_freedom == 196
        assert diag.parameter_at_bound == []

    def test_serialization_round_trip(self) -> None:
        """Test JSON serialization and deserialization."""
        diag = FitDiagnostics(
            converged=False,
            num_function_evals=10,
            num_data_points=50,
            num_variables=2,
            degrees_of_freedom=48,
            chi_squared=500.0,
            reduced_chi_squared=10.42,
            r_squared=0.5,
            residual_rms=3.0,
            residual_max=8.0,
            parameter_at_bound=["amplitude_gaussian_1"],
            nan_in_result=True,
            message="Maximum iterations reached",
        )
        data = diag.model_dump()
        restored = FitDiagnostics(**data)
        assert restored == diag

    def test_json_export(self) -> None:
        """Test model_dump_json produces valid JSON string."""
        diag = FitDiagnostics(
            converged=True,
            num_function_evals=1,
            num_data_points=10,
            num_variables=1,
            degrees_of_freedom=9,
            chi_squared=1.0,
            reduced_chi_squared=0.111,
            r_squared=0.99,
            residual_rms=0.05,
            residual_max=0.1,
            parameter_at_bound=[],
            nan_in_result=False,
            message="OK",
        )
        json_str = diag.model_dump_json()
        assert isinstance(json_str, str)
        assert '"converged":true' in json_str


class TestComputeDiagnostics:
    """Tests for compute_diagnostics function."""

    def test_good_fit(self) -> None:
        """Test diagnostics for a well-behaved fit result."""
        rng = np.random.default_rng(0)
        data = rng.normal(5.0, 1.0, 100)
        residual = rng.normal(0, 0.01, 100)

        result = _make_mock_result(
            residual=residual,
            ndata=100,
            nvarys=3,
            nfree=97,
            chisqr=float(np.sum(residual**2)),
            redchi=float(np.sum(residual**2) / 97),
        )
        diag = compute_diagnostics(result, data)

        assert diag.converged is True
        assert diag.num_data_points == 100
        assert diag.num_variables == 3
        assert diag.degrees_of_freedom == 97
        assert diag.r_squared > 0.99
        assert diag.residual_rms < 0.02
        assert diag.nan_in_result is False
        assert diag.parameter_at_bound == []

    def test_r_squared_range(self) -> None:
        """Test R² is between 0 and 1 for a reasonable fit."""
        rng = np.random.default_rng(1)
        data = rng.normal(10.0, 2.0, 200)
        residual = rng.normal(0, 0.1, 200)
        result = _make_mock_result(
            residual=residual,
            ndata=200,
            nvarys=2,
            nfree=198,
            chisqr=float(np.sum(residual**2)),
            redchi=float(np.sum(residual**2) / 198),
        )
        diag = compute_diagnostics(result, data)
        assert 0.0 <= diag.r_squared <= 1.0


class TestParameterAtBound:
    """Tests for parameter-at-bound detection."""

    def test_param_at_min_bound(self) -> None:
        """Test detection of a parameter sitting at its minimum bound."""
        params = {
            "amplitude_gaussian_1": _make_mock_param(
                value=0.01, min_val=0.0, max_val=2.0
            ),
            "center_gaussian_1": _make_mock_param(value=1.0, min_val=-5.0, max_val=5.0),
        }
        result = _make_mock_result(params=params, ndata=100)
        diag = compute_diagnostics(result, np.ones(100))
        assert "amplitude_gaussian_1" in diag.parameter_at_bound

    def test_param_at_max_bound(self) -> None:
        """Test detection of a parameter sitting at its maximum bound."""
        params = {
            "fwhm_gaussian_1": _make_mock_param(value=1.99, min_val=0.0, max_val=2.0),
        }
        result = _make_mock_result(params=params, ndata=50)
        diag = compute_diagnostics(result, np.ones(50))
        assert "fwhm_gaussian_1" in diag.parameter_at_bound

    def test_no_bound_hit(self) -> None:
        """Test no false positives when parameters are well within bounds."""
        params = {
            "center_gaussian_1": _make_mock_param(value=0.0, min_val=-5.0, max_val=5.0),
        }
        result = _make_mock_result(params=params, ndata=50)
        diag = compute_diagnostics(result, np.ones(50))
        assert diag.parameter_at_bound == []

    def test_fixed_params_ignored(self) -> None:
        """Test that non-varying parameters are not checked for bounds."""
        params = {
            "center_gaussian_1": _make_mock_param(
                value=0.0, vary=False, min_val=0.0, max_val=1.0
            ),
        }
        result = _make_mock_result(params=params, ndata=50)
        diag = compute_diagnostics(result, np.ones(50))
        assert diag.parameter_at_bound == []


class TestNaNDetection:
    """Tests for NaN and Inf detection in residuals."""

    def test_nan_in_residual(self) -> None:
        """Test that NaN in residuals is detected."""
        residual = np.array([0.1, np.nan, 0.2, 0.3])
        result = _make_mock_result(
            residual=residual,
            ndata=4,
            nvarys=1,
            nfree=3,
            chisqr=0.14,
            redchi=0.047,
        )
        diag = compute_diagnostics(result, np.ones(4))
        assert diag.nan_in_result is True

    def test_inf_in_residual(self) -> None:
        """Test that Inf in residuals is detected."""
        residual = np.array([0.1, np.inf, 0.2])
        result = _make_mock_result(
            residual=residual,
            ndata=3,
            nvarys=1,
            nfree=2,
            chisqr=0.05,
            redchi=0.025,
        )
        diag = compute_diagnostics(result, np.ones(3))
        assert diag.nan_in_result is True

    def test_clean_residual(self) -> None:
        """Test that clean residuals pass NaN check."""
        residual = np.array([0.01, -0.02, 0.005])
        result = _make_mock_result(
            residual=residual,
            ndata=3,
            nvarys=1,
            nfree=2,
            chisqr=0.000525,
            redchi=0.0002625,
        )
        diag = compute_diagnostics(result, np.ones(3))
        assert diag.nan_in_result is False


class TestValidateResult:
    """Tests for validate_result warning generation."""

    def test_good_fit_no_warnings(self) -> None:
        """Test that a good fit produces no warnings."""
        diag = FitDiagnostics(
            converged=True,
            num_function_evals=50,
            num_data_points=200,
            num_variables=4,
            degrees_of_freedom=196,
            chi_squared=1.0,
            reduced_chi_squared=0.005,
            r_squared=0.999,
            residual_rms=0.01,
            residual_max=0.03,
            parameter_at_bound=[],
            nan_in_result=False,
            message="Fit converged",
        )
        warns = validate_result(diag)
        assert warns == []

    def test_high_reduced_chi_squared_warning(self) -> None:
        """Test warning when reduced chi-squared exceeds threshold."""
        diag = FitDiagnostics(
            converged=True,
            num_function_evals=100,
            num_data_points=50,
            num_variables=2,
            degrees_of_freedom=48,
            chi_squared=600.0,
            reduced_chi_squared=12.5,
            r_squared=0.5,
            residual_rms=3.0,
            residual_max=8.0,
            parameter_at_bound=[],
            nan_in_result=False,
            message="Fit converged",
        )
        with pytest.warns(UserWarning, match="Poor fit"):
            warns = validate_result(diag)
        assert any("reduced chi-squared" in w for w in warns)

    def test_parameter_at_bound_warning(self) -> None:
        """Test warning when parameters are at their bounds."""
        diag = FitDiagnostics(
            converged=True,
            num_function_evals=30,
            num_data_points=100,
            num_variables=3,
            degrees_of_freedom=97,
            chi_squared=5.0,
            reduced_chi_squared=0.051,
            r_squared=0.99,
            residual_rms=0.05,
            residual_max=0.1,
            parameter_at_bound=["amplitude_gaussian_1", "fwhm_gaussian_1"],
            nan_in_result=False,
            message="Fit converged",
        )
        with pytest.warns(UserWarning, match="Parameters at bound"):
            warns = validate_result(diag)
        assert any("amplitude_gaussian_1" in w for w in warns)

    def test_nan_warning(self) -> None:
        """Test warning when NaN detected in residuals."""
        diag = FitDiagnostics(
            converged=False,
            num_function_evals=5,
            num_data_points=10,
            num_variables=1,
            degrees_of_freedom=9,
            chi_squared=0.0,
            reduced_chi_squared=0.0,
            r_squared=0.0,
            residual_rms=0.0,
            residual_max=0.0,
            parameter_at_bound=[],
            nan_in_result=True,
            message="Failed",
        )
        with pytest.warns(UserWarning, match="NaN or Inf"):
            warns = validate_result(diag)
        assert any("NaN" in w for w in warns)

    def test_multiple_warnings(self) -> None:
        """Test that multiple issues produce multiple warnings."""
        diag = FitDiagnostics(
            converged=False,
            num_function_evals=500,
            num_data_points=20,
            num_variables=5,
            degrees_of_freedom=15,
            chi_squared=200.0,
            reduced_chi_squared=13.33,
            r_squared=0.1,
            residual_rms=5.0,
            residual_max=12.0,
            parameter_at_bound=["center_voigt_1"],
            nan_in_result=True,
            message="Max iterations",
        )
        with pytest.warns(UserWarning, match="Poor fit|Parameters at bound|NaN"):
            warns = validate_result(diag)
        assert len(warns) == 3

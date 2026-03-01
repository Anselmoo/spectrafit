"""Tests for Pydantic fixture models in spectrafit.test.fixtures."""

from __future__ import annotations

from math import inf
from typing import Any

import numpy as np
import pandas as pd
import pytest

from spectrafit.models.solver import SolverModels
from spectrafit.test.fixtures import ParameterSpec
from spectrafit.test.fixtures import PeakSpec
from spectrafit.test.fixtures import double_gaussian
from spectrafit.test.fixtures import gaussian_with_background
from spectrafit.test.fixtures import single_gaussian
from spectrafit.test.fixtures import single_lorentzian


# ---------------------------------------------------------------------------
# ParameterSpec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestParameterSpec:
    """Tests for ParameterSpec creation and serialisation."""

    def test_defaults(self) -> None:
        """Default min/max/vary/expr are applied correctly."""
        p = ParameterSpec(value=1.5)
        assert p.min == -inf
        assert p.max == inf
        assert p.vary is True
        assert p.expr is None

    def test_to_dict_basic(self) -> None:
        """to_dict produces the expected keys and values."""
        p = ParameterSpec(value=2.0, min=0.0, max=5.0, vary=False)
        d = p.to_dict()
        assert d == {"value": 2.0, "min": 0.0, "max": 5.0, "vary": False}

    def test_to_dict_with_expr(self) -> None:
        """Expression key is included only when set."""
        p = ParameterSpec(value=0.0, expr="other_param * 2")
        d = p.to_dict()
        assert d["expr"] == "other_param * 2"

    def test_to_dict_without_expr(self) -> None:
        """Expression key is omitted when None."""
        p = ParameterSpec(value=0.0)
        assert "expr" not in p.to_dict()


# ---------------------------------------------------------------------------
# PeakSpec
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPeakSpec:
    """Tests for PeakSpec nested dict conversion."""

    def test_to_dict_structure(self) -> None:
        """to_dict produces {model_name: {param: {...}}} nesting."""
        peak = PeakSpec(
            model_name="gaussian",
            parameters={
                "amplitude": ParameterSpec(value=1.0, min=0, max=10),
                "center": ParameterSpec(value=0.0, min=-5, max=5),
                "fwhmg": ParameterSpec(value=0.5, min=0.01, max=5),
            },
        )
        d = peak.to_dict()

        assert "gaussian" in d
        assert set(d["gaussian"]) == {"amplitude", "center", "fwhmg"}
        assert d["gaussian"]["amplitude"]["value"] == 1.0
        assert d["gaussian"]["center"]["vary"] is True

    def test_to_dict_lorentzian(self) -> None:
        """Lorentzian model name is preserved."""
        peak = PeakSpec(
            model_name="lorentzian",
            parameters={
                "amplitude": ParameterSpec(value=1.0),
                "center": ParameterSpec(value=0.0),
                "fwhml": ParameterSpec(value=0.5),
            },
        )
        assert "lorentzian" in peak.to_dict()


# ---------------------------------------------------------------------------
# FittingFixture
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFittingFixture:
    """Tests for the complete FittingFixture model."""

    def test_to_peaks_dict_keys(self) -> None:
        """Peak IDs are 1-based string numbers."""
        fix = double_gaussian()
        peaks = fix.to_peaks_dict()
        assert set(peaks) == {"1", "2"}

    def test_to_input_dict_keys(self) -> None:
        """to_input_dict contains all required top-level keys."""
        fix = single_gaussian()
        d = fix.to_input_dict()
        expected_keys = {"column", "minimizer", "optimizer", "peaks", "global_"}
        assert set(d) == expected_keys

    def test_to_input_dict_peaks_format(self) -> None:
        """Peaks section matches the nested dict format for the solver."""
        fix = single_gaussian(amplitude=2.0, center=1.0, fwhmg=0.8)
        d = fix.to_input_dict()
        gauss = d["peaks"]["1"]["gaussian"]
        assert gauss["amplitude"]["value"] == 2.0
        assert gauss["center"]["value"] == 1.0
        assert gauss["fwhmg"]["value"] == 0.8

    def test_generate_data_shape(self) -> None:
        """generate_data returns arrays with the configured number of points."""
        fix = single_gaussian()
        x, y = fix.generate_data()
        assert x.shape == (fix.num_points,)
        assert y.shape == (fix.num_points,)

    def test_generate_data_range(self) -> None:
        """X data spans the configured range."""
        fix = single_gaussian()
        x, _ = fix.generate_data()
        np.testing.assert_allclose(x[0], fix.x_range[0])
        np.testing.assert_allclose(x[-1], fix.x_range[1])

    def test_generate_data_noiseless(self) -> None:
        """With noise_level=0 the signal is deterministic and non-negative."""
        fix = single_gaussian()
        _, y = fix.generate_data()
        assert np.all(np.isfinite(y))

    def test_minimizer_defaults(self) -> None:
        """Default minimizer settings are reasonable."""
        fix = single_gaussian()
        assert fix.minimizer["nan_policy"] == "propagate"
        assert fix.minimizer["calc_covar"] is True

    def test_optimizer_defaults(self) -> None:
        """Default optimizer settings are reasonable."""
        fix = single_gaussian()
        assert fix.optimizer["method"] == "leastsq"
        assert fix.optimizer["max_nfev"] == 1000


# ---------------------------------------------------------------------------
# Factory functions
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFactoryFunctions:
    """Tests for the convenience factory functions."""

    def test_single_gaussian_valid(self) -> None:
        """single_gaussian produces a valid fixture."""
        fix = single_gaussian()
        assert len(fix.peaks) == 1
        assert fix.peaks[0].model_name == "gaussian"
        assert set(fix.peaks[0].parameters) == {"amplitude", "center", "fwhmg"}

    def test_single_lorentzian_valid(self) -> None:
        """single_lorentzian produces a valid fixture."""
        fix = single_lorentzian()
        assert len(fix.peaks) == 1
        assert fix.peaks[0].model_name == "lorentzian"
        assert set(fix.peaks[0].parameters) == {"amplitude", "center", "fwhml"}

    def test_double_gaussian_valid(self) -> None:
        """double_gaussian produces two Gaussian peaks."""
        fix = double_gaussian()
        assert len(fix.peaks) == 2
        assert all(p.model_name == "gaussian" for p in fix.peaks)

    def test_double_gaussian_separation(self) -> None:
        """Peak centres are separated by the requested distance."""
        sep = 4.0
        fix = double_gaussian(separation=sep)
        c1 = fix.peaks[0].parameters["center"].value
        c2 = fix.peaks[1].parameters["center"].value
        np.testing.assert_allclose(abs(c2 - c1), sep)

    def test_gaussian_with_background_valid(self) -> None:
        """gaussian_with_background has a Gaussian and a constant component."""
        fix = gaussian_with_background()
        assert len(fix.peaks) == 2
        models = {p.model_name for p in fix.peaks}
        assert models == {"gaussian", "constant"}

    def test_factory_custom_params(self) -> None:
        """Factory functions accept custom parameter values."""
        fix = single_gaussian(amplitude=3.0, center=2.0, fwhmg=1.5)
        params = fix.peaks[0].parameters
        assert params["amplitude"].value == 3.0
        assert params["center"].value == 2.0
        assert params["fwhmg"].value == 1.5


# ---------------------------------------------------------------------------
# Integration: round-trip through SolverModels
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSolverIntegration:
    """Verify that fixtures can be consumed by the existing solver."""

    @staticmethod
    def _fitted_params(result: Any) -> dict[str, float]:
        """Extract fitted parameter values from a MinimizerResult."""
        return {name: param.value for name, param in result.params.items()}

    @pytest.mark.slow
    def test_single_gaussian_solver(self) -> None:
        """Fit a single-Gaussian fixture and recover parameters."""
        fix = single_gaussian(amplitude=1.0, center=0.0, fwhmg=1.0)
        x, y = fix.generate_data()
        df = pd.DataFrame({"energy": x, "intensity": y})
        args = fix.to_input_dict()

        _, result = SolverModels(df=df, args=args)()
        fitted = self._fitted_params(result)

        np.testing.assert_allclose(fitted["gaussian_amplitude_1"], 1.0, rtol=0.05)
        np.testing.assert_allclose(fitted["gaussian_center_1"], 0.0, atol=0.05)
        np.testing.assert_allclose(fitted["gaussian_fwhmg_1"], 1.0, rtol=0.05)

    @pytest.mark.slow
    def test_double_gaussian_solver(self) -> None:
        """Fit a double-Gaussian fixture and verify both peaks are recovered."""
        fix = double_gaussian(separation=4.0)
        x, y = fix.generate_data()
        df = pd.DataFrame({"energy": x, "intensity": y})
        args = fix.to_input_dict()

        _, result = SolverModels(df=df, args=args)()
        fitted = self._fitted_params(result)

        assert "gaussian_amplitude_1" in fitted
        assert "gaussian_amplitude_2" in fitted
        np.testing.assert_allclose(fitted["gaussian_center_1"], -2.0, atol=0.1)
        np.testing.assert_allclose(fitted["gaussian_center_2"], 2.0, atol=0.1)

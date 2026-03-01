"""Tests for the synthetic spectrum generator."""

from __future__ import annotations

import json

from typing import Any

import numpy as np
import pytest

from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum


class TestPeakDefinition:
    """Tests for the PeakDefinition model."""

    def test_valid_gaussian(self) -> None:
        """Test creating a valid Gaussian peak definition."""
        peak = PeakDefinition(
            model="gaussian",
            params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.5},
        )
        assert peak.model == "gaussian"
        assert peak.params["amplitude"] == 1.0

    def test_valid_pseudovoigt(self) -> None:
        """Test creating a valid PseudoVoigt peak definition."""
        peak = PeakDefinition(
            model="pseudovoigt",
            params={
                "amplitude": 2.0,
                "center": 1.0,
                "fwhmg": 0.3,
                "fwhml": 0.4,
            },
        )
        assert peak.model == "pseudovoigt"

    def test_missing_params(self) -> None:
        """Test that missing parameters raise a validation error."""
        with pytest.raises(ValueError, match="missing required params"):
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0},
            )

    def test_extra_params(self) -> None:
        """Test that extra parameters raise a validation error."""
        with pytest.raises(ValueError, match="unexpected params"):
            PeakDefinition(
                model="gaussian",
                params={
                    "amplitude": 1.0,
                    "center": 0.0,
                    "fwhmg": 0.5,
                    "extra": 1.0,
                },
            )

    def test_unknown_model(self) -> None:
        """Test that an unknown model name raises a validation error."""
        with pytest.raises(ValueError, match="Input should be"):
            PeakDefinition(model="nonexistent", params={"x": 1.0})


class TestSyntheticSpectrum:
    """Tests for the SyntheticSpectrum model."""

    @pytest.fixture
    def single_gaussian(self) -> SyntheticSpectrum:
        """Create a single Gaussian spectrum fixture."""
        return SyntheticSpectrum(
            x_min=-5.0,
            x_max=5.0,
            num_points=500,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
                ),
            ],
            seed=42,
        )

    @pytest.fixture
    def multi_peak(self) -> SyntheticSpectrum:
        """Create a multi-peak spectrum fixture."""
        return SyntheticSpectrum(
            x_min=-10.0,
            x_max=10.0,
            num_points=1000,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.0, "center": -2.0, "fwhmg": 0.8},
                ),
                PeakDefinition(
                    model="lorentzian",
                    params={"amplitude": 0.5, "center": 2.0, "fwhml": 1.2},
                ),
            ],
            seed=42,
        )

    def test_generate_shape(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test that generate returns correct array shapes."""
        x, y, gt = single_gaussian.generate()
        assert x.shape == (500,)
        assert y.shape == (500,)
        assert len(gt["peaks"]) == 1

    def test_generate_no_noise(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test noiseless generation produces exact ground truth."""
        x, y, gt = single_gaussian.generate()
        np.testing.assert_array_equal(y, gt["y_clean"])
        np.testing.assert_array_equal(gt["noise"], np.zeros_like(x))

    def test_generate_with_noise(self) -> None:
        """Test that noise injection produces different results than clean."""
        spectrum = SyntheticSpectrum(
            x_min=-5.0,
            x_max=5.0,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
                ),
            ],
            noise_level=0.1,
            seed=42,
        )
        _x, y, gt = spectrum.generate()
        assert not np.array_equal(y, gt["y_clean"])
        np.testing.assert_allclose(y, gt["y_clean"] + gt["noise"])

    def test_reproducibility(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test that same seed produces identical results."""
        x1, y1, _ = single_gaussian.generate()
        x2, y2, _ = single_gaussian.generate()
        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)

    def test_different_seeds_differ(self) -> None:
        """Test that different seeds produce different noisy results."""
        base: dict[str, Any] = {
            "x_min": -5.0,
            "x_max": 5.0,
            "noise_level": 0.1,
            "peaks": [
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
                ),
            ],
        }
        s1 = SyntheticSpectrum(**base, seed=1)
        s2 = SyntheticSpectrum(**base, seed=2)
        _, y1, _ = s1.generate()
        _, y2, _ = s2.generate()
        assert not np.array_equal(y1, y2)

    def test_multi_peak_components(self, multi_peak: SyntheticSpectrum) -> None:
        """Test that multi-peak spectrum has correct component count."""
        _x, y, gt = multi_peak.generate()
        assert len(gt["components"]) == 2
        assert len(gt["peaks"]) == 2
        # Sum of components equals clean signal
        total = np.sum(gt["components"], axis=0)
        np.testing.assert_array_almost_equal(y, total)

    def test_gaussian_center_recovery(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test that Gaussian peak maximum is at the specified center."""
        x, y, _ = single_gaussian.generate()
        peak_idx = np.argmax(y)
        # Peak should be near center=0.0 (within grid resolution)
        np.testing.assert_allclose(x[peak_idx], 0.0, atol=0.05)

    def test_gaussian_symmetry(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test that Gaussian centered at 0 produces symmetric spectrum."""
        _x, y, _ = single_gaussian.generate()
        np.testing.assert_allclose(y, y[::-1], atol=1e-10)

    def test_x_range_validation(self) -> None:
        """Test that x_min >= x_max raises error."""
        with pytest.raises(ValueError, match=r"x_min.*must be less than.*x_max"):
            SyntheticSpectrum(
                x_min=5.0,
                x_max=-5.0,
                peaks=[
                    PeakDefinition(model="constant", params={"amplitude": 1.0}),
                ],
            )

    def test_min_points_validation(self) -> None:
        """Test that num_points < 2 raises error."""
        with pytest.raises(ValueError):
            SyntheticSpectrum(
                x_min=-1.0,
                x_max=1.0,
                num_points=1,
                peaks=[
                    PeakDefinition(model="constant", params={"amplitude": 1.0}),
                ],
            )

    def test_to_dataframe(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test DataFrame output with correct columns."""
        df = single_gaussian.to_dataframe()
        assert list(df.columns) == ["energy", "intensity"]
        assert len(df) == 500

    def test_to_dataframe_custom_columns(
        self, single_gaussian: SyntheticSpectrum
    ) -> None:
        """Test DataFrame output with custom column names."""
        df = single_gaussian.to_dataframe(
            energy_col="binding_energy", intensity_col="counts"
        )
        assert list(df.columns) == ["binding_energy", "counts"]

    def test_to_spectrafit_input(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test SpectraFit input format generation."""
        config = single_gaussian.to_spectrafit_input()
        assert "peaks" in config
        assert "1" in config["peaks"]
        assert "gaussian" in config["peaks"]["1"]
        params = config["peaks"]["1"]["gaussian"]
        assert params["amplitude"]["value"] == 1.0
        assert params["center"]["value"] == 0.0
        assert params["fwhmg"]["value"] == 1.0
        assert params["amplitude"]["vary"] is True

    def test_to_json_roundtrip(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test JSON serialization roundtrip."""
        json_str = single_gaussian.to_json()
        data = json.loads(json_str)
        reconstructed = SyntheticSpectrum(**data)
        x1, y1, _ = single_gaussian.generate()
        x2, y2, _ = reconstructed.generate()
        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)

    def test_poisson_noise(self) -> None:
        """Test Poisson noise type."""
        spectrum = SyntheticSpectrum(
            x_min=-5.0,
            x_max=5.0,
            peaks=[
                PeakDefinition(
                    model="gaussian",
                    params={"amplitude": 100.0, "center": 0.0, "fwhmg": 1.0},
                ),
            ],
            noise_level=0.1,
            noise_type="poisson",
            seed=42,
        )
        _x, y, gt = spectrum.generate()
        assert not np.array_equal(y, gt["y_clean"])

    def test_ground_truth_metadata(self, single_gaussian: SyntheticSpectrum) -> None:
        """Test that ground truth dict contains expected metadata."""
        _, _, gt = single_gaussian.generate()
        assert gt["noise_level"] == 0.0
        assert gt["noise_type"] == "gaussian"
        assert gt["seed"] == 42
        assert gt["peaks"][0]["model"] == "gaussian"
        assert gt["peaks"][0]["params"]["amplitude"] == 1.0


class TestAllModels:
    """Test that the generator works with every available model."""

    @pytest.mark.parametrize(
        ("model", "params"),
        [
            ("gaussian", {"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0}),
            ("orcagaussian", {"amplitude": 1.0, "center": 0.0, "width": 1.0}),
            ("lorentzian", {"amplitude": 1.0, "center": 0.0, "fwhml": 1.0}),
            ("voigt", {"center": 0.0, "fwhmv": 1.0, "gamma": 0.5}),
            (
                "pseudovoigt",
                {
                    "amplitude": 1.0,
                    "center": 0.0,
                    "fwhmg": 0.5,
                    "fwhml": 0.5,
                },
            ),
            ("exponential", {"amplitude": 1.0, "decay": 1.0, "intercept": 0.0}),
            ("power", {"amplitude": 1.0, "exponent": 2.0, "intercept": 0.0}),
            ("linear", {"slope": 1.0, "intercept": 0.0}),
            ("constant", {"amplitude": 1.0}),
            ("erf", {"amplitude": 1.0, "center": 0.0, "sigma": 1.0}),
            ("heaviside", {"amplitude": 1.0, "center": 0.0, "sigma": 1.0}),
            ("atan", {"amplitude": 1.0, "center": 0.0, "sigma": 1.0}),
            ("log", {"amplitude": 1.0, "center": -6.0, "sigma": 1.0}),
            ("cgaussian", {"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0}),
            ("clorentzian", {"amplitude": 1.0, "center": 0.0, "fwhml": 1.0}),
            ("cvoigt", {"amplitude": 1.0, "center": 0.0, "fwhmv": 1.0, "gamma": 0.5}),
            (
                "polynom2",
                {"coefficient0": 1.0, "coefficient1": 0.0, "coefficient2": 0.0},
            ),
            (
                "polynom3",
                {
                    "coefficient0": 1.0,
                    "coefficient1": 0.0,
                    "coefficient2": 0.0,
                    "coefficient3": 0.0,
                },
            ),
            (
                "pearson1",
                {
                    "amplitude": 1.0,
                    "center": 0.0,
                    "sigma": 1.0,
                    "exponent": 1.5,
                },
            ),
            (
                "pearson2",
                {
                    "amplitude": 1.0,
                    "center": 0.0,
                    "sigma": 1.0,
                    "exponent": 1.5,
                },
            ),
            (
                "pearson3",
                {
                    "amplitude": 1.0,
                    "center": 0.0,
                    "sigma": 1.0,
                    "exponent": 1.5,
                    "skewness": 0.5,
                },
            ),
            (
                "pearson4",
                {
                    "amplitude": 1.0,
                    "center": 0.0,
                    "sigma": 1.0,
                    "exponent": 1.5,
                    "skewness": 0.5,
                    "kurtosis": 3.0,
                },
            ),
        ],
    )
    def test_model_generates(self, model: str, params: dict[str, float]) -> None:
        """Test that every registered model produces valid output."""
        spectrum = SyntheticSpectrum(
            x_min=-5.0,
            x_max=5.0,
            num_points=100,
            peaks=[PeakDefinition(model=model, params=params)],
            seed=42,
        )
        x, y, _gt = spectrum.generate()
        assert x.shape == (100,)
        assert y.shape == (100,)
        # Some models (log, pearson3/4) have domain restrictions that
        # produce NaN outside their valid range. Check that non-NaN values
        # are finite, and that at least some values are valid.
        valid_mask = ~np.isnan(y)
        assert np.any(valid_mask), f"All NaN in {model} output"
        assert not np.any(np.isinf(y[valid_mask])), f"Inf in {model} output"

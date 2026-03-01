"""Tests for the model registry."""

from __future__ import annotations

from typing import ClassVar

import numpy as np
import pytest

from spectrafit.models.registry import REGISTRY
from spectrafit.models.registry import ModelInfo
from spectrafit.models.registry import ModelRegistry


pytestmark = pytest.mark.unit


ALL_MODEL_NAMES = [
    "gaussian",
    "orcagaussian",
    "lorentzian",
    "voigt",
    "pseudovoigt",
    "erf",
    "heaviside",
    "atan",
    "log",
    "cgaussian",
    "clorentzian",
    "cvoigt",
    "polynom2",
    "polynom3",
    "linear",
    "constant",
    "exponential",
    "power",
    "pearson1",
    "pearson2",
    "pearson3",
    "pearson4",
]


class TestRegistryPopulation:
    """Tests for registry population with all 22 models."""

    def test_all_22_models_registered(self) -> None:
        """All 22 distribution models must be registered."""
        assert len(REGISTRY.names()) == 22

    @pytest.mark.parametrize("name", ALL_MODEL_NAMES)
    def test_model_is_registered(self, name: str) -> None:
        """Each expected model name is in the registry."""
        assert name in REGISTRY

    def test_names_returns_sorted(self) -> None:
        """names() returns a sorted list."""
        names = REGISTRY.names()
        assert names == sorted(names)


class TestCategoryFiltering:
    """Tests for category-based filtering."""

    def test_peak_category(self) -> None:
        """Peak category contains expected models."""
        peak_names = {m.name for m in REGISTRY.list_models("peak")}
        assert peak_names == {
            "gaussian",
            "orcagaussian",
            "lorentzian",
            "voigt",
            "pseudovoigt",
        }

    def test_step_category(self) -> None:
        """Step category contains expected models."""
        step_names = {m.name for m in REGISTRY.list_models("step")}
        assert step_names == {"erf", "heaviside", "atan", "log"}

    def test_cumulative_category(self) -> None:
        """Cumulative category contains expected models."""
        cum_names = {m.name for m in REGISTRY.list_models("cumulative")}
        assert cum_names == {"cgaussian", "clorentzian", "cvoigt"}

    def test_polynomial_category(self) -> None:
        """Polynomial category contains expected models."""
        poly_names = {m.name for m in REGISTRY.list_models("polynomial")}
        assert poly_names == {"polynom2", "polynom3"}

    def test_background_category(self) -> None:
        """Background category contains expected models."""
        bg_names = {m.name for m in REGISTRY.list_models("background")}
        assert bg_names == {"linear", "constant", "exponential", "power"}

    def test_pearson_category(self) -> None:
        """Pearson category contains expected models."""
        pearson_names = {m.name for m in REGISTRY.list_models("pearson")}
        assert pearson_names == {"pearson1", "pearson2", "pearson3", "pearson4"}

    def test_list_all(self) -> None:
        """list_models(None) returns all models."""
        assert len(REGISTRY.list_models()) == 22

    def test_categories_sum_to_total(self) -> None:
        """All category counts sum to total model count."""
        categories = [
            "peak",
            "step",
            "cumulative",
            "polynomial",
            "background",
            "pearson",
        ]
        total = sum(len(REGISTRY.list_models(c)) for c in categories)
        assert total == 22


class TestGetContainsNames:
    """Tests for get, __contains__, and names methods."""

    def test_get_returns_model_info(self) -> None:
        """get() returns a ModelInfo instance."""
        info = REGISTRY.get("gaussian")
        assert isinstance(info, ModelInfo)
        assert info.name == "gaussian"
        assert info.category == "peak"

    def test_get_unknown_raises_key_error(self) -> None:
        """get() raises KeyError for unknown model."""
        with pytest.raises(KeyError, match="Unknown model 'nonexistent'"):
            REGISTRY.get("nonexistent")

    def test_contains_true(self) -> None:
        """__contains__ returns True for registered model."""
        assert "gaussian" in REGISTRY

    def test_contains_false(self) -> None:
        """__contains__ returns False for unknown model."""
        assert "nonexistent" not in REGISTRY

    def test_names_is_list_of_str(self) -> None:
        """names() returns a list of strings."""
        names = REGISTRY.names()
        assert isinstance(names, list)
        assert all(isinstance(n, str) for n in names)

    def test_model_info_has_description(self) -> None:
        """All registered models have a non-empty description."""
        for name in REGISTRY.names():
            info = REGISTRY.get(name)
            assert info.description, f"Model '{name}' has empty description"

    def test_model_info_has_parameters(self) -> None:
        """All registered models have non-empty parameters list."""
        for name in REGISTRY.names():
            info = REGISTRY.get(name)
            assert len(info.parameters) > 0, f"Model '{name}' has no parameters"


class TestRegisteredFunctions:
    """Tests that registered functions produce valid output."""

    @pytest.fixture
    def x(self) -> np.ndarray:
        """Common x-values for testing."""
        return np.linspace(-5, 5, 100)

    _DEFAULT_PARAMS: ClassVar[dict[str, dict[str, float]]] = {
        "gaussian": {"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
        "orcagaussian": {"amplitude": 1.0, "center": 0.0, "width": 1.0},
        "lorentzian": {"amplitude": 1.0, "center": 0.0, "fwhml": 1.0},
        "voigt": {"center": 0.0, "fwhmv": 1.0, "gamma": 1.0},
        "pseudovoigt": {
            "amplitude": 1.0,
            "center": 0.0,
            "fwhmg": 1.0,
            "fwhml": 1.0,
        },
        "erf": {"amplitude": 1.0, "center": 0.0, "sigma": 1.0},
        "heaviside": {"amplitude": 1.0, "center": 0.0, "sigma": 1.0},
        "atan": {"amplitude": 1.0, "center": 0.0, "sigma": 1.0},
        "log": {"amplitude": 1.0, "center": 0.0, "sigma": 1.0},
        "cgaussian": {"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
        "clorentzian": {"amplitude": 1.0, "center": 0.0, "fwhml": 1.0},
        "cvoigt": {"amplitude": 1.0, "center": 0.0, "fwhmv": 1.0, "gamma": 1.0},
        "polynom2": {
            "coefficient0": 1.0,
            "coefficient1": 1.0,
            "coefficient2": 1.0,
        },
        "polynom3": {
            "coefficient0": 1.0,
            "coefficient1": 1.0,
            "coefficient2": 1.0,
            "coefficient3": 1.0,
        },
        "linear": {"slope": 1.0, "intercept": 0.0},
        "constant": {"amplitude": 1.0},
        "exponential": {"amplitude": 1.0, "decay": 1.0, "intercept": 0.0},
        "power": {"amplitude": 1.0, "exponent": 1.0, "intercept": 0.0},
        "pearson1": {
            "amplitude": 1.0,
            "center": 0.0,
            "sigma": 1.0,
            "exponent": 1.0,
        },
        "pearson2": {
            "amplitude": 1.0,
            "center": 0.0,
            "sigma": 1.0,
            "exponent": 1.0,
        },
        "pearson3": {
            "amplitude": 1.0,
            "center": 0.0,
            "sigma": 1.0,
            "exponent": 1.0,
            "skewness": 0.0,
        },
        "pearson4": {
            "amplitude": 1.0,
            "center": 0.0,
            "sigma": 1.0,
            "exponent": 1.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
        },
    }

    @pytest.mark.parametrize("name", ALL_MODEL_NAMES)
    def test_function_returns_array(self, name: str, x: np.ndarray) -> None:
        """Each registered function returns a numpy array of correct shape."""
        info = REGISTRY.get(name)
        params = self._DEFAULT_PARAMS[name]
        result = info.function(x, **params)
        assert isinstance(result, np.ndarray)
        assert result.shape == x.shape

    @pytest.mark.parametrize("name", ALL_MODEL_NAMES)
    def test_function_no_nan(self, name: str, x: np.ndarray) -> None:
        """Registered functions should not return NaN for default params.

        Note: The 'log' step function uses np.log internally, which produces
        NaN for negative inputs. We use positive-only x for that model.
        """
        info = REGISTRY.get(name)
        params = self._DEFAULT_PARAMS[name]
        x_test = np.linspace(0.1, 5, 100) if name == "log" else x
        result = info.function(x_test, **params)
        assert not np.any(np.isnan(result)), f"Model '{name}' returned NaN"

    @pytest.mark.parametrize("name", ALL_MODEL_NAMES)
    def test_parameters_match_function(self, name: str) -> None:
        """Registered parameter names match keys in default params."""
        info = REGISTRY.get(name)
        assert set(info.parameters) == set(self._DEFAULT_PARAMS[name].keys())


class TestModelRegistryInstance:
    """Tests for ModelRegistry instance methods."""

    def test_register_and_get(self) -> None:
        """Register a model and retrieve it."""
        registry = ModelRegistry()
        info = ModelInfo(
            name="test_model",
            category="peak",
            function=lambda x: x,
            parameters=["a"],
            description="Test model",
        )
        registry.register(info)
        assert registry.get("test_model") is info

    def test_empty_registry(self) -> None:
        """Empty registry has no models."""
        registry = ModelRegistry()
        assert registry.names() == []
        assert len(registry.list_models()) == 0
        assert "anything" not in registry

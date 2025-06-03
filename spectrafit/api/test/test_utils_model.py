"""Test the utility functions for type-safe API model creation."""

from __future__ import annotations

from typing import Any
from typing import Callable

import numpy as np
import pytest

from spectrafit.api.model_utils import create_amplitude_api
from spectrafit.api.model_utils import create_background_api
from spectrafit.api.model_utils import create_fwhml_api
from spectrafit.api.model_utils import create_hyperfinefield_api
from spectrafit.api.model_utils import create_isomershift_api
from spectrafit.api.model_utils import create_quadrupolesplitting_api
from spectrafit.api.moessbauer_model import AmplitudeAPI
from spectrafit.api.moessbauer_model import BackgroundAPI
from spectrafit.api.moessbauer_model import FwhmlAPI
from spectrafit.api.moessbauer_model import HyperfineFieldAPI
from spectrafit.api.moessbauer_model import IsomerShiftAPI
from spectrafit.api.moessbauer_model import QuadrupoleSplittingAPI


def test_create_quadrupolesplitting_api_basic() -> None:
    """Test creating QuadrupoleSplittingAPI with basic parameters."""
    data: dict[str, float | bool | None] = {
        "value": 0.5,
        "min": -1.0,
        "max": 1.0,
    }

    result = create_quadrupolesplitting_api(data)

    assert isinstance(result, QuadrupoleSplittingAPI)
    assert result.value is not None
    assert result.min is not None
    assert result.max is not None
    assert np.isclose(result.value, 0.5, rtol=1e-10)
    assert np.isclose(result.min, -1.0, rtol=1e-10)
    assert np.isclose(result.max, 1.0, rtol=1e-10)
    assert result.vary is True  # Default value
    assert result.expr is None  # Default value


def test_create_quadrupolesplitting_api_all_params() -> None:
    """Test creating QuadrupoleSplittingAPI with all parameters."""
    data: dict[str, float | bool | None | str] = {
        "value": 0.3,
        "min": -0.5,
        "max": 0.5,
        "vary": False,
        "expr": "2*amp",
    }

    result = create_quadrupolesplitting_api(data)  # type: ignore

    assert isinstance(result, QuadrupoleSplittingAPI)
    assert result.value is not None
    assert result.min is not None
    assert result.max is not None
    assert np.isclose(result.value, 0.3, rtol=1e-10)
    assert np.isclose(result.min, -0.5, rtol=1e-10)
    assert np.isclose(result.max, 0.5, rtol=1e-10)
    assert result.vary is False
    assert result.expr == "2*amp"


def test_create_quadrupolesplitting_api_none_values() -> None:
    """Test creating QuadrupoleSplittingAPI with None values."""
    data: dict[str, float | bool | None] = {
        "value": None,
        "min": None,
        "max": None,
        "vary": None,
    }

    result = create_quadrupolesplitting_api(data)

    assert isinstance(result, QuadrupoleSplittingAPI)
    assert result.value is None
    assert result.min is None
    assert result.max is None
    assert result.vary is True  # Default is True even when None is provided
    assert result.expr is None


def test_create_quadrupolesplitting_api_empty_dict() -> None:
    """Test creating QuadrupoleSplittingAPI with empty dictionary."""
    data: dict[str, float | bool | None] = {}

    result = create_quadrupolesplitting_api(data)

    assert isinstance(result, QuadrupoleSplittingAPI)
    assert result.value is None
    assert result.min is None
    assert result.max is None
    assert result.vary is True
    assert result.expr is None


def test_create_hyperfinefield_api_basic() -> None:
    """Test creating HyperfineFieldAPI with basic parameters."""
    data: dict[str, float | bool | None] = {
        "value": 30.0,
        "min": 0.0,
        "max": 50.0,
    }

    result = create_hyperfinefield_api(data)

    assert isinstance(result, HyperfineFieldAPI)
    assert result.value is not None
    assert result.min is not None
    assert result.max is not None
    assert np.isclose(result.value, 30.0, rtol=1e-10)
    assert np.isclose(result.min, 0.0, rtol=1e-10)
    assert np.isclose(result.max, 50.0, rtol=1e-10)
    assert result.vary is True
    assert result.expr is None


def test_create_hyperfinefield_api_all_params() -> None:
    """Test creating HyperfineFieldAPI with all parameters."""
    data: dict[str, float | bool | None | str] = {
        "value": 25.0,
        "min": 10.0,
        "max": 40.0,
        "vary": False,
        "expr": "field_factor*10",
    }

    result = create_hyperfinefield_api(data)  # type: ignore

    assert isinstance(result, HyperfineFieldAPI)
    assert result.value is not None
    assert result.min is not None
    assert result.max is not None
    assert np.isclose(result.value, 25.0, rtol=1e-10)
    assert np.isclose(result.min, 10.0, rtol=1e-10)
    assert np.isclose(result.max, 40.0, rtol=1e-10)
    assert result.vary is False
    assert result.expr == "field_factor*10"


@pytest.mark.parametrize(
    ("factory_func", "api_class", "test_value"),
    [
        (create_amplitude_api, AmplitudeAPI, 1.0),
        (create_isomershift_api, IsomerShiftAPI, 0.2),
        (create_fwhml_api, FwhmlAPI, 0.3),
        (create_background_api, BackgroundAPI, 0.1),
        (create_quadrupolesplitting_api, QuadrupoleSplittingAPI, 0.5),
        (create_hyperfinefield_api, HyperfineFieldAPI, 25.0),
    ],
)
def test_factory_functions_consistency(
    factory_func: Callable[[dict[str, float | bool | None]], Any],
    api_class: type[Any],
    test_value: float,
) -> None:
    """Test consistency of factory function behavior across different API models.

    Args:
        factory_func: Factory function to test
        api_class: Expected API class type
        test_value: Test value for parameter
    """
    data: dict[str, float | bool | None | str] = {
        "value": test_value,
        "min": test_value / 2,
        "max": test_value * 2,
        "vary": False,
        "expr": "test_expr",
    }

    result = factory_func(data)  # type: ignore

    assert isinstance(result, api_class)
    assert result.value == test_value
    assert result.min == test_value / 2
    assert result.max == test_value * 2
    assert result.vary is False
    assert result.expr == "test_expr"


@pytest.mark.parametrize(
    ("factory_func", "api_class"),
    [
        (create_amplitude_api, AmplitudeAPI),
        (create_isomershift_api, IsomerShiftAPI),
        (create_fwhml_api, FwhmlAPI),
        (create_background_api, BackgroundAPI),
        (create_quadrupolesplitting_api, QuadrupoleSplittingAPI),
        (create_hyperfinefield_api, HyperfineFieldAPI),
    ],
)
def test_factory_functions_with_boolean_strings(
    factory_func: Callable[[dict[str, float | bool | None]], Any],
    api_class: type[Any],
) -> None:
    """Test handling of boolean values that might come from serialized data.

    Args:
        factory_func: Factory function to test
        api_class: Expected API class type
    """
    # Test with boolean values
    data_true: dict[str, float | bool | None] = {"value": 1.0, "vary": True}
    result_true = factory_func(data_true)
    assert result_true.vary is True

    data_false: dict[str, float | bool | None] = {"value": 1.0, "vary": False}
    result_false = factory_func(data_false)
    assert result_false.vary is False


def test_create_api_with_mixed_types() -> None:
    """Test creating API models with mixed data types for vary parameter."""
    # Test with integer 0 (should convert to False)
    data: dict[str, float | bool | None] = {
        "value": 0.5,
        "vary": 0,
    }

    result = create_quadrupolesplitting_api(data)
    assert result.vary is False

    # Test with integer 1 (should convert to True)
    data = {
        "value": 0.5,
        "vary": 1,
    }

    result = create_quadrupolesplitting_api(data)
    assert result.vary is True

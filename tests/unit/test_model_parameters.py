"""Unit tests for ModelParameters (v2.0.0).

Tests the ModelParameters class that lives in ``spectrafit.models.model_parameters``.
Uses UnifiedFittingConfig and the v2 parameter naming: {component_id}_{field}.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lmfit import Parameters
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.model_parameters import ModelParameters


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def simple_df() -> pd.DataFrame:
    """Minimal two-column DataFrame (energy + intensity)."""
    x = np.linspace(-5, 5, 100)
    y = np.exp(-(x**2) / 0.5)
    return pd.DataFrame({"energy": x, "intensity": y})


@pytest.fixture
def simple_config() -> UnifiedFittingConfig:
    """Minimal UnifiedFittingConfig for a single Gaussian peak."""
    return UnifiedFittingConfig(
        components=[
            {
                "id": "p1",
                "model": "gaussian",
                "parameters": {
                    "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                    "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
                    "fwhmg": {"min": 0.01, "max": 1.0, "value": 0.5, "vary": True},
                },
            }
        ]
    )


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestModelParametersConstruction:
    def test_instantiation(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        assert mp is not None

    def test_return_params_is_lmfit_parameters(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        result = mp.return_params
        assert isinstance(result, Parameters)


# ---------------------------------------------------------------------------
# lmfit parameter naming contract  (v2 — {component_id}_{field})
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestLmfitParameterNamingContract:
    """Pin the v2 lmfit parameter name formula: {component_id}_{field}.

    Peak id "1" → sanitized id "p1" → param name "p1_amplitude".
    """

    def test_gaussian_amplitude_name(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        params = mp.return_params
        assert "p1_amplitude" in params

    def test_gaussian_center_name(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        params = mp.return_params
        assert "p1_center" in params

    def test_gaussian_fwhmg_name(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        params = mp.return_params
        assert "p1_fwhmg" in params

    def test_second_peak_naming(self, simple_df: pd.DataFrame) -> None:
        config = UnifiedFittingConfig(
            components=[
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {"value": -1.0, "vary": True},
                        "fwhmg": {"value": 0.5, "vary": True},
                    },
                },
                {
                    "id": "p2",
                    "model": "lorentzian",
                    "parameters": {
                        "amplitude": {"value": 0.8, "vary": True},
                        "center": {"value": 1.0, "vary": True},
                        "fwhml": {"value": 0.5, "vary": True},
                    },
                },
            ]
        )
        mp = ModelParameters(df=simple_df, config=config)
        params = mp.return_params
        assert "p2_amplitude" in params
        assert "p2_center" in params

    def test_parameter_values_match_input(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        params = mp.return_params
        assert params["p1_amplitude"].value == pytest.approx(1.0)
        assert params["p1_center"].value == pytest.approx(0.0)

    def test_parameter_bounds_match_input(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ModelParameters(df=simple_df, config=simple_config)
        params = mp.return_params
        assert params["p1_amplitude"].min == pytest.approx(0.0)
        assert params["p1_amplitude"].max == pytest.approx(2.0)

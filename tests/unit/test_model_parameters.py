"""Unit tests for the canonical parameter builder (v2.0.0).

Tests the builder that now lives in ``spectrafit.models.parameter_builder``.
Uses UnifiedFittingConfig and the v2 parameter naming: {component_id}_{field}.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lmfit import Parameters
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.parameter_builder import ParameterBuilder
from spectrafit.models.parameter_builder import PreparedInputData
from spectrafit.models.parameter_builder import PreparedModelParameters


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
class TestParameterBuilderConstruction:
    def test_instantiation(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        assert mp is not None

    def test_build_params_is_lmfit_parameters(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        result = mp.build().params
        assert isinstance(result, Parameters)

    def test_build_returns_prepared_model_parameters(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        prepared = mp.build()
        assert isinstance(prepared, PreparedModelParameters)
        assert isinstance(prepared.params, Parameters)
        assert prepared.bundle is not None

    def test_prepare_input_data_uses_named_columns(
        self, simple_config: UnifiedFittingConfig
    ) -> None:
        df = pd.DataFrame({"binding_energy": [0.0, 1.0], "counts": [2.0, 3.0]})
        config = simple_config.model_copy(
            update={
                "column": simple_config.column.model_copy(
                    update={"x": "binding_energy", "y": "counts"}
                )
            }
        )
        prepared = ParameterBuilder.prepare_input_data(df=df, config=config)
        assert isinstance(prepared, PreparedInputData)
        np.testing.assert_allclose(prepared.x, np.array([0.0, 1.0]))
        np.testing.assert_allclose(prepared.data, np.array([2.0, 3.0]))
        assert prepared.dataset_count == 1


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
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        params = mp.build().params
        assert "p1_amplitude" in params

    def test_gaussian_center_name(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        params = mp.build().params
        assert "p1_center" in params

    def test_gaussian_fwhmg_name(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        params = mp.build().params
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
        mp = ParameterBuilder(df=simple_df, config=config)
        params = mp.build().params
        assert "p2_amplitude" in params
        assert "p2_center" in params

    def test_parameter_values_match_input(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        params = mp.build().params
        assert params["p1_amplitude"].value == pytest.approx(1.0)
        assert params["p1_center"].value == pytest.approx(0.0)

    def test_parameter_bounds_match_input(
        self, simple_df: pd.DataFrame, simple_config: UnifiedFittingConfig
    ) -> None:
        mp = ParameterBuilder(df=simple_df, config=simple_config)
        params = mp.build().params
        assert params["p1_amplitude"].min == pytest.approx(0.0)
        assert params["p1_amplitude"].max == pytest.approx(2.0)

    def test_global_fit_uses_canonical_names_for_numeric_and_underscore_ids(
        self,
    ) -> None:
        df = pd.DataFrame(
            {
                "energy": [0.0, 1.0],
                "dataset__alpha": [1.0, 1.2],
                "dataset__beta": [0.8, 1.1],
            }
        )
        config = UnifiedFittingConfig(
            components=[
                {
                    "id": "1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {"value": 0.0, "vary": True},
                        "fwhmg": {"value": 0.5, "vary": True},
                    },
                },
                {
                    "id": "gaussian_main_peak",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 0.7, "vary": True},
                        "center": {"value": 0.4, "vary": True},
                        "fwhmg": {"value": 0.3, "vary": True},
                    },
                },
            ],
            context={"mode": "global", "n_datasets": 2},
            global_fitting_config=GlobalFittingConfig(
                n_datasets=2,
                shared_parameters=[
                    {"name": "1_center"},
                    {"name": "gaussian_main_peak_amplitude"},
                ],
            ),
        )

        params = ParameterBuilder(df=df, config=config).define_parameters_global()

        assert "p1_amplitude_1" in params
        assert "p1_center_1" in params
        assert params["p1_center_2"].expr == "p1_center_1"
        assert "gaussian_main_peak_center_1" in params
        assert params["gaussian_main_peak_amplitude_2"].expr == (
            "gaussian_main_peak_amplitude_1"
        )
        assert not any("dataset__" in name for name in params)

    def test_global_pre_uses_canonical_names_for_numeric_ids(self) -> None:
        df = pd.DataFrame(
            {
                "energy": [0.0, 1.0],
                "intensity_1": [1.0, 1.1],
                "intensity_2": [0.9, 1.0],
            }
        )
        config = UnifiedFittingConfig(
            components=[
                {
                    "id": "1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {"value": 0.0, "vary": True},
                        "fwhmg": {"value": 0.5, "vary": True},
                    },
                }
            ],
            context={"mode": "global", "n_datasets": 2},
            global_fitting_config=GlobalFittingConfig(n_datasets=2),
        )

        params = ParameterBuilder(df=df, config=config).define_parameters_global_pre()

        assert "p1_amplitude" in params
        assert "p1_center" in params
        assert "1_amplitude" not in params

    def test_build_uses_dataset_scoped_global_names_when_global_config_present(self) -> None:
        df = pd.DataFrame(
            {
                "energy": [0.0, 1.0],
                "intensity_1": [1.0, 1.1],
                "intensity_2": [0.9, 1.0],
            }
        )
        config = UnifiedFittingConfig(
            components=[
                {
                    "id": "1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {"value": 0.0, "vary": True},
                        "fwhmg": {"value": 0.5, "vary": True},
                    },
                }
            ],
            context={"mode": "global", "n_datasets": 2},
            global_fitting_config=GlobalFittingConfig(n_datasets=2),
        )

        prepared = ParameterBuilder(df=df, config=config).build()

        assert "p1_amplitude_1" in prepared.params
        assert "p1_center_2" in prepared.params
        assert prepared.component_models == {"p1": "gaussian"}

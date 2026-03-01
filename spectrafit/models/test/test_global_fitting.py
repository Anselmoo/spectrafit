"""Tests for global fitting models and shared parameter support."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest

from lmfit import Parameters
from pydantic import ValidationError

from spectrafit.models.global_fitting import DatasetResult
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.global_fitting import GlobalFittingResult
from spectrafit.models.global_fitting import SharedParameter


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# SharedParameter model tests
# ---------------------------------------------------------------------------


class TestSharedParameter:
    """Tests for the SharedParameter Pydantic model."""

    def test_create_minimal(self) -> None:
        """SharedParameter can be created with only the required name field."""
        sp = SharedParameter(name="pseudovoigt_center_1")
        assert sp.name == "pseudovoigt_center_1"
        assert sp.constraint_expr is None
        assert sp.datasets == []

    def test_create_full(self) -> None:
        """SharedParameter stores constraint_expr and datasets."""
        sp = SharedParameter(
            name="gaussian_center_1",
            constraint_expr="gaussian_center_1_1",
            datasets=[0, 1, 2],
        )
        assert sp.constraint_expr == "gaussian_center_1_1"
        assert sp.datasets == [0, 1, 2]

    def test_frozen(self) -> None:
        """SharedParameter instances are immutable."""
        sp = SharedParameter(name="x")
        with pytest.raises(ValidationError):
            sp.name = "y"  # type: ignore[misc]

    def test_empty_name_rejected(self) -> None:
        """SharedParameter rejects empty name."""
        with pytest.raises(ValidationError):
            SharedParameter(name="")


# ---------------------------------------------------------------------------
# GlobalFittingConfig tests
# ---------------------------------------------------------------------------


class TestGlobalFittingConfig:
    """Tests for the GlobalFittingConfig Pydantic model."""

    def test_minimal_config(self) -> None:
        """Config with only n_datasets is valid."""
        cfg = GlobalFittingConfig(n_datasets=3)
        assert cfg.n_datasets == 3
        assert cfg.shared_parameters == []
        assert cfg.weights is None

    def test_with_weights(self) -> None:
        """Weights matching n_datasets are accepted."""
        cfg = GlobalFittingConfig(n_datasets=2, weights=[1.0, 0.5])
        assert cfg.weights == [1.0, 0.5]

    def test_weights_length_mismatch_raises(self) -> None:
        """Weights length != n_datasets raises ValueError."""
        with pytest.raises(ValueError, match="weights"):
            GlobalFittingConfig(n_datasets=3, weights=[1.0, 0.5])

    def test_shared_parameters_stored(self) -> None:
        """Shared parameters are correctly stored."""
        sp = SharedParameter(name="gaussian_center_1", datasets=[0, 1])
        cfg = GlobalFittingConfig(n_datasets=2, shared_parameters=[sp])
        assert len(cfg.shared_parameters) == 1
        assert cfg.shared_parameters[0].name == "gaussian_center_1"

    def test_dataset_index_out_of_range_raises(self) -> None:
        """Dataset index >= n_datasets raises ValueError."""
        sp = SharedParameter(name="x", datasets=[0, 5])
        with pytest.raises(ValueError, match="out of range"):
            GlobalFittingConfig(n_datasets=3, shared_parameters=[sp])

    def test_n_datasets_zero_raises(self) -> None:
        """n_datasets must be >= 1."""
        with pytest.raises(ValidationError):
            GlobalFittingConfig(n_datasets=0)


# ---------------------------------------------------------------------------
# GlobalFittingResult tests
# ---------------------------------------------------------------------------


class TestGlobalFittingResult:
    """Tests for the GlobalFittingResult Pydantic model."""

    @pytest.fixture
    def sample_config(self) -> GlobalFittingConfig:
        """Create a sample GlobalFittingConfig.

        Returns:
            GlobalFittingConfig: A config with 2 datasets and one shared param.
        """
        sp = SharedParameter(name="gaussian_center_1", datasets=[0, 1])
        return GlobalFittingConfig(
            n_datasets=2,
            shared_parameters=[sp],
            weights=[1.0, 2.0],
        )

    @pytest.fixture
    def sample_result(self, sample_config: GlobalFittingConfig) -> GlobalFittingResult:
        """Create a sample GlobalFittingResult.

        Args:
            sample_config: Config fixture.

        Returns:
            GlobalFittingResult: A populated result object.
        """
        return GlobalFittingResult(
            config=sample_config,
            dataset_results=[
                DatasetResult(
                    index=0,
                    chi_squared=1.5,
                    reduced_chi_squared=0.8,
                    parameters={"a": 1.0},
                ),
                DatasetResult(
                    index=1,
                    chi_squared=2.0,
                    reduced_chi_squared=1.1,
                    parameters={"a": 1.1},
                ),
            ],
            shared_parameter_values={"gaussian_center_1": 5.0},
            correlation_matrix={"a": {"a": 1.0}},
        )

    def test_serialization_roundtrip(self, sample_result: GlobalFittingResult) -> None:
        """Result can be serialized and deserialized."""
        d = sample_result.to_dict()
        assert isinstance(d, dict)
        assert d["config"]["n_datasets"] == 2
        assert d["shared_parameter_values"]["gaussian_center_1"] == 5.0

        restored = GlobalFittingResult(**d)
        assert restored.config.n_datasets == sample_result.config.n_datasets

    def test_model_dump(self, sample_result: GlobalFittingResult) -> None:
        """model_dump produces a plain dict."""
        d = sample_result.model_dump()
        assert len(d["dataset_results"]) == 2
        assert d["dataset_results"][0]["index"] == 0

    def test_dataset_result_defaults(self) -> None:
        """DatasetResult has sensible defaults for optional fields."""
        dr = DatasetResult(index=0)
        assert dr.chi_squared is None
        assert dr.parameters == {}


# ---------------------------------------------------------------------------
# Integration: shared parameters in lmfit Parameters
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestSharedParameterLinking:
    """Test that shared parameters correctly constrain lmfit Parameters."""

    @staticmethod
    def _build_global_params(
        n_datasets: int,
        peaks: dict[str, Any],
        config: GlobalFittingConfig | None = None,
    ) -> Parameters:
        """Build lmfit Parameters mimicking global fitting.

        Args:
            n_datasets: Number of datasets.
            peaks: Peak definition dict.
            config: Optional GlobalFittingConfig.

        Returns:
            Parameters: Configured lmfit Parameters.
        """
        import pandas as pd

        from spectrafit.models.autopeak import ModelParameters

        cols = ["x"] + [f"data_{i}" for i in range(n_datasets)]
        df = pd.DataFrame(
            np.random.default_rng(42).random((20, len(cols))), columns=cols
        )

        args: dict[str, Any] = {
            "peaks": peaks,
            "global_": 1,
            "column": cols,
        }
        if config is not None:
            args["global_fitting_config"] = config

        mp = ModelParameters(df=df, args=args)
        return mp.return_params

    def test_default_linking_without_config(self) -> None:
        """Without GlobalFittingConfig, non-amplitude params link to dataset 1."""
        peaks: dict[str, Any] = {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0, "max": 10},
                    "center": {"value": 0.0, "vary": True, "min": -5, "max": 5},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2},
                }
            }
        }
        params = self._build_global_params(n_datasets=2, peaks=peaks)

        # center for dataset 2 should be expression-linked to dataset 1
        assert params["gaussian_center_1_2"].expr == "gaussian_center_1_1"
        # amplitude should be free for both
        assert params["gaussian_amplitude_1_1"].vary is True
        assert params["gaussian_amplitude_1_2"].vary is True

    def test_shared_param_links_specific_datasets(self) -> None:
        """SharedParameter links center across specified datasets."""
        peaks: dict[str, Any] = {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0, "max": 10},
                    "center": {"value": 0.0, "vary": True, "min": -5, "max": 5},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2},
                }
            }
        }
        sp = SharedParameter(name="gaussian_fwhmg_1", datasets=[0, 1])
        cfg = GlobalFittingConfig(n_datasets=2, shared_parameters=[sp])
        params = self._build_global_params(n_datasets=2, peaks=peaks, config=cfg)

        # fwhmg for dataset 2 linked via shared parameter
        assert params["gaussian_fwhmg_1_2"].expr is not None

    def test_custom_constraint_expr(self) -> None:
        """SharedParameter can use a custom constraint expression."""
        peaks: dict[str, Any] = {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0, "max": 10},
                    "center": {"value": 0.0, "vary": True, "min": -5, "max": 5},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2},
                }
            }
        }
        sp = SharedParameter(
            name="gaussian_center_1",
            constraint_expr="gaussian_center_1_1 + 0.1",
            datasets=[0, 1],
        )
        cfg = GlobalFittingConfig(n_datasets=2, shared_parameters=[sp])
        params = self._build_global_params(n_datasets=2, peaks=peaks, config=cfg)

        assert params["gaussian_center_1_2"].expr == "gaussian_center_1_1 + 0.1"


# ---------------------------------------------------------------------------
# Per-dataset weighting
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestPerDatasetWeighting:
    """Test that per-dataset weights are applied in global fitting residuals."""

    def test_weights_scale_residual(self) -> None:
        """Weights multiply per-column residual before flattening."""
        from spectrafit.models.solver import SolverModels

        x = np.linspace(-5, 5, 50)
        data = np.column_stack([np.exp(-(x**2)), 2 * np.exp(-(x**2))])

        params = Parameters()
        params.add("gaussian_amplitude_1_1", value=1.0)
        params.add("gaussian_center_1_1", value=0.0)
        params.add("gaussian_fwhmg_1_1", value=1.0)
        params.add("gaussian_amplitude_1_2", value=2.0)
        params.add("gaussian_center_1_2", expr="gaussian_center_1_1")
        params.add("gaussian_fwhmg_1_2", expr="gaussian_fwhmg_1_1")

        res_no_weight = SolverModels.solve_global_fitting(params, x, data)
        cfg = GlobalFittingConfig(n_datasets=2, weights=[1.0, 0.5])
        res_weighted = SolverModels.solve_global_fitting(params, x, data, config=cfg)

        # Weighted residual should differ from unweighted
        assert not np.allclose(res_no_weight, res_weighted)

    def test_equal_weights_same_as_no_weights(self) -> None:
        """Weights of [1.0, 1.0] should produce the same residual as no config."""
        from spectrafit.models.solver import SolverModels

        x = np.linspace(-5, 5, 50)
        data = np.column_stack([np.exp(-(x**2)), 2 * np.exp(-(x**2))])

        params = Parameters()
        params.add("gaussian_amplitude_1_1", value=1.0)
        params.add("gaussian_center_1_1", value=0.0)
        params.add("gaussian_fwhmg_1_1", value=1.0)
        params.add("gaussian_amplitude_1_2", value=2.0)
        params.add("gaussian_center_1_2", expr="gaussian_center_1_1")
        params.add("gaussian_fwhmg_1_2", expr="gaussian_fwhmg_1_1")

        res_none = SolverModels.solve_global_fitting(params, x, data)
        cfg = GlobalFittingConfig(n_datasets=2, weights=[1.0, 1.0])
        res_equal = SolverModels.solve_global_fitting(params, x, data, config=cfg)

        np.testing.assert_allclose(res_none, res_equal)

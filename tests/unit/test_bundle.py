"""Tests for Phase 6.3 — CompositeModelBundle.

Verifies:
- build_composite_bundle merges params from all components
- decompose returns per-component curves that sum to the total
- user constraints (min, max, vary, expr) are applied via apply_parameters
- empty components list raises ValueError
- cross-component expr constraints work
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from lmfit import Parameters
from spectrafit.models.bundle import build_composite_bundle
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.registry import REGISTRY
from spectrafit.models.solver import SolverModels
from spectrafit.models.solver import calculated_model


@pytest.fixture
def gaussian_component() -> Component:
    return Component(
        id="p1",
        model="gaussian",
        parameters={
            "amplitude": FitParameter(value=1.0, min=0.0, max=5.0),
            "center": FitParameter(value=0.0, min=-2.0, max=2.0),
            "fwhmg": FitParameter(value=0.5, min=0.05, max=2.0),
        },
    )


@pytest.fixture
def linear_component() -> Component:
    return Component(
        id="bg",
        model="linear",
        parameters={
            "slope": FitParameter(value=0.0, vary=False),
            "intercept": FitParameter(value=0.0, vary=True),
        },
    )


class TestBuildCompositeBundle:
    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            build_composite_bundle([])

    def test_single_component_params(self, gaussian_component: Component) -> None:
        bundle = build_composite_bundle([gaussian_component])
        keys = sorted(bundle.params.keys())
        assert keys == ["p1_amplitude", "p1_center", "p1_fwhmg"]

    def test_two_components_merged_params(
        self, gaussian_component: Component, linear_component: Component
    ) -> None:
        bundle = build_composite_bundle([gaussian_component, linear_component])
        keys = sorted(bundle.params.keys())
        assert "p1_amplitude" in keys
        assert "bg_slope" in keys
        assert "bg_intercept" in keys

    def test_user_constraints_applied(self, gaussian_component: Component) -> None:
        bundle = build_composite_bundle([gaussian_component])
        assert bundle.params["p1_amplitude"].value == pytest.approx(1.0)
        assert bundle.params["p1_amplitude"].min == pytest.approx(0.0)
        assert bundle.params["p1_amplitude"].max == pytest.approx(5.0)
        assert (
            bundle.params["bg_slope"].vary is False
            if "bg_slope" in bundle.params
            else True
        )

    def test_vary_false_applied(self, linear_component: Component) -> None:
        bundle = build_composite_bundle([linear_component])
        assert bundle.params["bg_slope"].vary is False

    def test_parts_ordered_correctly(
        self, gaussian_component: Component, linear_component: Component
    ) -> None:
        bundle = build_composite_bundle([gaussian_component, linear_component])
        assert bundle.parts[0][0] == "p1"
        assert bundle.parts[1][0] == "bg"


class TestDecompose:
    def test_decompose_keys_match_component_ids(
        self, gaussian_component: Component, linear_component: Component
    ) -> None:
        bundle = build_composite_bundle([gaussian_component, linear_component])
        x = np.linspace(-3, 3, 50)
        # Use bundle.params directly (no fit, just evaluate defaults)
        curves = bundle.decompose(bundle.params, x)
        assert set(curves.keys()) == {"p1", "bg"}

    def test_decompose_curves_sum_to_composite(
        self, gaussian_component: Component, linear_component: Component
    ) -> None:
        """Sum of component curves == composite.eval()."""
        bundle = build_composite_bundle([gaussian_component, linear_component])
        x = np.linspace(-3, 3, 50)
        total = bundle.composite.eval(bundle.params, x=x)
        curves = bundle.decompose(bundle.params, x)
        reconstructed = sum(curves.values())
        np.testing.assert_allclose(reconstructed, total, rtol=1e-10)

    def test_end_to_end_fit_and_decompose(self) -> None:
        """Fit a synthetic Gaussian+linear spectrum and decompose."""
        rng = np.random.default_rng(42)
        x = np.linspace(-3, 3, 100)
        # True signal: gaussian amplitude=2, center=0, fwhmg=1, bg slope=0.1
        y_true = (
            2.0 * np.exp(-0.5 * (x / 0.4247) ** 2) / (0.4247 * np.sqrt(2 * np.pi))
            + 0.1 * x
            + 0.05
        )
        y_noisy = y_true + rng.normal(0, 0.02, len(x))

        components = [
            Component(
                id="peak",
                model="gaussian",
                parameters={
                    "amplitude": FitParameter(value=1.5, min=0.0, max=5.0),
                    "center": FitParameter(value=0.1, min=-1.0, max=1.0),
                    "fwhmg": FitParameter(value=0.8, min=0.1, max=2.0),
                },
            ),
            Component(
                id="bg",
                model="linear",
                parameters={
                    "slope": FitParameter(value=0.0, min=-1.0, max=1.0),
                    "intercept": FitParameter(value=0.0, min=-1.0, max=1.0),
                },
            ),
        ]

        bundle = build_composite_bundle(components)
        result = bundle.composite.fit(y_noisy, bundle.params, x=x)
        curves = bundle.decompose(result.params, x)

        # Decomposed curves sum to the total fit
        total_fit = result.best_fit
        reconstructed = sum(curves.values())
        np.testing.assert_allclose(reconstructed, total_fit, rtol=1e-10)

        # Fit converged
        assert result.success or result.errorbars

    def test_decompose_returns_arrays(self, gaussian_component: Component) -> None:
        bundle = build_composite_bundle([gaussian_component])
        x = np.linspace(-1, 1, 20)
        curves = bundle.decompose(bundle.params, x)
        for v in curves.values():
            assert isinstance(v, np.ndarray)
            assert len(v) == len(x)

    def test_calculated_model_requires_bundle_for_local_fit(
        self,
        gaussian_component: Component,
    ) -> None:
        x = np.linspace(-1, 1, 20)
        df = pd.DataFrame({"energy": x, "intensity": np.zeros_like(x)})

        with pytest.raises(
            RuntimeError,
            match="CompositeModelBundle required for local decomposition",
        ):
            calculated_model(
                params=build_composite_bundle([gaussian_component]).params,
                x=x,
                df=df,
                global_fit=False,
            )


class TestCrossComponentExpr:
    def test_expr_constraint_applied(self) -> None:
        """Component 2 amplitude tied to component 1 amplitude via expr."""
        comp1 = Component(
            id="main",
            model="gaussian",
            parameters={
                "amplitude": FitParameter(value=2.0, min=0.0, max=5.0),
                "center": FitParameter(value=0.0),
                "fwhmg": FitParameter(value=0.5),
            },
        )
        comp2 = Component(
            id="sat",
            model="gaussian",
            parameters={
                # expr uses underscore notation (pre-translated)
                "amplitude": FitParameter(value=0.5, expr="main_amplitude * 0.3"),
                "center": FitParameter(value=1.0),
                "fwhmg": FitParameter(value=0.5),
            },
        )
        bundle = build_composite_bundle([comp1, comp2])
        # sat_amplitude should be constrained (expr set)
        assert bundle.params["sat_amplitude"].expr == "main_amplitude * 0.3"


class TestGlobalContributionAssembly:
    @staticmethod
    def _global_params() -> Parameters:
        params = Parameters()
        params.add("gaussian_main_amplitude_1", value=1.0)
        params.add("gaussian_main_center_1", value=0.0)
        params.add("gaussian_main_fwhmg_1", value=0.5)
        params.add("gaussian_main_amplitude_2", value=0.5)
        params.add("gaussian_main_center_2", value=0.5)
        params.add("gaussian_main_fwhmg_2", value=0.75)
        return params

    def test_calculated_model_global_preserves_full_contribution_id(self) -> None:
        params = self._global_params()
        x = np.linspace(-2, 2, 40)
        df = pd.DataFrame(
            {
                "energy": x,
                "intensity_1": np.zeros_like(x),
                "intensity_2": np.zeros_like(x),
            }
        )

        result = calculated_model(params=params, x=x, df=df, global_fit=True)

        expected_1 = REGISTRY.get("gaussian").function(
            x,
            amplitude=params["gaussian_main_amplitude_1"],
            center=params["gaussian_main_center_1"],
            fwhmg=params["gaussian_main_fwhmg_1"],
        )
        expected_2 = REGISTRY.get("gaussian").function(
            x,
            amplitude=params["gaussian_main_amplitude_2"],
            center=params["gaussian_main_center_2"],
            fwhmg=params["gaussian_main_fwhmg_2"],
        )

        assert "gaussian_main_1" in result.columns
        assert "gaussian_main_2" in result.columns
        np.testing.assert_allclose(result["gaussian_main_1"], expected_1)
        np.testing.assert_allclose(result["gaussian_main_2"], expected_2)

    def test_calculated_model_global_supports_canonical_component_ids_with_model_map(
        self,
    ) -> None:
        params = Parameters()
        params.add("p1_amplitude_1", value=1.0)
        params.add("p1_center_1", value=0.0)
        params.add("p1_fwhmg_1", value=0.5)
        params.add("p1_amplitude_2", value=0.5)
        params.add("p1_center_2", value=0.5)
        params.add("p1_fwhmg_2", value=0.75)
        x = np.linspace(-2, 2, 40)
        df = pd.DataFrame(
            {
                "energy": x,
                "intensity_1": np.zeros_like(x),
                "intensity_2": np.zeros_like(x),
            }
        )

        result = calculated_model(
            params=params,
            x=x,
            df=df,
            global_fit=True,
            component_models={"p1": "gaussian"},
        )

        assert "p1_1" in result.columns
        assert "p1_2" in result.columns

    def test_solve_global_fitting_assembles_contributions_by_dataset(self) -> None:
        params = self._global_params()
        x = np.linspace(-2, 2, 40)
        data = np.column_stack(
            [
                REGISTRY.get("gaussian").function(
                    x,
                    amplitude=params["gaussian_main_amplitude_1"],
                    center=params["gaussian_main_center_1"],
                    fwhmg=params["gaussian_main_fwhmg_1"],
                ),
                REGISTRY.get("gaussian").function(
                    x,
                    amplitude=params["gaussian_main_amplitude_2"],
                    center=params["gaussian_main_center_2"],
                    fwhmg=params["gaussian_main_fwhmg_2"],
                ),
            ]
        )

        residual = SolverModels.solve_global_fitting(params=params, x=x, data=data)

        assert residual.shape == (x.size * data.shape[1],)
        np.testing.assert_allclose(residual, np.zeros_like(residual))

    def test_solve_global_fitting_supports_canonical_component_ids_with_model_map(
        self,
    ) -> None:
        params = Parameters()
        params.add("p1_amplitude_1", value=1.0)
        params.add("p1_center_1", value=0.0)
        params.add("p1_fwhmg_1", value=0.5)
        params.add("p1_amplitude_2", value=0.5)
        params.add("p1_center_2", value=0.5)
        params.add("p1_fwhmg_2", value=0.75)
        x = np.linspace(-2, 2, 40)
        data = np.column_stack(
            [
                REGISTRY.get("gaussian").function(
                    x,
                    amplitude=params["p1_amplitude_1"],
                    center=params["p1_center_1"],
                    fwhmg=params["p1_fwhmg_1"],
                ),
                REGISTRY.get("gaussian").function(
                    x,
                    amplitude=params["p1_amplitude_2"],
                    center=params["p1_center_2"],
                    fwhmg=params["p1_fwhmg_2"],
                ),
            ]
        )

        residual = SolverModels.solve_global_fitting(
            params=params,
            x=x,
            data=data,
            component_models={"p1": "gaussian"},
        )

        assert residual.shape == (x.size * data.shape[1],)
        np.testing.assert_allclose(residual, np.zeros_like(residual))

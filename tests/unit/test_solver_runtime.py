"""Unit tests for the core solver runtime ownership split."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.solver import SolverModels


LOCAL_CONFIG: dict[str, object] = {
    "components": [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                "center": {"min": -1, "max": 1, "value": 0.0, "vary": True},
                "fwhmg": {"min": 0.1, "max": 2.0, "value": 0.7, "vary": True},
            },
        }
    ],
    "column": {"x": "energy", "y": "intensity"},
    "minimizer": {"nan_policy": "omit", "calc_covar": False},
    "optimizer": {"max_nfev": 17, "method": "powell"},
    "context": {"mode": "standard"},
}


GLOBAL_CONFIG: dict[str, object] = {
    "components": [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"value": 1.0, "vary": True},
                "center": {"value": 0.0, "vary": True},
                "fwhmg": {"value": 0.5, "vary": True},
            },
        }
    ],
    "context": {"mode": "global", "n_datasets": 2},
}


@pytest.mark.unit
def test_build_solver_models_returns_core_runtime() -> None:
    from spectrafit.core.pipeline import build_solver_models
    from spectrafit.core.solver_runtime import LmfitSolverRuntime

    df = pd.DataFrame({"energy": [0.0, 1.0], "intensity": [1.0, 0.5]})
    config = UnifiedFittingConfig.from_dict(LOCAL_CONFIG)

    solver = build_solver_models(df=df, config=config)

    assert isinstance(solver, LmfitSolverRuntime)


@pytest.mark.unit
def test_runtime_builds_local_execution_plan() -> None:
    from spectrafit.core.solver_runtime import LmfitSolverRuntime

    df = pd.DataFrame({"energy": [0.0, 1.0], "intensity": [1.0, 0.5]})
    config = UnifiedFittingConfig.from_dict(LOCAL_CONFIG)

    runtime = LmfitSolverRuntime(df=df, config=config)
    plan = runtime.build_execution_plan()

    assert plan.residual is SolverModels.solve_local_fitting
    assert plan.bundle is not None
    assert runtime.bundle is plan.bundle
    np.testing.assert_array_equal(plan.fcn_args[0], df["energy"].to_numpy())
    np.testing.assert_array_equal(plan.fcn_args[1], df["intensity"].to_numpy())
    assert plan.fcn_args[2] is plan.bundle


@pytest.mark.unit
def test_runtime_builds_global_execution_plan() -> None:
    from spectrafit.core.solver_runtime import LmfitSolverRuntime

    df = pd.DataFrame(
        {
            "energy": [0.0, 1.0],
            "intensity_1": [1.0, 0.5],
            "intensity_2": [0.8, 0.2],
        }
    )
    config = UnifiedFittingConfig(
        **GLOBAL_CONFIG,
        global_fitting_config=GlobalFittingConfig(n_datasets=2),
    )

    runtime = LmfitSolverRuntime(df=df, config=config)
    plan = runtime.build_execution_plan()

    assert plan.residual is SolverModels.solve_global_fitting
    assert plan.bundle is None
    assert runtime.bundle is None
    np.testing.assert_array_equal(plan.fcn_args[0], df["energy"].to_numpy())
    np.testing.assert_array_equal(
        plan.fcn_args[1],
        df[["intensity_1", "intensity_2"]].to_numpy(),
    )
    assert plan.fcn_args[2] == config.global_fitting_config
    assert plan.fcn_args[3] == {"p1": "gaussian"}


@pytest.mark.unit
def test_runtime_solve_forwards_solver_config(monkeypatch: pytest.MonkeyPatch) -> None:
    from spectrafit.core.solver_runtime import LmfitSolverRuntime

    df = pd.DataFrame({"energy": [0.0, 1.0], "intensity": [1.0, 0.5]})
    config = UnifiedFittingConfig.from_dict(LOCAL_CONFIG)
    captured: dict[str, object] = {}
    result_sentinel = object()

    class FakeMinimizer:
        def __init__(
            self,
            residual: object,
            params: object,
            fcn_args: tuple[object, ...],
            **kwargs: object,
        ) -> None:
            captured["residual"] = residual
            captured["params"] = params
            captured["fcn_args"] = fcn_args
            captured["minimizer_kwargs"] = kwargs

        def minimize(self, **kwargs: object) -> object:
            captured["optimizer_kwargs"] = kwargs
            return result_sentinel

    monkeypatch.setattr("spectrafit.core.solver_runtime.Minimizer", FakeMinimizer)

    runtime = LmfitSolverRuntime(df=df, config=config)
    minimizer, result = runtime.solve()

    assert isinstance(minimizer, FakeMinimizer)
    assert result is result_sentinel
    assert captured["residual"] is SolverModels.solve_local_fitting
    assert captured["minimizer_kwargs"] == {
        "nan_policy": "omit",
        "calc_covar": False,
    }
    assert captured["optimizer_kwargs"] == {
        "max_nfev": 17,
        "method": "powell",
    }

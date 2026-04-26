"""Solver models for curve fitting.

This module contains the SolverModels class and helper functions for solving
fitting problems using lmfit.
"""

from __future__ import annotations

import warnings

from math import log
from math import pi
from math import sqrt
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict

from spectrafit.models.naming import global_contribution_name


if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from lmfit import Parameters
    from numpy.typing import NDArray

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.core.solver_runtime import SolverExecutionPlan
    from spectrafit.models.bundle import CompositeModelBundle
    from spectrafit.models.global_fitting import GlobalFittingConfig

_CANONICAL_SOLVER_DEPENDENCY_MARKERS = (
    "from spectrafit.models.parameter_builder import ParameterBuilder",
    "from spectrafit.models.solver_config import SolverConfig",
)


class SolverModels:
    """Solver residual helpers plus a compatibility runtime shim.

    Runtime orchestration now lives in :mod:`spectrafit.core.solver_runtime`
    per ADR-004. This class remains as the canonical home for residual helpers
    and as a thin compatibility wrapper for direct ``SolverModels(...)`` usage.
    """

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Create a compatibility wrapper around the core solver runtime."""
        warnings.warn(
            "SolverModels is a legacy compatibility wrapper; instantiate "
            "spectrafit.core.solver_runtime.LmfitSolverRuntime directly for new code.",
            FutureWarning,
            stacklevel=2,
        )
        from spectrafit.core.solver_runtime import LmfitSolverRuntime  # noqa: PLC0415

        self._runtime = LmfitSolverRuntime(df=df, config=config)

    @property
    def bundle(self) -> CompositeModelBundle | None:
        """Return the prepared local-fit bundle when available."""
        return self._runtime.bundle

    def build_execution_plan(self) -> SolverExecutionPlan:
        """Build an explicit solver execution plan via the core runtime."""
        return self._runtime.build_execution_plan()

    def solve(self) -> tuple[object, object]:
        """Solve the fitting model via the core runtime."""
        return self._runtime.solve()

    @staticmethod
    def solve_local_fitting(
        params: Parameters,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
        bundle: CompositeModelBundle,
    ) -> NDArray[np.float64]:
        """Delegate local residual calculation to the core runtime owner."""
        from spectrafit.core.solver_runtime import solve_local_fitting  # noqa: PLC0415

        return solve_local_fitting(
            params=params,
            x=x,
            data=data,
            bundle=bundle,
        )

    @staticmethod
    def solve_global_fitting(
        params: Parameters,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
        config: GlobalFittingConfig | None = None,
        component_models: dict[str, str] | None = None,
    ) -> NDArray[np.float64]:
        """Delegate global residual calculation to the core runtime owner."""
        from spectrafit.core.solver_runtime import solve_global_fitting  # noqa: PLC0415

        return solve_global_fitting(
            params=params,
            x=x,
            data=data,
            config=config,
            component_models=component_models,
        )


def calculated_model(
    params: Parameters,
    x: NDArray[np.float64],
    df: pd.DataFrame,
    global_fit: bool,
    bundle: CompositeModelBundle | None = None,
    component_models: dict[str, str] | None = None,
) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

    !!! note "About calculated models"
        `calculated_model` are also wrapper functions similar to `solve_model`. The
        overall goal is to extract from the best parameters the single contributions in
        the model. Currently, `lmfit` provides only a single model, so the best-fit.

    Args:
        params (Parameters): The best optimized parameters of the fit.
        x (NDArray[np.float64]): `x`-values of the data.
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        global_fit (bool): ``True`` for global fitting mode.
        bundle (CompositeModelBundle | None): Optional composite model bundle for
            v2 local fits. When provided and ``global_fit`` is ``False``, decomposition uses
            ``bundle.decompose()`` instead of the legacy string-split approach.
        component_models: Optional mapping from canonical component ids to
            registry model names for canonical global-fit contribution names.

    Returns:
        pd.DataFrame: Extended dataframe containing the single contributions of the
            models.

    """
    from spectrafit.core.solver_runtime import (  # noqa: PLC0415
        _group_global_contributions_with_models,
    )

    _df = df.copy()

    if not global_fit:
        if bundle is None:
            msg = "CompositeModelBundle required for local decomposition."
            raise RuntimeError(msg)
        for comp_id, curve in bundle.decompose(params, x).items():
            _df[comp_id] = curve
        return _df

    for contribution in _group_global_contributions_with_models(
        params=params,
        component_models=component_models,
    ):
        _df[
            global_contribution_name(
                contribution.contribution_id,
                contribution.dataset_index,
            )
        ] = contribution.evaluate(x)

    return _df


class Constants(BaseModel):
    """Constants used for calculations.

    This class provides mathematical constants used across the package.
    Implemented as a frozen Pydantic model to ensure immutability.
    """

    model_config = ConfigDict(frozen=True)

    ln2: float = log(2.0)
    sq2pi: float = sqrt(2.0 * pi)
    sqpi: float = sqrt(pi)
    sq2: float = sqrt(2.0)
    fwhmg2sig: float = 1 / (2.0 * sqrt(2.0 * log(2.0)))
    fwhml2sig: float = 1 / 2.0
    fwhmv2sig: float = 1 / 3.60131

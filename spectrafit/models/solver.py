"""Solver models for curve fitting.

This module contains the SolverModels class and helper functions for solving
fitting problems using lmfit.
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from math import log
from math import pi
from math import sqrt
from typing import TYPE_CHECKING
from typing import ClassVar
from typing import cast

import numpy as np

from spectrafit.models.naming import GlobalLmfitContributionKey
from spectrafit.models.naming import global_contribution_name
from spectrafit.models.parameter_builder import ReferenceKeys
from spectrafit.models.registry import REGISTRY


if TYPE_CHECKING:
    import pandas as pd

    from lmfit import Parameter
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


@dataclass(slots=True)
class _GlobalContribution:
    """Grouped global contribution parameters for one dataset/component curve."""

    contribution_id: str
    dataset_index: int
    registry_model: str
    parameter_values: dict[str, Parameter] = field(default_factory=dict)

    def add_parameter(
        self, parameter_key: GlobalLmfitContributionKey, value: Parameter
    ) -> None:
        """Add a parsed lmfit parameter to this contribution."""
        self.parameter_values[parameter_key.field_name] = value

    @property
    def column_name(self) -> str:
        """Return the output column name for this contribution."""
        return global_contribution_name(self.contribution_id, self.dataset_index)

    @property
    def dataset_offset(self) -> int:
        """Return the zero-based dataset offset."""
        return self.dataset_index - 1

    def evaluate(
        self,
        x: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Evaluate the contribution curve for one dataset."""
        ReferenceKeys().model_check(model=self.registry_model)
        return np.asarray(
            REGISTRY.get(self.registry_model).function(x, **self.parameter_values),
            dtype=np.float64,
        )


def _group_global_contributions(params: Parameters) -> list[_GlobalContribution]:
    """Group global lmfit parameters into typed per-dataset contributions."""
    return _group_global_contributions_with_models(params=params)


def _group_global_contributions_with_models(
    params: Parameters,
    component_models: dict[str, str] | None = None,
) -> list[_GlobalContribution]:
    """Group global lmfit parameters into typed per-dataset contributions."""
    grouped: dict[str, _GlobalContribution] = {}

    for parameter_name, value in params.items():
        contribution_key = GlobalLmfitContributionKey.parse(parameter_name)
        registry_model = contribution_key.registry_model
        if component_models is not None:
            registry_model = component_models.get(
                contribution_key.contribution_id,
                registry_model,
            )
        contribution = grouped.setdefault(
            contribution_key.contribution_name,
            _GlobalContribution(
                contribution_id=contribution_key.contribution_id,
                dataset_index=contribution_key.dataset_index,
                registry_model=registry_model,
            ),
        )
        contribution.add_parameter(contribution_key, value)

    return list(grouped.values())


class SolverModels:
    """Solver residual helpers plus a compatibility runtime shim.

    Runtime orchestration now lives in :mod:`spectrafit.core.solver_runtime`
    per ADR-004. This class remains as the canonical home for residual helpers
    and as a thin compatibility wrapper for direct ``SolverModels(...)`` usage.
    """

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Create a compatibility wrapper around the core solver runtime."""
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
        """Compute residual for local (single-dataset) fitting using the composite bundle.

        Args:
            params (Parameters): Current parameter values from the minimizer.
            x (NDArray[np.float64]): x-values of the data.
            data (NDArray[np.float64]): y-values of the data as 1d-array.
            bundle (CompositeModelBundle): Prepared local-fit composite bundle.

        Returns:
            NDArray[np.float64]: Residual (model - data).

        """
        return np.array(
            bundle.composite.eval(params, x=x) - data,
            dtype=np.float64,
        )

    @staticmethod
    def solve_global_fitting(
        params: Parameters,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
        config: GlobalFittingConfig | None = None,
        component_models: dict[str, str] | None = None,
    ) -> NDArray[np.float64]:
        r"""Solving the fitting for global problem.

        !!! note "About implemented models"
            `solve_global_fitting` is the global solution of `solve_local_fitting` a
            wrapper function for the calling the implemented moldels. For the kind of
            supported models see `solve_local_fitting`.

        !!! note "About the global solution"
            The global solution is a solution for the problem, where the `x`-values is
            the energy, but the y-values are the intensities, which has to be fitted as
            one unit. For this reason, the residual is calculated as the difference
            between all the y-values and the global proposed solution. Later the
            residual has to be flattened to a 1-dimensional array and minimized by the
            `lmfit`-optimizer.


        Args:
            params (Parameters): The best optimized parameters of the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 2D-array.
            config (GlobalFittingConfig | None): Optional global fitting
                configuration with per-dataset weights.
            component_models: Optional mapping from canonical component ids
                (e.g. ``"p1"``) to registry model names (e.g. ``"gaussian"``)
                for canonical global-fit parameter names.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.

        """
        val = np.zeros(data.shape)
        for contribution in _group_global_contributions_with_models(
            params=params,
            component_models=component_models,
        ):
            val[:, contribution.dataset_offset] += cast(
                "np.ndarray[tuple[int], np.dtype[np.float64]]",
                contribution.evaluate(x),
            )

        residual = val - data

        if config is not None and config.weights is not None:
            weights_arr = np.array(config.weights, dtype=np.float64)
            residual = residual * weights_arr[np.newaxis, :]

        return residual.flatten()


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
        _df[contribution.column_name] = contribution.evaluate(x)

    return _df


@dataclass(frozen=True)
class Constants:
    """Constants used for calculations.

    This class provides mathematical constants used across the package.
    It's implemented as a frozen dataclass with class variables
    to ensure they can't be modified.
    """

    ln2: ClassVar[float] = log(2.0)
    sq2pi: ClassVar[float] = sqrt(2.0 * pi)
    sqpi: ClassVar[float] = sqrt(pi)
    sq2: ClassVar[float] = sqrt(2.0)
    fwhmg2sig: ClassVar[float] = 1 / (2.0 * sqrt(2.0 * log(2.0)))
    fwhml2sig: ClassVar[float] = 1 / 2.0
    fwhmv2sig: ClassVar[float] = 1 / 3.60131

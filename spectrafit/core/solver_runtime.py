"""Core-owned lmfit solver runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING
from typing import cast

import numpy as np

from lmfit import Minimizer
from lmfit import Parameter
from lmfit import Parameters

from spectrafit.models.naming import GlobalLmfitContributionKey
from spectrafit.models.parameter_builder import ParameterBuilder
from spectrafit.models.parameter_builder import ReferenceKeys
from spectrafit.models.registry import REGISTRY
from spectrafit.models.solver_config import SolverConfig


if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from lmfit.minimizer import MinimizerResult
    from numpy.typing import NDArray

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.models.bundle import CompositeModelBundle
    from spectrafit.models.global_fitting import GlobalFittingConfig


@dataclass(slots=True)
class _GlobalContribution:
    """Grouped global contribution parameters for one dataset/component curve."""

    contribution_id: str
    dataset_index: int
    registry_model: str
    parameter_values: dict[str, Parameter] = field(default_factory=dict)

    def add_parameter(
        self,
        parameter_key: GlobalLmfitContributionKey,
        value: Parameter,
    ) -> None:
        """Add a parsed lmfit parameter to this contribution."""
        self.parameter_values[parameter_key.field_name] = value

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


def solve_local_fitting(
    params: Parameters,
    x: NDArray[np.float64],
    data: NDArray[np.float64],
    bundle: CompositeModelBundle,
) -> NDArray[np.float64]:
    """Compute residual for local fitting using the prepared composite bundle."""
    return np.array(
        bundle.composite.eval(params, x=x) - data,
        dtype=np.float64,
    )


def solve_global_fitting(
    params: Parameters,
    x: NDArray[np.float64],
    data: NDArray[np.float64],
    config: GlobalFittingConfig | None = None,
    component_models: dict[str, str] | None = None,
) -> NDArray[np.float64]:
    """Compute the flattened residual for global fitting across all datasets."""
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


@dataclass(frozen=True, slots=True)
class SolverExecutionPlan:
    """Explicit solver execution plan for one fit run."""

    residual: Callable[..., NDArray]
    params: Parameters
    fcn_args: tuple[object, ...]
    bundle: CompositeModelBundle | None = None


class LmfitSolverRuntime:
    """Own runtime planning and lmfit execution for one fitting run."""

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Initialize runtime collaborators for one solve execution."""
        self.config = config
        self._parameter_builder = ParameterBuilder(df=df, config=config)
        self._solver_config = SolverConfig(
            minimizer=config.minimizer,
            optimizer=config.optimizer,
        )
        self._bundle: CompositeModelBundle | None = None

    @property
    def bundle(self) -> CompositeModelBundle | None:
        """Return the prepared local-fit bundle when available."""
        return self._bundle

    def build_execution_plan(self) -> SolverExecutionPlan:
        """Build an explicit solver execution plan for the current config."""
        prepared = self._parameter_builder.build()
        self._bundle = prepared.bundle

        if self.config.context.is_global:
            return SolverExecutionPlan(
                residual=solve_global_fitting,
                params=prepared.params,
                fcn_args=(
                    self._parameter_builder.x,
                    self._parameter_builder.data,
                    self._parameter_builder.global_fitting_config,
                    prepared.component_models,
                ),
                bundle=prepared.bundle,
            )

        if prepared.bundle is None:
            msg = "CompositeModelBundle not initialized for local solving"
            raise RuntimeError(msg)
        return SolverExecutionPlan(
            residual=solve_local_fitting,
            params=prepared.params,
            fcn_args=(
                self._parameter_builder.x,
                self._parameter_builder.data,
                prepared.bundle,
            ),
            bundle=prepared.bundle,
        )

    def solve(self) -> tuple[Minimizer, MinimizerResult]:
        """Execute the solver execution plan via lmfit."""
        plan = self.build_execution_plan()
        minimizer = Minimizer(
            plan.residual,
            params=plan.params,
            fcn_args=plan.fcn_args,
            **self._solver_config.minimizer_kwargs(),
        )
        result = minimizer.minimize(**self._solver_config.optimizer_kwargs())
        return minimizer, result

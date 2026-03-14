"""Core-owned lmfit solver runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from lmfit import Minimizer
from lmfit import Parameters

from spectrafit.models.parameter_builder import ParameterBuilder
from spectrafit.models.solver import SolverModels
from spectrafit.models.solver_config import SolverConfig


if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from lmfit.minimizer import MinimizerResult
    from numpy.typing import NDArray

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.models.bundle import CompositeModelBundle


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
                residual=SolverModels.solve_global_fitting,
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
            residual=SolverModels.solve_local_fitting,
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

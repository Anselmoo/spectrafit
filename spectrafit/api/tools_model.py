"""Backward-compatible tool boundary models built on canonical config ownership.

Canonical definitions for solver, fitting-context, and preprocessing state live in
``spectrafit.models``. This module keeps historical API/notebook imports working by
projecting those canonical models to compatibility DTOs instead of re-declaring
runtime ownership here.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.models.column_names import ColumnNames as ColumnNamesAPI
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.fitting_context import coerce_legacy_fitting_mode
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig
from spectrafit.models.solver_config import SolverConfig


class DataPreProcessingAPI(PreprocessingConfig):
    """Compatibility preprocessing DTO layered on canonical config ownership."""

    column: list[int | str] = Field(
        min_length=1,
        default_factory=lambda: [0, 1],
        description="Column of the data.",
    )

    def to_preprocessing_config(self) -> PreprocessingConfig:
        """Project the compatibility DTO onto the canonical preprocessing model."""
        return PreprocessingConfig.model_validate(
            self.model_dump(mode="python", exclude={"column"})
        )

    @classmethod
    def from_preprocessing_config(
        cls,
        preprocessing: PreprocessingConfig | None,
        *,
        column: list[int | str],
    ) -> DataPreProcessingAPI:
        """Project canonical preprocessing ownership onto the DTO boundary."""
        canonical = (
            preprocessing if preprocessing is not None else PreprocessingConfig()
        )
        return cls(
            **canonical.model_dump(mode="python"),
            column=list(column),
        )


class GlobalFittingAPI(BaseModel):
    """Definition of the global fitting routine."""

    model_config = ConfigDict(extra="forbid")

    global_: FittingMode = Field(
        default=FittingMode.STANDARD,
        description="Global fitting mode.",
    )

    @field_validator("global_", mode="before")
    @classmethod
    def _coerce_global_mode(cls, v: object) -> str:
        """Accept legacy bool/int values for backward compatibility."""
        return coerce_legacy_fitting_mode(v).value

    def to_fitting_context(self, *, n_datasets: int | None = None) -> FittingContext:
        """Resolve the compatibility mode flag to the canonical fitting context."""
        resolved_n_datasets = (
            n_datasets
            if n_datasets is not None
            else (1 if self.global_ == FittingMode.STANDARD else 2)
        )
        return FittingContext(mode=self.global_, n_datasets=resolved_n_datasets)

    @classmethod
    def from_fitting_context(cls, context: FittingContext) -> GlobalFittingAPI:
        """Project canonical fitting-context ownership onto the mode DTO."""
        return cls(global_=context.mode)


class SolverModelsAPI(SolverConfig):
    """Compatibility solver DTO layered on canonical solver ownership."""

    def to_solver_config(self) -> SolverConfig:
        """Convert API-facing solver settings into the canonical core model."""
        return SolverConfig(
            minimizer=self.minimizer,
            optimizer=self.optimizer,
        )

    @classmethod
    def from_solver_config(cls, config: SolverConfig) -> SolverModelsAPI:
        """Build the boundary DTO from canonical solver settings."""
        return cls(**config.model_dump(mode="python"))


class GeneralSolverModelsAPI(SolverModelsAPI):
    """Compatibility DTO that couples solver settings to legacy fitting mode."""

    global_: FittingMode = GlobalFittingAPI().global_

    @field_validator("global_", mode="before")
    @classmethod
    def _coerce_global_mode(cls, v: object) -> str:
        """Accept legacy bool/int global flags."""
        return coerce_legacy_fitting_mode(v).value

    def to_fitting_context(self, *, n_datasets: int | None = None) -> FittingContext:
        """Resolve the legacy fitting-mode flag to canonical fitting context."""
        return GlobalFittingAPI(global_=self.global_).to_fitting_context(
            n_datasets=n_datasets
        )

    @classmethod
    def from_solver_context(
        cls,
        *,
        solver_config: SolverConfig,
        fitting_context: FittingContext,
    ) -> GeneralSolverModelsAPI:
        """Project canonical solver/context ownership onto the compatibility DTO."""
        return cls(
            global_=fitting_context.mode,
            **solver_config.model_dump(mode="python"),
        )


__all__ = [
    "ColumnNamesAPI",
    "DataPreProcessingAPI",
    "GeneralSolverModelsAPI",
    "GlobalFittingAPI",
    "MinimizerConfig",
    "OptimizerConfig",
    "SolverModelsAPI",
]

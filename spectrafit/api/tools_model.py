"""Backward-compatible re-exports for API tools models.

Canonical definitions for :class:`MinimizerConfig` and :class:`OptimizerConfig`
have moved to :mod:`spectrafit.models.solver_config`.  These aliases keep the frozen
notebook plugin working without modification.

:class:`ColumnNamesAPI` is aliased from :mod:`spectrafit.models.column_names`.
:class:`DataPreProcessingAPI` keeps its original definition here (it has a ``column``
field that :class:`~spectrafit.models.preprocessing_config.PreprocessingConfig` does
not expose).
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.models.column_names import ColumnNames as ColumnNamesAPI
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig


class DataPreProcessingAPI(BaseModel):
    """Definition of the data preprocessing command line argument."""

    model_config = ConfigDict(extra="forbid")

    oversampling: bool = Field(
        default=False,
        description="Oversampling the spectra by using factor of 5; default to False.",
    )
    energy_start: float | None = Field(
        default=None,
        description="Start energy of the spectra; default to None.",
    )
    energy_stop: float | None = Field(
        default=None,
        description="Stop energy of the spectra; default to None.",
    )
    smooth: int = Field(
        default=0,
        ge=0,
        description="Smoothing level of the spectra; default to 0.",
    )
    shift: float = Field(
        default=0,
        description="Shift the energy axis; default to 0.",
    )
    column: list[int | str] = Field(
        min_length=1,
        default=[0, 1],
        description="Column of the data.",
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
        if isinstance(v, bool):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        if isinstance(v, int):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        return str(v)


class SolverModelsAPI(BaseModel):
    """Definition of the solver of SpectraFit."""

    model_config = ConfigDict(extra="forbid")

    minimizer: MinimizerConfig = Field(
        default_factory=MinimizerConfig,
        description="Minimizer options",
    )
    optimizer: OptimizerConfig = Field(
        default_factory=OptimizerConfig,
        description="Optimizer options",
    )


class GeneralSolverModelsAPI(BaseModel):
    """Definition of the general solver of SpectraFit."""

    model_config = ConfigDict(extra="forbid")

    global_: FittingMode = GlobalFittingAPI().global_
    minimizer: MinimizerConfig = Field(default_factory=MinimizerConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)

    @field_validator("global_", mode="before")
    @classmethod
    def _coerce_global_mode(cls, v: object) -> str:
        """Accept legacy bool/int global flags."""
        if isinstance(v, bool):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        if isinstance(v, int):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        return str(v)


__all__ = [
    "ColumnNamesAPI",
    "DataPreProcessingAPI",
    "GeneralSolverModelsAPI",
    "GlobalFittingAPI",
    "MinimizerConfig",
    "OptimizerConfig",
    "SolverModelsAPI",
]

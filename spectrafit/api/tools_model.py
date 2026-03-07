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
from pydantic import Field

from spectrafit.models.column_names import ColumnNames as ColumnNamesAPI
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig


class DataPreProcessingAPI(BaseModel):
    """Definition of the data preprocessing command line argument."""

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

    global_: int = Field(default=0, ge=0, le=2, description="Global fitting routine.")


class SolverModelsAPI(BaseModel):
    """Definition of the solver of SpectraFit."""

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

    global_: int = GlobalFittingAPI().global_
    minimizer: MinimizerConfig = Field(default_factory=MinimizerConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)


__all__ = [
    "ColumnNamesAPI",
    "DataPreProcessingAPI",
    "GeneralSolverModelsAPI",
    "GlobalFittingAPI",
    "MinimizerConfig",
    "OptimizerConfig",
    "SolverModelsAPI",
]

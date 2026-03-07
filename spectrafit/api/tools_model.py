"""Reference model for the API of the SpectraFit tools."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


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


class MinimizerConfig(BaseModel):
    """Configuration for the lmfit minimizer.

    Attributes:
        nan_policy: Policy for handling NaN values during fitting.
        calc_covar: Whether to calculate the covariance matrix.
    """

    model_config = ConfigDict(extra="allow")

    nan_policy: str = Field(
        default="propagate",
        description="Policy for handling NaN values (propagate, raise, omit)",
    )
    calc_covar: bool = Field(
        default=True,
        description="Whether to calculate the covariance matrix",
    )


class OptimizerConfig(BaseModel):
    """Configuration for the lmfit optimizer.

    Attributes:
        max_nfev: Maximum number of function evaluations.
        method: Optimization method (e.g., leastsq, least_squares, nelder).
    """

    model_config = ConfigDict(extra="allow")

    max_nfev: int | None = Field(
        default=None,
        description="Maximum number of function evaluations",
    )
    method: str = Field(
        default="leastsq",
        description="Optimization method",
    )


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
    """Definition of the general solver of SpectraFit.

    !!! note "GeneralSolver"

        The General Solver combines the settings for `lmfit` by adding the global
        fitting settings.
    """

    global_: int = GlobalFittingAPI().global_
    minimizer: MinimizerConfig = Field(default_factory=MinimizerConfig)
    optimizer: OptimizerConfig = Field(default_factory=OptimizerConfig)


class ColumnNamesAPI(BaseModel):
    """Definition of the column names of the exported model."""

    energy: str = "energy"
    intensity: str = "intensity"
    residual: str = "residual"
    fit: str = "fit"

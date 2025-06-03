"""Reference model for the API of the SpectraFit tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class AutopeakAPI(BaseModel):
    """Definition of the auto detection of peak command line argument.

    The auto detection of peaks is performed by the SpectraFit tools. Here is listed the
    set of parameters that are used to control the auto detection of peaks according to
    the following `scipy.signal.find_peaks` -module; source:
    [https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html](
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
    )
    """

    modeltype: str | None = None
    height: list[float] | None = None
    threshold: list[float] | None = None
    distance: int | None = None
    prominence: list[float] | None = None
    width: list[float] | None = None
    wlen: int | None = None
    rel_height: float | None = None
    plateau_size: float | None = None
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


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

    minimizer: dict[str, Any] = Field(
        default={"nan_policy": "propagate", "calc_covar": True},
        description="Minimizer options",
    )
    optimizer: dict[str, Any] = Field(
        default={"max_nfev": None, "method": "leastsq"},
        description="Optimzer options",
    )


class GeneralSolverModelsAPI(BaseModel):
    """Definition of the general solver of SpectraFit.

    !!! note "GeneralSolver"

        The General Solver combines the settings for `lmfit` by adding the global
        fitting settings.
    """

    global_: int = GlobalFittingAPI().global_
    minimizer: dict[str, Any] = SolverModelsAPI().minimizer
    optimizer: dict[str, Any] = SolverModelsAPI().optimizer


class ColumnNamesAPI(BaseModel):
    """Definition of the column names of the exported model."""

    energy: str = "energy"
    intensity: str = "intensity"
    residual: str = "residual"
    fit: str = "fit"

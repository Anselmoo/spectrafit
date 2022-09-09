"""Reference model for the API of the SpectraFit tools."""
from __future__ import annotations
from __future__ import print_function

from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field


class DataPreProcessing(BaseModel):
    """Model for the data preprocessing command line argument."""

    oversampling: bool = Field(
        default=False,
        description="Oversampling the spectra by using factor of 5; default to False.",
    )
    energy_start: Optional[Union[int, float]] = Field(
        default=None,
        dtypes=[int, float],
        description="Start energy of the spectra; default to None.",
    )
    energy_stop: Optional[Union[int, float]] = Field(
        default=None,
        dtypes=[int, float],
        description="Stop energy of the spectra; default to None.",
    )
    smooth: int = Field(
        default=0,
        ge=0,
        dtypes=int,
        description="Smoothing level of the spectra; default to 0.",
    )
    shift: Union[int, float] = Field(
        default=0,
        dtypes=[int, float],
        description="Shift the energy axis; default to 0.",
    )


class GlobalFitting(BaseModel):
    """Model for the global fitting routine."""

    global_: int = Field(default=0, ge=0, le=2, alias="global")


class SolverModels(BaseModel):
    """Model for the solver command line argument."""

    minimizer: Dict[str, Any] = Field(
        default={"nan_policy": "propagate", "calc_covar": True},
        description="Minimizer options",
    )
    optimizer: Dict[str, Any] = Field(
        default={"max_nfev": 1000, "method": "leastsq"},
        description="Optimzer options",
    )


class GeneralSolverModels(BaseModel):
    """Model for the general solver command line argument.

    !!! note "GeneralSolver"

        The General Solver combines the settings for `lmfit` by adding the global
        fitting settings.
    """

    global_: int = GlobalFitting().global_
    minimizer: Dict[str, Any] = SolverModels().minimizer
    optimizer: Dict[str, Any] = SolverModels().optimizer

"""Reference model for the API of the SpectraFit tools."""
from __future__ import annotations
from __future__ import print_function

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Extra
from pydantic import Field


class Autopeak(BaseModel):
    """Model for the auto detection of peak command line argument.

    The auto detection of peaks is performed by the SpectraFit tools. Here is listed the
    set of parameters that are used to control the auto detection of peaks according to
    the following `scipy.signal.find_peaks` -module; source:
    [https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html](
    https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
    )
    """

    model_type: Optional[str] = None
    height: Optional[List[float]] = None
    threshold: Optional[List[float]] = None
    distance: Optional[int] = None
    prominence: Optional[List[float]] = None
    width: Optional[List[float]] = None
    wlen: Optional[int] = None
    rel_height: Optional[float] = None
    plateau_size: Optional[float] = None

    class Config:
        """Activate the Validation Error Raise."""

        extra = Extra.forbid
        validate_assignment = True


class DataPreProcessing(BaseModel):
    """Model for the data preprocessing command line argument."""

    oversampling: bool = Field(
        default=False,
        description="Oversampling the spectra by using factor of 5; default to False.",
    )
    energy_start: Optional[float] = Field(
        default=None,
        dtypes=float,
        description="Start energy of the spectra; default to None.",
    )
    energy_stop: Optional[float] = Field(
        default=None,
        dtypes=float,
        description="Stop energy of the spectra; default to None.",
    )
    smooth: int = Field(
        default=0,
        ge=0,
        dtypes=int,
        description="Smoothing level of the spectra; default to 0.",
    )
    shift: float = Field(
        default=0,
        dtypes=float,
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

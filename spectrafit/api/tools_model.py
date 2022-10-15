"""Reference model for the API of the SpectraFit tools."""


from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Extra
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


class DataPreProcessingAPI(BaseModel):
    """Definition of the data preprocessing command line argument."""

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
    column: List[Union[int, str]] = Field(
        min_items=1,
        default=[0, 1],
        dtypes=[int, str],
        description="Column of the data.",
    )


class GlobalFittingAPI(BaseModel):
    """Definition of the global fitting routine."""

    global_: int = Field(default=0, ge=0, le=2, description="Global fitting routine.")


class SolverModelsAPI(BaseModel):
    """Definition of the solver of SpectraFit."""

    minimizer: Dict[str, Any] = Field(
        default={"nan_policy": "propagate", "calc_covar": True},
        description="Minimizer options",
    )
    optimizer: Dict[str, Any] = Field(
        default={"max_nfev": 1000, "method": "leastsq"},
        description="Optimzer options",
    )


class GeneralSolverModelsAPI(BaseModel):
    """Definition of the general solver of SpectraFit.

    !!! note "GeneralSolver"

        The General Solver combines the settings for `lmfit` by adding the global
        fitting settings.
    """

    global_: int = GlobalFittingAPI().global_
    minimizer: Dict[str, Any] = SolverModelsAPI().minimizer
    optimizer: Dict[str, Any] = SolverModelsAPI().optimizer


class ColumnNamesAPI(BaseModel, frozen=True):
    """Definition of the column names of the exported model."""

    energy: str = "energy"
    intensity: str = "intensity"
    residual: str = "residual"
    fit: str = "fit"

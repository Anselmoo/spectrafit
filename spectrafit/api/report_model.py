"""Reference model for the API of the Jupyter Notebook report."""
from typing import Any
from typing import Dict
from typing import Hashable
from typing import List
from typing import Union

from dtale import __version__ as dtale_version
from emcee import __version__ as emcee_version
from itables import __version__ as itables_version
from lmfit import __version__ as lmfit_version
from numdifftools import __version__ as numdifftools_version
from numpy import __version__ as numpy_version
from pandas import __version__ as pandas_version
from plotly import __version__ as plotly_version
from pydantic import BaseModel
from pydantic import Field
from pydantic import __version__ as pydantic_version
from scipy import __version__ as scipy_version
from sklearn import __version__ as sklearn_version
from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from statsmodels import __version__ as statsmodels_version


class CreditsAPI(BaseModel, frozen=True):
    """Credits API model."""

    dtale: str = f"dtale v{dtale_version}"
    emcee: str = f"emcee v{emcee_version}"
    itables: str = f"itables v{itables_version}"
    lmfit: str = f"lmfit v{lmfit_version}"
    numdifftools: str = f"numdifftools v{numdifftools_version}"
    numpy: str = f"numpy v{numpy_version}"
    pandas: str = f"pandas v{pandas_version}"
    plotly: str = f"plotly v{plotly_version}"
    pydantic: str = f"pydantic v{pydantic_version}"
    scipy: str = f"scipy v{scipy_version}"
    sklearn: str = f"sklearn v{sklearn_version}"
    statsmodels: str = f"statsmodels v{statsmodels_version}"


class FitMethodAPI(BaseModel):
    """Fit method API model."""

    global_fitting: Union[bool, int] = Field(
        default=False,
        description="Fitting in the global fashion",
    )
    confidence_interval: Dict[str, Any] = Field(
        ...,
        description="Settings for the confidence interval calculation",
    )
    configurations: Dict[str, Any] = Field(
        ..., description="Settings for the fitting configuration"
    )


class InputAPI(BaseModel):
    """Input API for the report endpoint."""

    description: DescriptionAPI = DescriptionAPI()
    credits: CreditsAPI = CreditsAPI()
    initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]] = Field(
        ..., description="Initial model for the fit"
    )
    method: FitMethodAPI = Field(
        ..., description="Fitting method with optional including of confidence interval"
    )
    pre_processing: DataPreProcessingAPI = Field(..., description="Data pre-processing")


class SolverAPI(BaseModel):
    """Solver API for the report endpoint."""

    goodness_of_fit: Dict[str, float] = Field(..., description="Goodness of fit")
    regression_metrics: Dict[str, List[Any]] = Field(
        ..., description="Regression metrics"
    )
    descriptive_statistic: Dict[str, List[Any]] = Field(
        ..., description="Descriptive statistic"
    )
    linear_correlation: Dict[str, List[Any]] = Field(
        ..., description="Linear correlation"
    )
    component_correlation: Dict[str, Dict[str, Any]] = Field(
        default={},
        description="Linear correlation of each attribute of components. if possible",
    )
    confidence_interval: Dict[str, Any] = Field(
        default={}, description="Confidence interval, if possible"
    )
    covariance_matrix: Dict[str, Dict[str, Any]] = Field(
        default={}, description="Covariance matrix, if possible"
    )
    variables: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="Variables with their initial, optimized and optional error values",
    )
    errorbars: Dict[str, Any] = Field(
        default={},
        description="Error bar comment if values reach initial value or boundary",
    )


class OutputAPI(BaseModel):
    """Output API for the report endpoint."""

    df_org: Dict[Hashable, Any] = Field(
        ...,
        description="DataFrame of the original data via 'records' orient",
    )
    df_fit: Dict[Hashable, Any] = Field(
        ...,
        description="DataFrame of the fitted data via 'records' orient",
    )
    df_pre: Dict[Hashable, Any] = Field(
        default={},
        description="DataFrame of the pre-processed data via 'records' orient",
    )

    class Config:
        """Config for the OutputAPI of arbitary types."""

        arbitrary_types_allowed = True


class ReportAPI(BaseModel):
    """Definition of the report model."""

    input: InputAPI = Field(
        ...,
        description="Input data for the report.",
    )
    solver: SolverAPI = Field(
        ...,
        description="Solver data for the report.",
    )
    output: OutputAPI = Field(
        ...,
        description="Output data for the report.",
    )

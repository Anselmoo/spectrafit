"""Reference model for the API of the Jupyter Notebook report."""

from __future__ import annotations

from dtale import __version__ as dtale_version
from emcee import __version__ as emcee_version
from itables import __version__ as itables_version
from lmfit import __version__ as lmfit_version
from numdifftools import __version__ as numdifftools_version
from numpy import __version__ as numpy_version
from pandas import __version__ as pandas_version
from plotly import __version__ as plotly_version
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import __version__ as pydantic_version
from pydantic import field_validator
from scipy import __version__ as scipy_version
from sklearn import __version__ as sklearn_version
from statsmodels import __version__ as statsmodels_version

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.types import DataSplitDict


type DataCell = float | int | str | bool | None
type DataFrameListDict = dict[str, list[DataCell]]


class FitConfigurationsAPI(BaseModel):
    """Solver configuration snapshot used for report generation."""

    model_config = ConfigDict(extra="forbid")

    method: str = ""
    max_nfev: int = 0
    nan_policy: str = "raise"


class CreditsAPI(BaseModel):
    """Credits API model."""

    model_config = ConfigDict(extra="forbid")

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

    model_config = ConfigDict(extra="forbid")

    global_fitting: FittingMode = Field(
        default=FittingMode.STANDARD,
        description="Fitting in the global fashion",
    )
    confidence_interval: bool | ConfIntervalAPI = Field(
        ...,
        description="Settings for the confidence interval calculation",
    )
    configurations: FitConfigurationsAPI = Field(
        ...,
        description="Settings for the fitting configuration",
    )
    settings_solver_models: SolverModelsAPI = Field(
        ...,
        description="Settings for the solver models including minimizer and optimizer",
    )

    @field_validator("global_fitting", mode="before")
    @classmethod
    def _coerce_global_mode(cls, v: object) -> str:
        """Accept legacy bool/int fitting mode values."""
        if isinstance(v, bool):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        if isinstance(v, int):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        return str(v)


class ParameterSpec(BaseModel):
    """Specification for a single fit parameter.

    Attributes:
        max: Upper bound for the parameter.
        min: Lower bound for the parameter.
        vary: Whether the parameter is varied during fitting.
        value: Initial value of the parameter.
        expr: Lmfit expression for explicit parameter dependencies.
    """

    model_config = ConfigDict(extra="forbid")

    max: float | None = Field(default=None, description="Upper bound for the parameter")
    min: float | None = Field(default=None, description="Lower bound for the parameter")
    vary: bool = Field(default=True, description="Whether to vary the parameter")
    value: float | None = Field(default=None, description="Initial parameter value")
    expr: str | None = Field(
        default=None,
        description="Lmfit expression for explicit dependencies",
    )


class InputAPI(BaseModel):
    """Input API for the report endpoint."""

    model_config = ConfigDict(extra="forbid")

    description: DescriptionAPI = DescriptionAPI()
    credits: CreditsAPI = CreditsAPI()
    initial_model: list[dict[str, dict[str, ParameterSpec]]] = Field(
        ...,
        description="Initial model for the fit",
    )
    method: FitMethodAPI = Field(
        ...,
        description="Fitting method with optional including of confidence interval",
    )
    pre_processing: DataPreProcessingAPI = Field(..., description="Data pre-processing")


class VariableResult(BaseModel):
    """Result for a single fitted variable.

    Attributes:
        init_value: Initial value before fitting.
        model_value: Optimized value after fitting.
        best_value: Best value found during fitting.
        stderr: Standard error of the parameter.
    """

    model_config = ConfigDict(extra="forbid")

    init_value: float | None = Field(
        default=None,
        description="Initial value before fitting",
    )
    model_value: float | None = Field(
        default=None,
        description="Optimized value after fitting",
    )
    best_value: float | None = Field(
        default=None,
        description="Best value found during fitting",
    )
    stderr: float | None = Field(
        default=None,
        description="Standard error of the parameter",
    )


class ComputationalInfo(BaseModel):
    """Computational information about the fitting process.

    Attributes:
        nfev: Number of function evaluations.
        ndata: Number of data points.
        nvarys: Number of varied parameters.
        chisqr: Chi-squared statistic.
        redchi: Reduced chi-squared statistic.
        aic: Akaike Information Criterion.
        bic: Bayesian Information Criterion.
    """

    model_config = ConfigDict(extra="forbid")

    nfev: int | None = Field(default=None, description="Number of function evaluations")
    ndata: int | None = Field(default=None, description="Number of data points")
    nvarys: int | None = Field(default=None, description="Number of varied parameters")
    chisqr: float | None = Field(default=None, description="Chi-squared statistic")
    redchi: float | None = Field(
        default=None,
        description="Reduced chi-squared statistic",
    )
    aic: float | None = Field(default=None, description="Akaike Information Criterion")
    bic: float | None = Field(
        default=None,
        description="Bayesian Information Criterion",
    )
    success: bool | None = Field(default=None, description="Whether the fit converged")
    message: str | None = Field(default=None, description="Minimizer status message")
    errorbars: bool | None = Field(
        default=None,
        description="Whether parameter error bars were estimated",
    )
    max_nfev: int | None = Field(
        default=None,
        description="Maximum allowed function evaluations",
    )
    scale_covar: bool | None = Field(
        default=None,
        description="Whether covariance scaling was enabled",
    )
    calc_covar: bool | None = Field(
        default=None,
        description="Whether covariance matrix was calculated",
    )


class SolverAPI(BaseModel):
    """Solver API for the report endpoint."""

    model_config = ConfigDict(
        extra="allow"  # intentional: result container, v2.1 migration target
    )

    goodness_of_fit: dict[str, float] = Field(..., description="Goodness of fit")
    regression_metrics: DataSplitDict = Field(
        ...,
        description="Regression metrics",
    )
    descriptive_statistic: DataSplitDict = Field(
        ...,
        description="Descriptive statistic",
    )
    linear_correlation: DataSplitDict = Field(
        ...,
        description="Linear correlation",
    )
    component_correlation: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Linear correlation of each attribute of components. if possible",
    )
    confidence_interval: dict[str, list[tuple[float, float]]] = Field(
        default_factory=dict,
        description="Confidence interval, if possible",
    )
    covariance_matrix: dict[str, dict[str, float]] = Field(
        default_factory=dict,
        description="Covariance matrix, if possible",
    )
    variables: dict[str, VariableResult] = Field(
        ...,
        description="Variables with their initial, optimized and optional error values",
    )
    errorbars: dict[str, str] = Field(
        default_factory=dict,
        description="Error bar comment if values reach initial value or boundary",
    )
    computational: ComputationalInfo = Field(
        ...,
        description="Computational information like number of function evaluations",
    )


class OutputAPI(BaseModel):
    """Output API for the report endpoint."""

    df_org: DataFrameListDict = Field(
        ...,
        description="DataFrame of the original data via 'records' orient",
    )
    df_fit: DataFrameListDict = Field(
        ...,
        description="DataFrame of the fitted data via 'records' orient",
    )
    df_pre: DataFrameListDict = Field(
        default_factory=dict,
        description="DataFrame of the pre-processed data via 'records' orient",
    )
    model_config = ConfigDict(extra="forbid")


class ReportAPI(BaseModel):
    """Definition of the report model."""

    model_config = ConfigDict(extra="forbid")

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

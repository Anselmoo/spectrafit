"""Typed fitting result container — v2 output model.

Mirrors the `PrototypeOutput` design with
full JSON Schema support via Pydantic v2.  The model is intentionally kept at the
*data* level (plain Python scalars / lists) so that it is serialisable to JSON
without any lmfit dependency at the consumer side.

Examples:
    ```python
    from spectrafit.adapters.fit_result_json import deserialize_fit_result
    from spectrafit.adapters.fit_result_json import save_fit_result

    result = deserialize_fit_result(data)
    save_fit_result(result, Path("output.json"))
    schema = FitResult.model_json_schema()   # stable, MCP-ready
    ```

!!! note
    `FittingResult` (``spectrafit.core.pipeline``) still wraps lmfit objects and
    is used internally by `FittingPipeline`.
    `FitResult` is the *export* representation produced after the fit.
"""

from __future__ import annotations

import math

from collections.abc import Mapping
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.split_frame import SplitFrame


if TYPE_CHECKING:
    from lmfit.minimizer import MinimizerResult


CI_BOUND_PAIR_LENGTH = 2
REPORT_CONFIDENCE_SETTING_KEYS = frozenset(
    {"p_names", "trace", "maxiter", "verbose", "prob_func"}
)

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]
type ReportConfidenceSettingValue = bool | int | str | list[str]
type ReportConfidenceSettings = dict[str, ReportConfidenceSettingValue]


def normalize_confidence_results_payload(
    value: object,
) -> dict[str, list[tuple[float, float]]] | object:
    """Normalize legacy confidence-result payloads to numeric bound pairs."""
    if not isinstance(value, Mapping):
        return value

    normalized: dict[str, list[tuple[float, float]]] = {}
    for parameter_name, raw_bounds in value.items():
        if not isinstance(parameter_name, str) or not isinstance(
            raw_bounds,
            list | tuple,
        ):
            continue

        bounds: list[tuple[float, float]] = []
        for bound in raw_bounds:
            if (
                not isinstance(bound, list | tuple)
                or len(bound) != CI_BOUND_PAIR_LENGTH
            ):
                continue
            sigma, limit = bound
            if not isinstance(sigma, int | float) or not isinstance(
                limit,
                int | float,
            ):
                continue
            bounds.append((float(sigma), float(limit)))

        if bounds:
            normalized[parameter_name] = bounds

    return normalized


def project_confidence_settings_payload(
    settings: ConfIntervalConfig | bool,
) -> bool | ReportConfidenceSettings:
    """Project canonical confidence settings to the legacy report contract."""
    if isinstance(settings, bool):
        return settings

    raw_settings = settings.model_dump(exclude_none=True)
    projected_settings: ReportConfidenceSettings = {
        key: value
        for key, value in raw_settings.items()
        if key in REPORT_CONFIDENCE_SETTING_KEYS
    }
    if (
        "prob_func" in projected_settings
        and projected_settings["prob_func"] is not None
        and not callable(projected_settings["prob_func"])
    ):
        projected_settings.pop("prob_func", None)
    return projected_settings


# ---------------------------------------------------------------------------
# Parameter-level sub-models
# ---------------------------------------------------------------------------


class ParameterResult(BaseModel):
    """Fitted value and uncertainty for a single lmfit parameter.

    Attributes:
        name: lmfit parameter name (e.g. ``"p1_amplitude"``).
        init_value: Initial value before fitting.
        best_value: Best-fit value after minimisation.
        stderr: Standard error (``None`` if not computed or the parameter is fixed).
        vary: Whether the parameter was free during fitting.
        expr: Constraint expression if any.
    """

    name: str
    init_value: float
    best_value: float
    stderr: float | None = None
    vary: bool = True
    expr: str | None = None


class ComponentResult(BaseModel):
    """Per-component evaluated curve.

    Attributes:
        id: Component identifier matching the input ``ComponentSpec.id``.
        model: Model function name.
        curve: Fitted y-values at each x point.
    """

    id: str
    model: str
    curve: list[float]


class FitStatistics(BaseModel):
    """Summary statistics from the lmfit minimisation result.

    Attributes:
        method: Optimisation method used (e.g. ``"leastsq"``).
        nfev: Number of function evaluations.
        ndata: Number of data points.
        nvarys: Number of free parameters.
        nfree: Degrees of freedom (ndata - nvarys).
        chisqr: Chi-squared statistic.
        redchi: Reduced chi-squared (chisqr / nfree).
        aic: Akaike information criterion.
        bic: Bayesian information criterion.
        success: Whether the minimiser reported convergence.
        message: Status message from the minimiser.
    """

    model_config = ConfigDict(extra="forbid")

    method: str = ""
    nfev: int = 0
    ndata: int = 0
    nvarys: int = 0
    nfree: int = 0
    chisqr: float = 0.0
    redchi: float = 0.0
    aic: float = 0.0
    bic: float = 0.0
    success: bool = False
    message: str = ""

    @classmethod
    def from_minimizer_result(cls, result: MinimizerResult) -> FitStatistics:
        """Build canonical fit statistics from an lmfit minimizer result."""
        return cls(
            method=str(getattr(result, "method", "")),
            nfev=int(getattr(result, "nfev", 0) or 0),
            ndata=int(getattr(result, "ndata", 0) or 0),
            nvarys=int(getattr(result, "nvarys", 0) or 0),
            nfree=int(getattr(result, "nfree", 0) or 0),
            chisqr=float(getattr(result, "chisqr", 0.0) or 0.0),
            redchi=float(getattr(result, "redchi", 0.0) or 0.0),
            aic=float(getattr(result, "aic", 0.0) or 0.0),
            bic=float(getattr(result, "bic", 0.0) or 0.0),
            success=bool(getattr(result, "success", False)),
            message=str(getattr(result, "message", "") or ""),
        )


# ---------------------------------------------------------------------------
# FitInsights sub-models (replace fit_insights dict)
# ---------------------------------------------------------------------------


class VariableFitResult(BaseModel):
    """Result for a single fitted variable within `FitInsights`.

    Attributes:
        init_value: Initial parameter value before fitting.
        model_value: Value at the model's nominal point.
        best_value: Best-fit value after minimisation.
        stderr: Standard error of the parameter (``None`` if not estimated).
    """

    model_config = ConfigDict(extra="forbid")

    init_value: float | None = None
    model_value: float | None = None
    best_value: float | None = None
    stderr: float | None = None


class FitConfigurations(BaseModel):
    """Solver configuration snapshot captured at fit time.

    Attributes:
        method: Optimisation method name (e.g. ``"leastsq"``).
        max_nfev: Maximum number of function evaluations allowed.
        nan_policy: How NaN values were handled (``"raise"`` / ``"propagate"``).
    """

    model_config = ConfigDict(extra="forbid")

    method: str = ""
    max_nfev: int = 0
    nan_policy: str = "raise"


class ErrorbarDiagnostics(BaseModel):
    """Structured uncertainty diagnostics derived from lmfit result state.

    Attributes:
        estimated: Whether lmfit reported that errorbars were estimated.
        at_initial_value: Parameter name left at the initial value, if any.
        at_boundary: Parameter name sitting at a hard bound, if any.
        unsupported_method: Method name when the optimizer does not natively
            estimate uncertainties.
    """

    model_config = ConfigDict(extra="forbid")

    estimated: bool | None = None
    at_initial_value: str | None = None
    at_boundary: str | None = None
    unsupported_method: str | None = None

    @staticmethod
    def _isclose(left: float | None, right: float | None) -> bool:
        """Return whether two numeric values are effectively equal."""
        if left is None or right is None:
            return False
        return math.isclose(float(left), float(right))

    @classmethod
    def from_minimizer_result(cls, result: MinimizerResult) -> ErrorbarDiagnostics:
        """Build structured errorbar diagnostics from a minimizer result."""
        diagnostics = cls(estimated=bool(getattr(result, "errorbars", None)))
        if diagnostics.estimated:
            return diagnostics

        method = str(getattr(result, "method", "") or "")
        if method not in ("leastsq", "least_squares"):
            diagnostics.unsupported_method = method

        for name, parameter in result.params.items():
            if not parameter.vary:
                continue
            if diagnostics.at_initial_value is None and cls._isclose(
                parameter.value,
                parameter.init_value,
            ):
                diagnostics.at_initial_value = name
            if diagnostics.at_boundary is None and (
                cls._isclose(parameter.value, parameter.min)
                or cls._isclose(parameter.value, parameter.max)
            ):
                diagnostics.at_boundary = name

        return diagnostics

    def warning_messages(self) -> list[str]:
        """Return compatibility warning messages for uncertainty diagnostics."""
        if self.estimated:
            return []

        warnings: list[str] = ["Uncertainties could not be estimated"]
        if self.unsupported_method:
            warnings.append(
                f"The fitting method '{self.unsupported_method}' does not natively "
                "calculate and uncertainties cannot be estimated due to be out of "
                "region!",
            )
        if self.at_initial_value:
            warnings.append(
                f"The parameter '{self.at_initial_value}' is at its initial value "
                "and uncertainties cannot be estimated!",
            )
        if self.at_boundary:
            warnings.append(
                f"The parameter '{self.at_boundary}' is at its boundary and "
                "uncertainties cannot be estimated!",
            )
        return warnings

    def report_mapping(self) -> dict[str, str]:
        """Project diagnostics to the frozen report compatibility mapping."""
        projected: dict[str, str] = {}
        if self.at_initial_value:
            projected["at_initial_value"] = self.at_initial_value
        if self.at_boundary:
            projected["at_boundary"] = self.at_boundary
        return projected


class ComputationalMeta(BaseModel):
    """Computational metadata extracted from lmfit fitting results.

    Attributes:
        success: Whether the fit converged successfully.
        message: Minimiser status message.
        errorbars: Whether errorbars were estimated.
        nfev: Number of function evaluations.
        max_nfev: Maximum allowed function evaluations.
        scale_covar: Whether covariance matrix was scaled.
        calc_covar: Whether covariance matrix was calculated.
    """

    model_config = ConfigDict(
        extra="allow"  # intentional: result container, v2.1 migration target
    )  # intentional: lmfit result keys vary by method

    success: bool | None = None
    message: str | None = None
    errorbars: bool | None = None
    nfev: int | None = None
    max_nfev: int | None = None
    scale_covar: bool | None = None
    calc_covar: bool | None = None
    diagnostics: ErrorbarDiagnostics = Field(default_factory=ErrorbarDiagnostics)


class InputSnapshot(BaseModel):
    """Reproducibility snapshot of the original input configuration.

    Captures the full original config dict so fits can be reproduced.
    Extra fields are allowed to accommodate any pipeline-specific keys.
    """

    model_config = ConfigDict(extra="allow")  # intentional: reproducibility snapshot


class FitInsights(BaseModel):
    """Structured fit insights — replaces the raw ``fit_insights`` dict.

    Attributes:
        configurations: Solver configuration used during fitting.
        statistics: Goodness-of-fit statistics keyed by metric name.
        variables: Per-parameter variable results.
        errorbars: Error-bar availability message per parameter.
        correlations: Pairwise parameter correlation coefficients.
        covariance_matrix: Full parameter covariance matrix.
        computational: Timing and computational metadata.
    """

    model_config = ConfigDict(extra="forbid")

    configurations: FitConfigurations = Field(default_factory=FitConfigurations)
    statistics: dict[str, float] = Field(default_factory=dict)
    variables: dict[str, VariableFitResult] = Field(default_factory=dict)
    errorbars: dict[str, str] = Field(default_factory=dict)
    correlations: dict[str, dict[str, float]] = Field(default_factory=dict)
    covariance_matrix: dict[str, dict[str, float]] = Field(default_factory=dict)
    computational: ComputationalMeta = Field(default_factory=ComputationalMeta)

    @classmethod
    def from_minimizer_result(
        cls,
        result: MinimizerResult,
        *,
        max_nfev: int | None = None,
        nan_policy: str | None = None,
        scale_covar: bool | None = None,
        calc_covar: bool | None = None,
    ) -> FitInsights:
        """Build `FitInsights` directly from an lmfit `MinimizerResult`.

        Follows the prototype pattern from `extract_parameters`
        and `extract_statistics`: typed Pydantic models
        are built directly from lmfit objects — no intermediate dict roundtrip.

        All parameters (both free and fixed) are included in `variables` to
        match the legacy ``fit_report_as_dict`` behaviour used by
        the pre-v2 export path.

        Args:
            result: The lmfit `MinimizerResult` after fitting.
            max_nfev: Maximum function-evaluation budget resolved from the
                active minimizer settings.
            nan_policy: Effective NaN-handling policy used by the minimizer.
            scale_covar: Whether lmfit scaled the covariance matrix.
            calc_covar: Whether lmfit attempted covariance calculation.

        Returns:
            FitInsights: Fully-typed insights instance.
        """
        variables: dict[str, VariableFitResult] = {
            name: VariableFitResult(
                init_value=(
                    float(param.init_value)
                    if param.init_value is not None
                    else float(param.value)
                ),
                model_value=float(param.value),
                best_value=float(param.value),
                stderr=float(param.stderr) if param.stderr is not None else None,
            )
            for name, param in result.params.items()
            # Include ALL params (free and fixed) to match legacy formatter output
        }
        errorbars: dict[str, str] = {
            name: ("True" if param.stderr is not None else "False")
            for name, param in result.params.items()
        }
        correlations: dict[str, dict[str, float]] = {
            name: {k: float(v) for k, v in (param.correl or {}).items()}
            for name, param in result.params.items()
            if param.correl
        }
        covariance = getattr(result, "covar", None)
        covariance_matrix: dict[str, dict[str, float]] = {}
        if covariance is not None and covariance.shape[0] == len(result.params):
            parameter_names = list(result.params.keys())
            covariance_matrix = {
                name: {
                    other_name: float(covariance[row_index, column_index])
                    for column_index, other_name in enumerate(parameter_names)
                }
                for row_index, name in enumerate(parameter_names)
            }
        statistics: dict[str, float] = {
            "chi_square": float(result.chisqr),
            "reduced_chi_square": float(result.redchi),
            "akaike_information": float(result.aic),
            "bayesian_information": float(result.bic),
        }
        configurations = FitConfigurations(
            method=str(getattr(result, "method", "")),
            max_nfev=max_nfev or 0,
            nan_policy=nan_policy or str(getattr(result, "nan_policy", "raise")),
        )
        diagnostics = ErrorbarDiagnostics.from_minimizer_result(result)
        computational = ComputationalMeta(
            success=bool(getattr(result, "success", None)),
            message=str(getattr(result, "message", "") or "") or None,
            errorbars=bool(getattr(result, "errorbars", None)),
            nfev=int(result.nfev),
            max_nfev=max_nfev,
            scale_covar=scale_covar,
            calc_covar=calc_covar,
            diagnostics=diagnostics,
        )
        return cls(
            configurations=configurations,
            statistics=statistics,
            variables=variables,
            errorbars=errorbars,
            correlations=correlations,
            covariance_matrix=covariance_matrix,
            computational=computational,
        )


# ---------------------------------------------------------------------------
# DataSummary sub-model (replaces top-level regression / descriptive keys)
# ---------------------------------------------------------------------------


class DataSummary(BaseModel):
    """Regression metrics, descriptive stats, and linear correlations.

    All three fields hold validated split-frame models.

    Attributes:
        regression_metrics: Regression metrics for the fit.
        descriptive_statistic: Descriptive statistics for data, fit, and components.
        linear_correlation: Linear correlation between data, fit, and components.
    """

    model_config = ConfigDict(extra="forbid")

    regression_metrics: SplitFrame = Field(default_factory=SplitFrame.empty)
    descriptive_statistic: SplitFrame = Field(default_factory=SplitFrame.empty)
    linear_correlation: SplitFrame = Field(default_factory=SplitFrame.empty)


# ---------------------------------------------------------------------------
# ConfidenceResults sub-model
# ---------------------------------------------------------------------------


class ConfidenceResults(BaseModel):
    """Confidence interval settings and computed results.

    Attributes:
        settings: ``False`` when confidence intervals are disabled, or the
            canonical confidence-interval configuration when enabled.
        results: lmfit confidence interval output:
            ``{param_name: [(sigma, lower_bound), (sigma, upper_bound), ...]}``.
    """

    model_config = ConfigDict(extra="forbid")

    settings: ConfIntervalConfig | bool = False
    results: dict[str, list[tuple[float, float]]] = Field(default_factory=dict)

    @field_validator("settings", mode="before")
    @classmethod
    def _normalize_settings(cls, value: object) -> object:
        """Normalize legacy confidence settings payloads to the canonical model."""
        if value is False:
            return False
        if value is True:
            return ConfIntervalConfig()
        if isinstance(value, ConfIntervalConfig):
            return value
        if isinstance(value, Mapping):
            raw_settings = dict(value)
            if "sigma" in raw_settings and "sigmas" not in raw_settings:
                raw_settings["sigmas"] = raw_settings.pop("sigma")

            prob_func = raw_settings.get("prob_func")
            if prob_func is not None and not isinstance(prob_func, str):
                raw_settings.pop("prob_func", None)

            return ConfIntervalConfig.model_validate(raw_settings)
        return value

    @field_validator("results", mode="before")
    @classmethod
    def _normalize_results(
        cls, value: object
    ) -> dict[str, list[tuple[float, float]]] | object:
        """Normalize legacy confidence result payloads at typed boundaries."""
        return normalize_confidence_results_payload(value)

    def report_settings(self) -> bool | ReportConfidenceSettings:
        """Project confidence settings to the frozen report compatibility shape."""
        return project_confidence_settings_payload(self.settings)

    def report_results(self) -> dict[str, list[tuple[float, float]]]:
        """Project confidence results to the frozen report compatibility shape."""
        if self.settings is False:
            return {}
        return self.results


# ---------------------------------------------------------------------------
# Root FitResult — the complete, authoritative output container
# ---------------------------------------------------------------------------


class FitResult(BaseModel):
    """Full fitting result — JSON Schema-validated export container.

    This is the **single authoritative output** of the fitting pipeline.
    All consumers (CLI export, Jupyter display, MCP, HTTP API) receive a
    ``FitResult`` — no raw ``FittingArgs`` dicts cross module boundaries.

    Suitable for serialisation to ``output.json``, HTTP response payloads,
    or MCP tool return values.  All fields are plain Python scalars / lists
    with no lmfit objects, making the model fully portable.

    Attributes:
        input_snapshot: Original input configuration dict (for reproducibility).
        statistics: Summary statistics of the minimisation.
        parameters: Per-parameter fitted results.
        components: Per-component evaluated curves.
        x: x-axis values used in the fit.
        y_data: Observed y-values.
        y_fit: Total fitted y-values (sum of all component curves).
        global_fitting: Global fitting mode flag (``False`` = single spectrum).
        fit_insights: Structured fit insights (replaces raw ``fit_insights`` dict).
        data_summary: Regression and descriptive statistics.
        confidence: Confidence interval settings and results.
    """

    model_config = ConfigDict(extra="forbid")

    input_snapshot: InputSnapshot = Field(
        default_factory=InputSnapshot,
        description="Original input configuration for reproducibility",
    )
    statistics: FitStatistics = Field(
        default_factory=FitStatistics,
        description="Minimisation statistics",
    )
    parameters: list[ParameterResult] = Field(
        default_factory=list,
        description="Per-parameter fitted results",
    )
    components: list[ComponentResult] = Field(
        default_factory=list,
        description="Per-component evaluated curves",
    )
    x: list[float] = Field(default_factory=list, description="x-axis values")
    y_data: list[float] = Field(default_factory=list, description="Observed y-values")
    y_fit: list[float] = Field(
        default_factory=list,
        description="Total fitted y (sum of components)",
    )
    global_fitting: FittingMode = Field(
        default=FittingMode.STANDARD,
        description="Fitting mode (STANDARD = single spectrum, GLOBAL = multi-spectrum)",
    )
    fit_insights: FitInsights = Field(
        default_factory=FitInsights,
        description="Structured fit insights (variables, errorbars, correlations, etc.)",
    )
    data_summary: DataSummary = Field(
        default_factory=DataSummary,
        description="Regression metrics and descriptive statistics",
    )
    confidence: ConfidenceResults = Field(
        default_factory=ConfidenceResults,
        description="Confidence interval settings and computed results",
    )

"""Typed fitting result container — v2 output model.

Mirrors the :class:`~prototype.input_output_interface.PrototypeOutput` design with
full JSON Schema support via Pydantic v2.  The model is intentionally kept at the
*data* level (plain Python scalars / lists) so that it is serialisable to JSON
without any lmfit dependency at the consumer side.

Usage::

    result = FitResult.from_dict(data)
    result.save(Path("output.json"))
    schema = FitResult.model_json_schema()   # stable, MCP-ready

.. note::
    ``FittingResult`` (``spectrafit.core.pipeline``) still wraps lmfit objects and
    is used internally by :class:`~spectrafit.core.pipeline.FittingPipeline`.
    ``FitResult`` is the *export* representation produced after the fit.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.types import DataSplitDict


if TYPE_CHECKING:
    from lmfit.minimizer import MinimizerResult


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


# ---------------------------------------------------------------------------
# FitInsights sub-models (replace fit_insights dict)
# ---------------------------------------------------------------------------


class VariableFitResult(BaseModel):
    """Result for a single fitted variable within :class:`FitInsights`.

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
        extra="allow"
    )  # intentional: lmfit result keys vary by method

    success: bool | None = None
    message: str | None = None
    errorbars: bool | None = None
    nfev: int | None = None
    max_nfev: int | None = None
    scale_covar: bool | None = None
    calc_covar: bool | None = None


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
    def from_minimizer_result(cls, result: MinimizerResult) -> FitInsights:
        """Build :class:`FitInsights` directly from an lmfit :class:`MinimizerResult`.

        Follows the prototype pattern from :func:`prototype.core_fitting.extract_parameters`
        and :func:`prototype.core_fitting.extract_statistics`: typed Pydantic models
        are built directly from lmfit objects — no intermediate dict roundtrip.

        Args:
            result: The lmfit :class:`~lmfit.minimizer.MinimizerResult` after fitting.

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
            if param.vary
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
        statistics: dict[str, float] = {
            "chi_square": float(result.chisqr),
            "reduced_chi_square": float(result.redchi),
            "akaike_information": float(result.aic),
            "bayesian_information": float(result.bic),
        }
        configurations = FitConfigurations(
            method=str(getattr(result, "method", "")),
            max_nfev=int(result.nfev),
            nan_policy=str(getattr(result, "nan_policy", "raise")),
        )
        return cls(
            configurations=configurations,
            statistics=statistics,
            variables=variables,
            errorbars=errorbars,
            correlations=correlations,
        )


# ---------------------------------------------------------------------------
# DataSummary sub-model (replaces top-level regression / descriptive keys)
# ---------------------------------------------------------------------------


class DataSummary(BaseModel):
    """Regression metrics, descriptive stats, and linear correlations.

    All three fields hold the ``DataFrame.to_dict(orient='split')`` output:
    ``{"columns": [...], "index": [...], "data": [[...], ...]}``.

    Attributes:
        regression_metrics: Regression metrics for the fit.
        descriptive_statistic: Descriptive statistics for data, fit, and components.
        linear_correlation: Linear correlation between data, fit, and components.
    """

    model_config = ConfigDict(extra="forbid")

    regression_metrics: DataSplitDict = Field(
        default_factory=lambda: DataSplitDict(data=[], index=[], columns=[])
    )
    descriptive_statistic: DataSplitDict = Field(
        default_factory=lambda: DataSplitDict(data=[], index=[], columns=[])
    )
    linear_correlation: DataSplitDict = Field(
        default_factory=lambda: DataSplitDict(data=[], index=[], columns=[])
    )


# ---------------------------------------------------------------------------
# ConfidenceResults sub-model
# ---------------------------------------------------------------------------


class ConfidenceResults(BaseModel):
    """Confidence interval settings and computed results.

    Attributes:
        settings: ``False`` when confidence intervals are disabled, or a
            ``dict`` of ``conf_interval`` kwargs when enabled.
        results: lmfit confidence interval output:
            ``{param_name: [(sigma, lower_bound), (sigma, upper_bound), ...]}``.
    """

    model_config = ConfigDict(extra="forbid")

    settings: dict[str, object] | bool = False
    results: dict[str, list[tuple[float, float]]] = Field(default_factory=dict)


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

    def save(self, path: Path | str) -> None:
        """Serialise the result to a JSON file.

        Args:
            path: Destination path (e.g. ``"output.json"``).
        """
        Path(path).write_text(
            json.dumps(self.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

    @field_validator("global_fitting", mode="before")
    @classmethod
    def _coerce_global_fitting(cls, v: object) -> str:
        """Accept legacy ``int``/``bool`` values and coerce to ``FittingMode``.

        Args:
            v: Raw input value (``FittingMode``, ``str``, ``int``, or ``bool``).

        Returns:
            str: ``FittingMode`` member value string.
        """
        if isinstance(v, (int, bool)):
            return FittingMode.GLOBAL.value if v else FittingMode.STANDARD.value
        return str(v)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> FitResult:
        """Deserialise a ``FitResult`` from a plain dict or JSON file content.

        Args:
            data: Dict matching the ``FitResult`` JSON schema.

        Returns:
            FitResult: Validated instance.
        """
        return cls.model_validate(data)

    @classmethod
    def load(cls, path: Path | str) -> FitResult:
        """Load a ``FitResult`` from a JSON file written by :meth:`save`.

        Args:
            path: Path to the JSON file.

        Returns:
            FitResult: Validated instance.
        """
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.model_validate(raw)

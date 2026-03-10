"""Pydantic models for deserialising SpectraFit _summary.json output.

These models replace ``cast()``-heavy dict access throughout the CLI report
command, providing typed, validated access to every field produced by the
fitting pipeline.
"""

from __future__ import annotations

import json

from pathlib import Path

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class FitStatisticsReport(BaseModel):
    """Goodness-of-fit statistics from lmfit.

    Attributes:
        chi_square: Weighted sum of squared residuals (χ²).
        reduced_chi_square: χ² divided by degrees of freedom.
        akaike_information: Akaike information criterion.
        bayesian_information: Bayesian information criterion.
    """

    model_config = ConfigDict(extra="forbid")

    chi_square: float | None = Field(default=None, description="Chi-square statistic")
    reduced_chi_square: float | None = Field(
        default=None, description="Reduced chi-square"
    )
    akaike_information: float | None = Field(default=None, description="AIC")
    bayesian_information: float | None = Field(default=None, description="BIC")


class FitVariableReport(BaseModel):
    """Per-parameter fit result.

    Attributes:
        init_value: Value at start of fit.
        model_value: Current model value.
        best_value: Best-fit value.
        stderr: Standard error of the parameter (if errorbars were estimated).
    """

    model_config = ConfigDict(extra="forbid")

    init_value: float | None = None
    model_value: float | None = None
    best_value: float | None = None
    stderr: float | None = None


class FitConfigurationsReport(BaseModel):
    """Serialized fit configuration metadata from lmfit."""

    model_config = ConfigDict(extra="forbid")

    fitting_method: str | None = None
    function_evals: int | None = None
    data_points: int | None = None
    variable_names: list[str] = Field(default_factory=list)
    variable_numbers: int | None = None
    degree_of_freedom: int | None = None


class ComputationalReport(BaseModel):
    """Computational metadata attached to fit insights."""

    model_config = ConfigDict(extra="forbid")

    success: bool | None = None
    message: str | None = None
    errorbars: bool | None = None
    nfev: int | None = None
    max_nfev: int | None = None
    scale_covar: bool | None = None
    calc_covar: bool | None = None


class FitInsightsReport(BaseModel):
    """Container for all per-fit diagnostic data.

    Attributes:
        statistics: Goodness-of-fit statistics.
        variables: Mapping of parameter name → per-parameter result.
        configurations: lmfit fit configuration metadata (method, evals, DOF, …).
        errorbars: Whether lmfit estimated parameter errorbars.
        correlations: Parameter correlation matrix produced by lmfit.
        covariance_matrix: Parameter covariance matrix produced by lmfit.
        computational: Computational timing / platform metadata.
    """

    model_config = ConfigDict(extra="forbid")

    statistics: FitStatisticsReport = Field(default_factory=FitStatisticsReport)
    variables: dict[str, FitVariableReport] = Field(default_factory=dict)
    configurations: FitConfigurationsReport = Field(
        default_factory=FitConfigurationsReport
    )
    errorbars: dict[str, str] = Field(default_factory=dict)
    correlations: dict[str, dict[str, float]] = Field(default_factory=dict)
    covariance_matrix: dict[str, dict[str, float]] = Field(default_factory=dict)
    computational: ComputationalReport = Field(default_factory=ComputationalReport)


class SplitOrientFrame(BaseModel):
    """Split-orient DataFrame serialisation (pandas ``DataFrame.to_dict("split")``).

    Attributes:
        index: Row index values.
        columns: Column names.
        data: Row-major nested list of cell values.
    """

    model_config = ConfigDict(extra="allow")  # intentional: pandas split-orient dict

    index: list[str | int | float] = Field(default_factory=list)
    columns: list[str | int | float] = Field(default_factory=list)
    data: list[list[float | int | str | None]] = Field(default_factory=list)


class FitSummaryReport(BaseModel):
    """Top-level deserialisation model for a SpectraFit ``_summary.json`` file.

    All keys not explicitly modelled are captured via ``extra='allow'`` so that
    forward-compatible reading of richer result files is safe.

    Attributes:
        fit_insights: Nested fit diagnostics (statistics, variables, …).
        regression_metrics: Split-orient DataFrame (index/columns/data).
        linear_correlation: Correlation matrix in split-orient format.
        outfile: Base output path used when the fit was saved.
    """

    model_config = ConfigDict(extra="allow")  # intentional: forward-compat JSON schemas
    fit_insights: FitInsightsReport = Field(default_factory=FitInsightsReport)
    regression_metrics: SplitOrientFrame = Field(default_factory=SplitOrientFrame)
    linear_correlation: SplitOrientFrame = Field(default_factory=SplitOrientFrame)
    outfile: str | None = None

    @model_validator(mode="before")
    @classmethod
    def migrate_fitresult_schema(cls, raw: object) -> object:
        """Map FitResult JSON shape to the report-reader shape.

        FitResult stores regression and correlation data under ``data_summary``.
        The report command reads the legacy top-level keys, so this validator
        bridges the schema without requiring downstream dict casts.

        Args:
            raw: Incoming object passed to model validation.

        Returns:
            object: Normalized mapping compatible with FitSummaryReport fields.
        """
        if not isinstance(raw, dict):
            return raw
        data_summary = raw.get("data_summary")
        if not isinstance(data_summary, dict):
            return raw

        normalized: dict[str, object] = dict(  # intentional: legacy JSON normalization
            raw
        )
        if "regression_metrics" not in normalized:
            regression = data_summary.get("regression_metrics")
            if isinstance(regression, dict):
                normalized["regression_metrics"] = regression
        if "linear_correlation" not in normalized:
            correlation = data_summary.get("linear_correlation")
            if isinstance(correlation, dict):
                normalized["linear_correlation"] = correlation
        return normalized

    @classmethod
    def from_json_file(cls, path: str | object) -> FitSummaryReport:
        """Load and validate a ``_summary.json`` file.

        Args:
            path: Filesystem path to the summary JSON.

        Returns:
            FitSummaryReport: Validated model populated from the file.

        Raises:
            FileNotFoundError: If ``path`` does not exist.
            ValueError: If the file contains invalid JSON.
        """
        p = Path(str(path))
        with p.open(encoding="utf-8") as fh:
            return cls.model_validate(json.load(fh))

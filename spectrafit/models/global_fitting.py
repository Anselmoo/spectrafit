"""Global fitting models with shared parameter support.

This module provides Pydantic models for configuring and reporting global
(multi-dataset) fitting routines with first-class shared/linked parameters
and per-dataset weighting.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator


class SharedParameter(BaseModel):
    """A parameter shared (linked) across multiple datasets.

    Attributes:
        name: Parameter name in ``model_param_peak`` format
            (e.g. ``"pseudovoigt_center_1"``).
        constraint_expr: Optional lmfit expression that ties the parameter
            across datasets.  When *None* the parameter value is simply
            copied to every listed dataset.
        datasets: 0-based indices of datasets that share this parameter.
            An empty list means *all* datasets.
    """

    model_config = ConfigDict(frozen=True)

    name: str = Field(..., min_length=1, description="Parameter name to share.")
    constraint_expr: str | None = Field(
        default=None,
        description="Optional lmfit constraint expression.",
    )
    datasets: list[int] = Field(
        default_factory=list,
        description="Dataset indices sharing this parameter (empty = all).",
    )


class GlobalFittingConfig(BaseModel):
    """Configuration for a global (multi-dataset) fitting run.

    Attributes:
        n_datasets: Number of datasets to fit simultaneously.
        shared_parameters: Parameters linked across datasets.
        weights: Per-dataset weights applied to the residual.  When *None*
            all datasets are weighted equally (weight = 1.0).
    """

    model_config = ConfigDict(frozen=True)

    n_datasets: int = Field(..., ge=1, description="Number of datasets.")
    shared_parameters: list[SharedParameter] = Field(default_factory=list)
    weights: list[float] | None = Field(
        default=None,
        description="Per-dataset weights (length must equal n_datasets).",
    )

    @model_validator(mode="after")
    def _validate_weights_length(self) -> GlobalFittingConfig:
        """Ensure weights length matches n_datasets when provided."""
        if self.weights is not None and len(self.weights) != self.n_datasets:
            msg = (
                f"Length of weights ({len(self.weights)}) must equal "
                f"n_datasets ({self.n_datasets})."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_dataset_indices(self) -> GlobalFittingConfig:
        """Ensure shared parameter dataset indices are within range."""
        for sp in self.shared_parameters:
            for idx in sp.datasets:
                if idx < 0 or idx >= self.n_datasets:
                    msg = (
                        f"Dataset index {idx} in shared parameter "
                        f"'{sp.name}' is out of range [0, {self.n_datasets})."
                    )
                    raise ValueError(msg)
        return self


class DatasetResult(BaseModel):
    """Fitting result for a single dataset within a global fit.

    Attributes:
        index: 0-based dataset index.
        chi_squared: Chi-squared statistic for this dataset.
        reduced_chi_squared: Reduced chi-squared for this dataset.
        parameters: Best-fit parameter values keyed by name.
    """

    model_config = ConfigDict(frozen=True)

    index: int = Field(..., ge=0)
    chi_squared: float | None = Field(default=None)
    reduced_chi_squared: float | None = Field(default=None)
    parameters: dict[str, float] = Field(default_factory=dict)


class GlobalFittingResult(BaseModel):
    """Aggregated result of a global fitting run.

    Attributes:
        config: The configuration used for the fit.
        dataset_results: Per-dataset results.
        shared_parameter_values: Resolved values for shared parameters.
        correlation_matrix: Parameter correlation matrix as nested dict.
    """

    model_config = ConfigDict(frozen=True)

    config: GlobalFittingConfig
    dataset_results: list[DatasetResult] = Field(default_factory=list)
    shared_parameter_values: dict[str, float] = Field(default_factory=dict)
    correlation_matrix: dict[str, dict[str, float]] | None = Field(default=None)

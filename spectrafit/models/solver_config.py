"""Canonical Pydantic models for lmfit minimizer and optimizer configuration."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class MinimizerConfig(BaseModel):
    """Configuration for the lmfit minimizer.

    Attributes:
        nan_policy: Policy for handling NaN values during fitting.
        calc_covar: Whether to calculate the covariance matrix.

    Note:
        ``extra="allow"`` is intentional: lmfit accepts additional minimizer
        keyword arguments that vary by method and should pass through unchanged.
    """

    model_config = ConfigDict(extra="allow")

    nan_policy: str = Field(
        default="propagate",
        description="Policy for handling NaN values (propagate, raise, omit)",
    )
    calc_covar: bool = Field(
        default=True,
        description="Whether to calculate the covariance matrix",
    )


class OptimizerConfig(BaseModel):
    """Configuration for the lmfit optimizer.

    Attributes:
        max_nfev: Maximum number of function evaluations.
        method: Optimization method (e.g., leastsq, least_squares, nelder).

    Note:
        ``extra="allow"`` is intentional: method-specific kwargs (e.g., ``ftol``,
        ``xtol``) should pass through to lmfit without being declared here.
    """

    model_config = ConfigDict(extra="allow")

    max_nfev: int | None = Field(
        default=None,
        description="Maximum number of function evaluations",
    )
    method: str = Field(
        default="leastsq",
        description="Optimization method",
    )

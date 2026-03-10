"""Canonical Pydantic models for lmfit minimizer, optimizer, and CI configuration."""

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
        ``extra='allow'`` is intentional: lmfit accepts additional minimizer
        keyword arguments that vary by method and should pass through unchanged.
    """

    model_config = ConfigDict(
        extra="allow"  # intentional: result container, v2.1 migration target
    )

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
        ``extra='allow'`` is intentional: method-specific kwargs (e.g., ``ftol``,
        ``xtol``) should pass through to lmfit without being declared here.
    """

    model_config = ConfigDict(
        extra="allow"  # intentional: result container, v2.1 migration target
    )

    max_nfev: int | None = Field(
        default=None,
        description="Maximum number of function evaluations",
    )
    method: str = Field(
        default="leastsq",
        description="Optimization method",
    )


class ConfIntervalConfig(BaseModel):
    """Configuration for lmfit confidence interval calculation.

    Passed to :func:`lmfit.conf_interval` after a successful minimisation.
    All fields map directly to ``conf_interval()`` keyword arguments.

    Attributes:
        p_names: Parameter names to compute CI for.  ``None`` means all
            varying parameters.
        sigmas: Sigma levels for which to compute CI (default: 1-sigma, 2-sigma, 3-sigma).
        trace: Store parameter traces for each CI step.
        maxiter: Maximum number of iterations per CI boundary search.
        verbose: Print progress to stdout.
        prob_func: Name of a probability function to use instead of the
            default F-distribution test.  ``None`` uses the default.

    Examples:
        >>> ci = ConfIntervalConfig(sigmas=[1.0, 2.0])
        >>> ci.maxiter
        200
    """

    model_config = ConfigDict(extra="forbid")

    p_names: list[str] | None = Field(
        default=None,
        description="Parameter names to compute CI for (None = all varying)",
    )
    sigmas: list[float] = Field(
        default_factory=lambda: [1.0, 2.0, 3.0],
        description="Sigma levels (default: 1-sigma, 2-sigma, 3-sigma)",
    )
    trace: bool = Field(
        default=True,
        description="Store parameter trace for each CI step",
    )
    maxiter: int = Field(
        default=200,
        ge=1,
        le=2000,
        description="Maximum iterations per CI boundary search",
    )
    verbose: bool = Field(
        default=False,
        description="Print CI calculation progress",
    )
    prob_func: str | None = Field(
        default=None,
        description="Name of probability function (None = default F-distribution)",
    )

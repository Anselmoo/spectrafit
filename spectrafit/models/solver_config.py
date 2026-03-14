"""Canonical Pydantic models for lmfit minimizer, optimizer, and CI configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


if TYPE_CHECKING:
    from collections.abc import Mapping


type LmfitKwargScalar = str | int | float | bool | None
type LmfitKwargValue = (
    LmfitKwargScalar
    | list["LmfitKwargValue"]
    | dict[str, "LmfitKwargValue"]
    | tuple["LmfitKwargValue", ...]
)


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


class SolverConfig(BaseModel):
    """Canonical internal solver configuration.

    This model groups minimizer and optimizer settings used by the solver core.
    API-facing DTOs may adapt to and from this model, but internal execution
    should depend on this canonical representation only.
    """

    model_config = ConfigDict(extra="forbid")

    minimizer: MinimizerConfig = Field(
        default_factory=MinimizerConfig,
        description="Minimizer options forwarded to lmfit",
    )
    optimizer: OptimizerConfig = Field(
        default_factory=OptimizerConfig,
        description="Optimizer options forwarded to lmfit",
    )

    def minimizer_kwargs(self) -> dict[str, LmfitKwargValue]:
        """Serialize minimizer options for ``lmfit.Minimizer`` construction."""
        return self.minimizer.model_dump()

    def optimizer_kwargs(self) -> dict[str, LmfitKwargValue]:
        """Serialize optimizer options for ``lmfit.Minimizer.minimize``."""
        return self.optimizer.model_dump(exclude_none=True)


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


def normalize_conf_interval_value(
    conf_interval: bool | ConfIntervalConfig | Mapping[str, object] | None,
) -> ConfIntervalConfig | None:
    """Normalize raw CI input to the canonical configuration model."""
    if isinstance(conf_interval, ConfIntervalConfig):
        return conf_interval
    if conf_interval is None or conf_interval is False:
        return None
    if conf_interval is True:
        return ConfIntervalConfig()

    raw_settings = dict(conf_interval)
    if "sigma" in raw_settings and "sigmas" not in raw_settings:
        raw_settings["sigmas"] = raw_settings.pop("sigma")

    prob_func = raw_settings.get("prob_func")
    if prob_func is not None and not isinstance(prob_func, str):
        raw_settings.pop("prob_func", None)

    return ConfIntervalConfig.model_validate(raw_settings)

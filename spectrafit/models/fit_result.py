"""Typed fitting result container — v2 replacement for ``FittingArgs`` dict output.

Mirrors the :class:`~prototype.input_output_interface.PrototypeOutput` design with
full JSON Schema support via Pydantic v2.  The model is intentionally kept at the
*data* level (plain Python scalars / lists) so that it is serialisable to JSON
without any lmfit dependency at the consumer side.

Usage::

    result = FitResult.from_minimizer_result(minimizer_result, config, x, y_data)
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

from pydantic import BaseModel
from pydantic import Field


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
        method: Optimisation method used (e.g. ``"leastsq"``, ``"emcee"``).
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


class FitResult(BaseModel):
    """Full fitting result — JSON Schema-validated export container.

    Suitable for serialisation to ``output.json``, HTTP response payloads, or
    MCP tool return values.  All fields are plain Python scalars / lists with no
    lmfit objects, making the model fully portable.

    Attributes:
        input_snapshot: Original input configuration dict (for reproducibility).
        statistics: Summary statistics of the minimisation.
        parameters: Per-parameter fitted results.
        components: Per-component evaluated curves.
        x: x-axis values used in the fit.
        y_data: Observed y-values.
        y_fit: Total fitted y-values (sum of all component curves).
    """

    input_snapshot: dict[str, object] = Field(
        default_factory=dict,
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

    def save(self, path: Path | str) -> None:
        """Serialise the result to a JSON file.

        Args:
            path: Destination path (e.g. ``"output.json"``).
        """
        Path(path).write_text(
            json.dumps(self.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

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

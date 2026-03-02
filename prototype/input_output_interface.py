"""Pydantic I/O models for the prototype fitting pipeline.

This module is intentionally self-contained — zero imports from spectrafit.*.
It provides:

- :class:`PrototypeInput`  — validated input schema loaded from TOML/JSON/YAML.
- :class:`PrototypeOutput` — fitting result container serialised to ``output.json``.

Schema design (v1.0)
--------------------
Input uses a flat ``[[components]]`` TOML array-of-tables, a single ``[solver]``
block (replacing the legacy split ``[fit.minimizer]`` / ``[fit.optimizer]``), and
inline-table parameter specs with ``bounds = [min, max]`` syntax::

    [[components]]
    id    = "p1"
    model = "gaussian"

    [components.parameters]
    amplitude = { value = 1.0, bounds = [0.0, 3.0], vary = true }

This avoids the 3-level nested dict required by the legacy SpectraFit format
and enables full schema validation via Pydantic + JSON Schema.
"""

from __future__ import annotations

import json
import math
import re

from pathlib import Path
from typing import Annotated
from typing import Literal

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

# Pre-compiled regex for dot-notation → underscore translation.
_DOT_NOTATION_RE: re.Pattern[str] = re.compile(r"\b([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b")

# Validated 2-element float list used for parameter bounds [min, max].
_Bounds = Annotated[list[float], Field(min_length=2, max_length=2)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _translate_dot_notation(expr: str) -> str:
    """Translate ``"id.field"`` expressions to lmfit ``"id_field"`` notation.

    Args:
        expr: User expression, possibly containing dot-notation references.

    Returns:
        Expression with dots replaced by underscores where used as id.field.

    Examples:
        >>> _translate_dot_notation("p1.center + 1.0")
        'p1_center + 1.0'
        >>> _translate_dot_notation("p2.fwhmg")
        'p2_fwhmg'
    """
    return _DOT_NOTATION_RE.sub(r"\1_\2", expr)


class ConfigError(ValueError):
    """Raised when a config file cannot be parsed or validated.

    Attributes:
        path: Path to the config file that triggered the error (if known).
    """

    def __init__(self, message: str, path: Path | None = None) -> None:
        """Initialise with message and optional file path.

        Args:
            message: Human-readable error description.
            path: Path to the config file that triggered the error, if known.
        """
        prefix = f"[{path}] " if path else ""
        super().__init__(f"{prefix}{message}")
        self.path = path


def _parse_file(path: Path) -> dict[str, object]:
    """Parse a TOML, JSON, or YAML file into a raw dict.

    Args:
        path: Path to the config file.

    Returns:
        Parsed dict ready for Pydantic validation.

    Raises:
        ConfigError: If the file extension is unsupported or parsing fails.
        FileNotFoundError: If ``path`` does not exist.
    """
    suffix = path.suffix.lower()

    try:
        if suffix == ".toml":
            try:
                import tomllib  # Python >= 3.11
            except ImportError:
                import tomli as tomllib  # type: ignore[no-redef]
            with open(path, "rb") as fh:
                return tomllib.load(fh)  # type: ignore[return-value]

        if suffix == ".json":
            with open(path) as fh:
                return json.load(fh)

        if suffix in {".yaml", ".yml"}:
            import yaml

            with open(path) as fh:
                return yaml.safe_load(fh)

    except (OSError, json.JSONDecodeError, Exception) as exc:
        raise ConfigError(f"Failed to parse file: {exc}", path=path) from exc

    raise ConfigError(
        f"Unsupported file format {suffix!r}. Use .toml, .json, or .yaml.",
        path=path,
    )


# ---------------------------------------------------------------------------
# Input models
# ---------------------------------------------------------------------------


class FitParameterSpec(BaseModel):
    """A single lmfit parameter constraint.

    Attributes:
        value: Initial parameter value.
        bounds: Optional ``[min, max]`` bounds list.
            If ``None``, the parameter is unbounded (``−∞``, ``+∞``).
        vary: Whether the parameter is free during optimisation.
        expr: Constraint expression in dot or underscore notation.
        units: Optional physical units label (for documentation only).

    Properties:
        min: Lower bound — ``bounds[0]`` or ``-math.inf`` when unbounded.
        max: Upper bound — ``bounds[1]`` or ``+math.inf`` when unbounded.

    Examples:
        >>> p = FitParameterSpec(value=1.0, bounds=[0.0, 3.0])
        >>> p.min, p.max
        (0.0, 3.0)
        >>> p = FitParameterSpec(value=0.5, expr="p1.center + 1.0")
        >>> p.expr
        'p1_center + 1.0'
    """

    model_config = ConfigDict(extra="forbid")

    value: float = 0.0
    bounds: _Bounds | None = None
    vary: bool = True
    expr: str | None = None
    units: str | None = None

    @model_validator(mode="after")
    def _validate_bounds(self) -> FitParameterSpec:
        """Enforce bounds order and value-within-bounds.

        Returns:
            Self after validation.

        Raises:
            ValueError: If bounds are out of order or value is outside bounds.
        """
        if self.bounds is not None:
            lo, hi = self.bounds
            if lo > hi:
                raise ValueError(f"bounds[0]={lo} must be ≤ bounds[1]={hi}")
            if not (lo <= self.value <= hi):
                raise ValueError(
                    f"value={self.value} must be within bounds [{lo}, {hi}]"
                )
        return self

    @field_validator("expr", mode="before")
    @classmethod
    def translate_expr(cls, v: str | None) -> str | None:
        """Translate dot notation to lmfit underscore notation at parse time.

        Args:
            v: Raw expression string or ``None``.

        Returns:
            Translated expression or ``None``.
        """
        return _translate_dot_notation(str(v)) if v is not None else v

    @property
    def min(self) -> float:
        """Lower bound — ``bounds[0]`` or ``-math.inf`` when unbounded."""
        return self.bounds[0] if self.bounds is not None else -math.inf

    @property
    def max(self) -> float:
        """Upper bound — ``bounds[1]`` or ``+math.inf`` when unbounded."""
        return self.bounds[1] if self.bounds is not None else math.inf


class ComponentSpec(BaseModel):
    """A single fitting component: one model type with parameter constraints.

    Attributes:
        id: Unique component identifier (e.g. ``"p1"``, ``"bg"``).
        model: Registry key identifying the model (e.g. ``"gaussian"``).
        parameters: Mapping of parameter name to constraint spec.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    model: str
    parameters: dict[str, FitParameterSpec] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_model_name(self) -> ComponentSpec:
        """Validate ``model`` and parameter names against MODEL_REGISTRY.

        Returns:
            Self after validation.

        Raises:
            ValueError: If ``model`` is not registered or parameter names are invalid.
        """
        try:
            from prototype.model_functions import MODEL_REGISTRY
        except ImportError:
            from model_functions import MODEL_REGISTRY  # type: ignore[no-redef]

        if self.model not in MODEL_REGISTRY:
            valid = sorted(MODEL_REGISTRY)
            raise ValueError(f"Unknown model {self.model!r}. Valid models: {valid}")
        expected = set(MODEL_REGISTRY[self.model].parameters)
        given = set(self.parameters)
        unknown = given - expected
        if unknown:
            raise ValueError(
                f"Component {self.id!r}: unknown parameters {sorted(unknown)} "
                f"for model {self.model!r}. Expected: {sorted(expected)}"
            )
        return self


class DataConfig(BaseModel):
    """Data file configuration.

    Attributes:
        infile: Path to the CSV data file.
        x_col: Column name for the x-axis (energy / wavelength).
        y_col: Column name for the y-axis (intensity / counts).
    """

    model_config = ConfigDict(extra="forbid")

    infile: Path
    x_col: str = "energy"
    y_col: str = "intensity"


class MetaConfig(BaseModel):
    """Optional metadata block.

    Attributes:
        description: Free-text description of this fitting job.
    """

    model_config = ConfigDict(extra="allow")

    description: str = ""


class SolverConfig(BaseModel):
    """Combined minimizer + optimizer settings.

    Replaces the legacy split ``[fit.minimizer]`` / ``[fit.optimizer]``
    structure with a single flat ``[solver]`` block.

    Attributes:
        method: Minimization algorithm (e.g. ``"leastsq"``, ``"least_squares"``).
        max_nfev: Maximum number of function evaluations.
        nan_policy: How to handle NaN values in residuals.
        calc_covar: Whether to calculate the covariance matrix.
    """

    model_config = ConfigDict(extra="allow")

    method: str = "leastsq"
    max_nfev: int = 1000
    nan_policy: Literal["propagate", "omit", "raise"] = "propagate"
    calc_covar: bool = True


class PrototypeInput(BaseModel):
    """Top-level input schema (flat structure, schema v1.0).

    The schema uses a flat ``[[components]]`` TOML array rather than the
    legacy ``[[fit.components]]`` nesting, eliminating the 3-level nested-dict
    iteration of the original codebase.

    Attributes:
        schema_version: Schema version string for future evolution.
        config_type: Fixed identifier for this config type.
        meta: Optional metadata block.
        data: Data file and column configuration.
        solver: Combined minimizer + optimizer settings.
        components: Ordered list of fitting component specifications.

    Examples:
        >>> cfg = PrototypeInput.load(Path("prototype/input.toml"))
        >>> [c.id for c in cfg.components]
        ['p1', 'p2', 'bg']
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"
    config_type: str = "peak_fit"
    meta: MetaConfig = Field(default_factory=MetaConfig)
    data: DataConfig
    solver: SolverConfig = Field(default_factory=SolverConfig)
    components: list[ComponentSpec]

    @classmethod
    def load(cls, path: Path) -> PrototypeInput:
        """Load and validate input from a TOML, JSON, or YAML file.

        Args:
            path: Path to the input file. Extension determines parser:
                ``.toml`` → tomllib/tomli, ``.json`` → stdlib json,
                ``.yaml``/``.yml`` → pyyaml.

        Returns:
            Validated :class:`PrototypeInput` instance.

        Raises:
            ValueError: If the file extension is not supported.
            FileNotFoundError: If ``path`` does not exist.
        """
        return cls.model_validate(_parse_file(Path(path)))


# ---------------------------------------------------------------------------
# Output models
# ---------------------------------------------------------------------------


class ParameterResult(BaseModel):
    """Fitted value and uncertainty for a single lmfit parameter.

    Attributes:
        name: lmfit parameter name (e.g. ``"p1_amplitude"``).
        init_value: Initial value before fitting.
        best_value: Best-fit value after minimisation.
        stderr: Standard error (``None`` if not computed or fixed).
        vary: Whether the parameter was free during fitting.
        expr: Constraint expression if any.
    """

    name: str
    init_value: float
    best_value: float
    stderr: float | None
    vary: bool
    expr: str | None


class ComponentResult(BaseModel):
    """Per-component fitted curve.

    Attributes:
        id: Component identifier matching the input ``ComponentSpec.id``.
        model: Model name.
        curve: Fitted y-values at each x point.
    """

    id: str
    model: str
    curve: list[float]


class FitStatistics(BaseModel):
    """Summary statistics of the minimisation result.

    Attributes:
        chi_squared: Sum of squared residuals (unnormalised).
        redchi: Reduced chi-squared (chi_squared / nfree).
        nfev: Number of function evaluations.
        ndata: Number of data points.
        nvarys: Number of free parameters.
        nfree: Degrees of freedom (ndata - nvarys).
        success: Whether the minimiser converged.
        message: Status message from the minimiser.
    """

    chi_squared: float
    redchi: float
    nfev: int
    ndata: int
    nvarys: int
    nfree: int
    success: bool
    message: str


class PrototypeOutput(BaseModel):
    """Full fitting result, suitable for serialisation to ``output.json``.

    Attributes:
        input_snapshot: Original input dict (for reproducibility).
        statistics: Fit statistics summary.
        parameters: Per-parameter fit results.
        components: Per-component fitted curves.
        x: x-axis values used in the fit.
        y_data: Observed y-values.
        y_fit: Total fitted y-values (sum of all components).
    """

    input_snapshot: dict[str, object]
    statistics: FitStatistics
    parameters: list[ParameterResult]
    components: list[ComponentResult]
    x: list[float]
    y_data: list[float]
    y_fit: list[float]

    def save(self, path: Path) -> None:
        """Serialise output to a JSON file.

        Args:
            path: Destination path (e.g. ``prototype/output.json``).
        """
        Path(path).write_text(
            json.dumps(self.model_dump(mode="json"), indent=2),
            encoding="utf-8",
        )

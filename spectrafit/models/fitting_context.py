"""FittingContext — typed fitting mode replacing bare ``global_: int``.

The old ``global_: int`` flag (0/1/2) is a stringly-typed encoding of
what is semantically a richer concept: *how many datasets are being fit
simultaneously and what advanced fitting strategy applies*.

This module introduces:

- :class:`FittingMode` — a ``str`` enum with four values.  ``str`` mixin
  allows direct JSON serialisation without a custom encoder.
- :class:`FittingContext` — a Pydantic model that replaces the bare
  integer and makes all fitting configuration explicit and validated.

Backward compatibility
----------------------
``FittingContext.from_global_int(n)`` converts old ``global_: int`` values:

=====  =======================
 int    FittingMode
=====  =======================
  0    STANDARD (single dataset)
  1    GLOBAL (multi-dataset)
  2    GLOBAL (pre-defined params)
=====  =======================
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# FittingMode
# ---------------------------------------------------------------------------
# Use a plain str-subclassing enum for clean JSON serialisation
import sys

from enum import Enum
from enum import unique

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import model_validator

from spectrafit.models.global_fitting import SharedParameter  # noqa: TC001


@unique
class EnvironmentMode(str, Enum):
    """Runtime execution environment.

    Attributes:
        CLI: Interactive terminal session (``sys.stdin.isatty()`` is ``True``).
        NOTEBOOK: Running inside a Jupyter / IPython kernel.
        API: Non-interactive process (piped stdin, CI runner, scripted call).

    Examples:
        >>> EnvironmentMode.CLI == "cli"
        True
    """

    CLI = "cli"
    NOTEBOOK = "notebook"
    API = "api"


def detect_environment() -> EnvironmentMode:
    """Detect the current runtime environment.

    Checks for an active IPython kernel first (covers Jupyter notebooks and
    interactive IPython sessions), then falls back to ``sys.stdin.isatty()``.

    Returns:
        :attr:`EnvironmentMode.NOTEBOOK` when an IPython kernel is active,
        :attr:`EnvironmentMode.CLI` when stdin is a tty,
        :attr:`EnvironmentMode.API` otherwise (piped, CI, scripted).

    Examples:
        >>> isinstance(detect_environment(), EnvironmentMode)
        True
    """
    try:
        from IPython import get_ipython  # noqa: PLC0415

        if get_ipython() is not None:
            return EnvironmentMode.NOTEBOOK
    except ImportError:
        pass
    try:
        if not sys.stdin.isatty():
            return EnvironmentMode.API
    except Exception:  # noqa: BLE001 — closed or missing stdin in some environments
        return EnvironmentMode.API
    return EnvironmentMode.CLI


@unique
class FittingMode(str, Enum):
    """Enumeration of supported fitting strategies.

    Attributes:
        STANDARD: Single-dataset standard fit (replaces ``global_ = 0``).
        GLOBAL: Multi-dataset global fit with optional shared parameters
            (replaces ``global_ = 1`` and ``global_ = 2``).
        TIME_RESOLVED: Sequence of spectra sharing peak positions along a
            time axis. Reserved for future use.
        SEQUENTIAL: Sequential fitting where the result of one fit seeds
            the next.  Reserved for future use.

    Examples:
        >>> FittingMode.STANDARD == "standard"
        True
        >>> FittingMode("global") == FittingMode.GLOBAL
        True
    """

    STANDARD = "standard"
    GLOBAL = "global"
    TIME_RESOLVED = "time_resolved"
    SEQUENTIAL = "sequential"

    def __str__(self) -> str:
        """Return the enum value string (not 'FittingMode.STANDARD' repr)."""
        return self.value


# ---------------------------------------------------------------------------
# FittingContext
# ---------------------------------------------------------------------------


class FittingContext(BaseModel):
    """Typed, validated fitting context replacing ``global_: int``.

    Args:
        mode: Fitting strategy.  Defaults to :attr:`FittingMode.STANDARD`.
        n_datasets: Number of datasets for multi-dataset modes.  Must be
            ``≥ 1``.  Defaults to ``1``.
        shared_parameters: Parameters linked across datasets.  Only
            meaningful for :attr:`FittingMode.GLOBAL`.
        time_axis: Values along the time axis.  Only meaningful for
            :attr:`FittingMode.TIME_RESOLVED`.

    Examples:
        >>> ctx = FittingContext(mode=FittingMode.STANDARD)
        >>> ctx.global_int
        0
        >>> ctx = FittingContext(mode=FittingMode.GLOBAL, n_datasets=5)
        >>> ctx.global_int
        1
        >>> FittingContext.from_global_int(0).mode == FittingMode.STANDARD
        True
    """

    model_config = ConfigDict(frozen=True)

    mode: FittingMode = FittingMode.STANDARD
    n_datasets: int = Field(default=1, ge=1)
    shared_parameters: list[SharedParameter] = Field(default_factory=list)
    time_axis: list[float] | None = Field(default=None)
    environment: EnvironmentMode = Field(
        default_factory=detect_environment,
        description="Runtime environment — CLI, Notebook, or API.",
    )

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_global_requires_multiple_datasets(self) -> FittingContext:
        """GLOBAL mode must declare at least 2 datasets."""
        if self.mode == FittingMode.GLOBAL and self.n_datasets < 2:  # noqa: PLR2004
            msg = (
                "FittingMode.GLOBAL requires n_datasets >= 2; "
                f"got n_datasets={self.n_datasets}."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def _validate_time_axis_length(self) -> FittingContext:
        """TIME_RESOLVED mode time_axis length must match n_datasets."""
        if (
            self.mode == FittingMode.TIME_RESOLVED
            and self.time_axis is not None
            and len(self.time_axis) != self.n_datasets
        ):
            msg = (
                f"time_axis length ({len(self.time_axis)}) must equal "
                f"n_datasets ({self.n_datasets})."
            )
            raise ValueError(msg)
        return self

    # ------------------------------------------------------------------
    # Properties and helpers
    # ------------------------------------------------------------------

    @property
    def global_int(self) -> int:
        """Legacy ``global_: int`` representation for backward compatibility.

        Returns:
            ``0`` for STANDARD, ``1`` for GLOBAL/TIME_RESOLVED/SEQUENTIAL.
        """
        return 0 if self.mode == FittingMode.STANDARD else 1

    @property
    def is_global(self) -> bool:
        """Whether global fitting mode is active.

        Returns:
            ``True`` for GLOBAL/TIME_RESOLVED/SEQUENTIAL; ``False`` for STANDARD.
        """
        return self.mode != FittingMode.STANDARD

    @classmethod
    def from_global_int(cls, value: int) -> FittingContext:
        """Construct a :class:`FittingContext` from a legacy integer flag.

        Args:
            value: Legacy ``global_`` value (0, 1, or 2).

        Returns:
            A :class:`FittingContext` with the equivalent mode.

        Raises:
            ValueError: If ``value`` is not 0, 1, or 2.

        Examples:
            >>> FittingContext.from_global_int(0).mode == FittingMode.STANDARD
            True
            >>> FittingContext.from_global_int(1).mode == FittingMode.GLOBAL
            True
        """
        _map = {
            0: FittingMode.STANDARD,
            1: FittingMode.GLOBAL,
            2: FittingMode.GLOBAL,  # WITH_PRE maps to GLOBAL as well
        }
        if value not in _map:
            msg = f"global_ must be 0, 1, or 2; got {value!r}."
            raise ValueError(msg)
        if value == 0:
            return cls(mode=FittingMode.STANDARD)
        # For values 1/2, we need at least 2 datasets; caller must set n_datasets
        return cls(mode=FittingMode.GLOBAL, n_datasets=2)

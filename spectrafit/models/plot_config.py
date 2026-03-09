"""Typed plot configuration — replaces the raw args dict in PlotSpectra."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.types import DataSplitDict


class PlotConfig(BaseModel):
    """Typed plot configuration for :class:`~spectrafit.plotting.PlotSpectra`.

    Replaces the legacy ``args: dict[str, object]`` contract so that callers
    and the plotting layer share a single, validated surface.

    Args:
        noplot: Suppress all plot windows.  Defaults to ``False``.
        global_fitting: Fitting mode; non-standard triggers the global-spectra
            plotting path.  Accepts a :class:`FittingMode` value or legacy
            ``int``/``bool`` (``0``/``False`` → :attr:`~FittingMode.STANDARD`,
            ``1``/``True`` → :attr:`~FittingMode.GLOBAL`).
        data_statistic: Per-spectrum statistical summary keyed by dataset
            identifier.  Used to count the number of spectra for the global
            grid layout.

    Examples:
        >>> PlotConfig()
        PlotConfig(noplot=False, ...)
        >>> PlotConfig(noplot=True)
        PlotConfig(noplot=True, ...)
    """

    model_config = ConfigDict(extra="forbid")

    noplot: bool = Field(default=False, description="Suppress all matplotlib windows.")
    global_fitting: FittingMode = Field(
        default=FittingMode.STANDARD,
        description="Fitting mode — non-standard triggers the global-spectra grid layout.",
    )
    data_statistic: DataSplitDict = Field(
        default_factory=lambda: DataSplitDict(data=[], index=[], columns=[]),
        description="Preprocessing statistics in pandas split-dict format.",
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

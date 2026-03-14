"""Typed plot configuration for SpectraFit's shared Plotly plotting pipeline.

This model backs the validated configuration passed into
``spectrafit.plotting.PlotSpectra`` from the CLI and other non-notebook
callers. It is intentionally separate from notebook/Jupyter plotting concerns
and should not be treated as the configuration surface for interactive widgets.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.split_frame import SplitFrame


class PlotConfig(BaseModel):
    """Typed configuration for the CLI/static :class:`~spectrafit.plotting.PlotSpectra` path.

    Replaces the legacy untyped ``args`` dict contract so that callers
    and the static plotting layer share a single, validated surface. This model
    owns the non-interactive Plotly configuration used by the CLI fitting
    flow; notebook-specific plotting state should live elsewhere.

    Args:
        noplot: Suppress all plot windows.  Defaults to ``False``.
        global_fitting: Fitting mode; non-standard triggers the global-spectra
            plotting path.
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

    noplot: bool = Field(
        default=False, description="Suppress all interactive plot display."
    )
    global_fitting: FittingMode = Field(
        default=FittingMode.STANDARD,
        description="Fitting mode — non-standard triggers the global-spectra grid layout.",
    )
    data_statistic: SplitFrame = Field(
        default_factory=SplitFrame.empty,
        description=(
            "Preprocessing statistics for the static global-spectra layout as a "
            "validated split-frame model."
        ),
    )

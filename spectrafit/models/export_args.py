"""Typed Pydantic model for the pipeline result dict passed to :class:`SaveResult`.

See :class:`~spectrafit.core.export.SaveResult` for usage.

``SaveResultArgs`` replaces the bare ``dict[str, object]`` (formerly typed as
``FittingArgs``) at the export boundary.  It is the *write-path* counterpart to
:class:`~spectrafit.models.fit_summary.FitSummaryReport`, which is the *read-path*
model used by the CLI ``report`` sub-command.

!!! note "Usage"
    ``SaveResultArgs`` is not yet wired into :class:`~spectrafit.core.export.SaveResult`
    because ``export.py`` is frozen until Phase 6.  It is defined here so that:

    1. The model hierarchy is complete and importable.
    2. Downstream code (e.g. future MCP server, batch runner) can validate the
       pipeline result dict at the export boundary without touching the frozen module.
    3. Tests can document and pin the expected shape of the result dict.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.results.fit_summary import FitInsightsReport
from spectrafit.models.results.fit_summary import SplitOrientFrame


class SaveResultArgs(BaseModel):
    """Validated representation of the pipeline result dict for the export layer.

    This model captures every key that :class:`~spectrafit.core.export.SaveResult`
    reads.  Unknown keys from the pipeline (e.g. ``peaks``, ``column``,
    ``minimizer``, ``_bundle``) are stored as extra fields (``extra="allow"``) so
    that ``model_dump()`` produces the same dict that was passed in — preserving
    full round-trip fidelity for the JSON summary file.

    Attributes:
        outfile: Base path for output files (without extension).  All save methods
            append their own suffix (e.g. ``_summary.json``, ``_fit.csv``).
        linear_correlation: Pearson correlation matrix in pandas split-orient format
            (``DataFrame.to_dict("split")``), produced by ``df.corr()``.
        fit_insights: Per-parameter diagnostics from :mod:`~spectrafit.report`.
        regression_metrics: Regression quality metrics in split-orient format.
        descriptive_statistic: Descriptive statistics of the fit DataFrame in
            split-orient format (``df.describe().to_dict("split")``).
    """

    model_config = ConfigDict(extra="allow", frozen=False)

    outfile: str = Field(description="Base output path (no extension)")
    linear_correlation: SplitOrientFrame = Field(
        default_factory=SplitOrientFrame,
        description="Correlation matrix (split-orient)",
    )
    fit_insights: FitInsightsReport = Field(
        default_factory=FitInsightsReport,
        description="Per-parameter fit diagnostics",
    )
    regression_metrics: SplitOrientFrame = Field(
        default_factory=SplitOrientFrame,
        description="Regression quality metrics (split-orient)",
    )
    descriptive_statistic: SplitOrientFrame = Field(
        default_factory=SplitOrientFrame,
        description="Descriptive statistics (split-orient)",
    )

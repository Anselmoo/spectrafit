"""Type aliases for the SpectraFit fitting parameter structure.

This module is the single source of truth for the nested parameter
type aliases used throughout the pipeline.

Previously these lived in ``spectrafit.models.autopeak``. A re-export
shim remains there for backward compatibility until v2.1.0.
"""

from __future__ import annotations

from typing import TypeAlias
from typing import TypedDict


ParameterConstraint: TypeAlias = dict[str, float | bool | str | None]
"""Single lmfit parameter constraint.

Example::

    {"min": 0, "max": 2, "vary": True, "value": 1.0}
"""

ModelParameterSpec: TypeAlias = dict[str, ParameterConstraint]
"""Maps parameter names to constraints.

Example::

    {"amplitude": {...}, "center": {...}, "fwhmg": {...}}
"""


class DataSplitDict(TypedDict):
    """Pandas ``DataFrame.to_dict(orient='split')`` output format.

    Used for ``linear_correlation``, ``regression_metrics``,
    ``descriptive_statistic``, and ``data_statistic`` keys in the
    pipeline result dict.
    """

    data: list[list[float | str | None]]
    index: list[int | str]
    columns: list[int | str]


class FitReportKwargs(TypedDict, total=False):
    """Keyword arguments forwarded to :class:`~spectrafit.report.confidence.FitReport`."""

    sort_pars: bool
    show_correl: bool
    min_correl: float

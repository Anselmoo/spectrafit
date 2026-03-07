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

PeakModelSpec: TypeAlias = dict[str, ModelParameterSpec]
"""Maps a model name to its parameter specs.

Example::

    {"gaussian": {"amplitude": {...}, "center": {...}}}
"""

PeaksDict: TypeAlias = dict[str, PeakModelSpec]
"""All peaks keyed by positive string-integer index.

Example::

    {"1": {"pseudovoigt": {...}}, "2": {"gaussian": {...}}}
"""


class DataSplitDict(TypedDict):
    """Pandas ``DataFrame.to_dict(orient='split')`` output format.

    Used for ``linear_correlation``, ``regression_metrics``,
    ``descriptive_statistic``, and ``data_statistic`` keys in the
    pipeline result dict.
    """

    data: list[list[float | str | None]]
    index: list[int | str]
    columns: list[str]


class FitReportKwargs(TypedDict, total=False):
    """Keyword arguments forwarded to :class:`~spectrafit.report.confidence.FitReport`."""

    sort_pars: bool
    show_correl: bool
    min_correl: float


FittingArgs: TypeAlias = dict[str, object]
"""Top-level fitting arguments dictionary passed through the pipeline.

Keys: ``peaks``, ``column``, ``minimizer``, ``optimizer``, ``global_``,
and optionally ``conf_interval``, ``global_fitting_config``.

!!! warning
    This alias is the v2 migration target. In v2.1.0 all consumers
    will accept ``UnifiedFittingConfig`` directly and this alias will
    be removed.
"""

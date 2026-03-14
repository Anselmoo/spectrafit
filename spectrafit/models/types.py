"""Type aliases for the SpectraFit fitting parameter structure.

This module is the single source of truth for the nested parameter
type aliases used throughout the pipeline.

Previously these lived in ``spectrafit.models.autopeak``. A re-export
shim remains there for backward compatibility until v2.1.0.
"""

from __future__ import annotations

from typing import TypedDict

from spectrafit.models.split_frame import SplitFrame


type ParameterConstraint = dict[str, float | bool | str | None]
"""Single lmfit parameter constraint.

Example::

    {"min": 0, "max": 2, "vary": True, "value": 1.0}
"""

type ModelParameterSpec = dict[str, ParameterConstraint]
"""Maps parameter names to constraints.

Example::

    {"amplitude": {...}, "center": {...}, "fwhmg": {...}}
"""


class CanonicalComponentInput(TypedDict):
    """Canonical serialized v2 component payload."""

    id: str
    model: str
    parameters: ModelParameterSpec


class CanonicalSpectraFitInput(TypedDict):
    """Canonical serialized v2 SpectraFit config payload."""

    components: list[CanonicalComponentInput]


type LegacyModelParameterSpec = dict[str, ModelParameterSpec]
"""Legacy serialized per-component model payload used by compatibility shims."""


class LegacySpectraFitInput(TypedDict):
    """Legacy serialized v1 SpectraFit config payload."""

    peaks: dict[str, LegacyModelParameterSpec]


DataSplitDict = SplitFrame
"""Backward-compatible alias for the canonical split-frame model."""


class FitReportKwargs(TypedDict, total=False):
    """Keyword arguments shared by canonical reporting-service helpers.

    These flags describe the runtime reporting knobs owned by
    :mod:`spectrafit.reporting.service`, including
    :func:`spectrafit.reporting.service.render_runtime_report` and
    :func:`spectrafit.reporting.service.emit_runtime_report`.
    """

    sort_pars: bool
    show_correl: bool
    min_correl: float

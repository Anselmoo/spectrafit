"""Canonical ingress for legacy peak-spec to Component conversion.

This module is the **single boundary owner** for converting any legacy peak/model
spec format into typed ``Component`` models.  Both v1 config migration and the
transformer notebook utilities must delegate here so that
``Component.model_validate`` is called in exactly one place.

Centralising here resolves the duplicate conversion pipelines previously split
between :mod:`spectrafit.adapters.v1_config_migration` and
:mod:`spectrafit.utilities.transformer`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from spectrafit.models.peak_models import Component
from spectrafit.models.registry import REGISTRY


if TYPE_CHECKING:
    from collections.abc import Mapping


type LegacyConstraintScalar = float | int | bool | str | None
type LegacyParameterConstraint = dict[str, LegacyConstraintScalar]
type LegacyModelParameters = dict[str, LegacyParameterConstraint]
type LegacyModelSpec = dict[str, LegacyModelParameters]


def spec_to_component(
    component_id: str,
    model_name: str,
    parameters: Mapping[str, object],
) -> Component:
    """Construct a typed ``Component`` from an atomic raw spec.

    This is the **canonical ingress** for all legacy-to-Component conversion.
    Every caller that turns a raw dict spec into a ``Component`` must go through
    this function.

    Args:
        component_id: Canonical component identifier, e.g. ``"p1"``.
        model_name: Registered peak model name, e.g. ``"gaussian"``.
        parameters: Raw parameter constraint mapping accepted by
            :class:`~spectrafit.models.peak_models.Component`.

    Returns:
        Component: Validated typed component.

    Examples:
        >>> c = spec_to_component(
        ...     "p1", "gaussian",
        ...     {"amplitude": {"value": 1.0, "min": 0.0, "max": 2.0, "vary": True}},
        ... )
        >>> c.id
        'p1'
        >>> c.model
        'gaussian'
    """
    return Component.model_validate(
        {
            "id": component_id,
            "model": model_name,
            "parameters": dict(parameters),
        }
    )


def legacy_list_to_components(peak_list: list[LegacyModelSpec]) -> list[Component]:
    """Convert a notebook-style legacy peak list into typed ``Component`` models.

    Entries whose model name is not found in the registry are silently skipped,
    preserving the existing ``list2components`` / ``list2dict`` filtering
    behaviour.

    Args:
        peak_list: List of ``{model_name: {param: constraint}}`` specs as
            emitted by the notebook initial-model helper.

    Returns:
        list[Component]: Validated typed components, one per registered entry.

    Examples:
        >>> specs = [{"gaussian": {"amplitude": {"value": 1.0}}}]
        >>> comps = legacy_list_to_components(specs)
        >>> comps[0].id
        'p1'
    """
    components: list[Component] = []
    for i, peak in enumerate(peak_list, start=1):
        model_name = next(iter(peak))
        if model_name not in REGISTRY:
            continue
        components.append(spec_to_component(f"p{i}", model_name, peak[model_name]))
    return components


__all__ = [
    "LegacyModelSpec",
    "legacy_list_to_components",
    "spec_to_component",
]

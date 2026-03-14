"""Transformer functions for the SpectraFit."""

from __future__ import annotations

from spectrafit.adapters.component_conversion import LegacyModelSpec
from spectrafit.adapters.component_conversion import legacy_list_to_components
from spectrafit.models.peak_models import Component
from spectrafit.models.registry import REGISTRY


type LegacyConstraintScalar = float | int | bool | str | None
type JsonScalar = float | int | bool | str | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


LegacyParameterConstraint = dict[str, LegacyConstraintScalar]
LegacyModelParameters = dict[str, LegacyParameterConstraint]
InitialModelLike = list[LegacyModelSpec] | list[Component]


def list2dict(
    peak_list: list[LegacyModelSpec],
) -> dict[str, dict[str, LegacyModelSpec]]:
    """Convert the list of peaks to dictionary.

    Args:
        peak_list: List of dictionaries with the initial fitting parameters for the
            peaks.  Each dict maps a model name to its parameter constraints.

    Returns:
        dict: Dictionary with the initial fitting parameters for the peaks, keyed
            under ``"peaks"`` and indexed by 1-based string ordinals.

    """
    peaks_dict: dict[str, dict[str, LegacyModelSpec]] = {"peaks": {}}
    for i, peak in enumerate(peak_list, start=1):
        model_name = next(iter(peak))
        if model_name in REGISTRY:
            peaks_dict["peaks"][f"{i}"] = peak
    return peaks_dict


def list2components(peak_list: list[LegacyModelSpec]) -> list[Component]:
    """Convert legacy notebook peak-list specs into typed v2 components.

    Delegates to :func:`~spectrafit.adapters.component_conversion.legacy_list_to_components`,
    which is the canonical ingress for all legacy-to-Component conversion.

    Args:
        peak_list: Legacy initial model list from notebook inputs.

    Returns:
        list[Component]: Validated component models accepted by
            ``UnifiedFittingConfig`` and notebook export bridges.
    """
    return legacy_list_to_components(peak_list)


def normalize_components(initial_model: InitialModelLike) -> list[Component]:
    """Normalize notebook initial-model inputs into canonical typed components.

    Args:
        initial_model: Legacy notebook specs or canonical typed components.

    Returns:
        list[Component]: Deep-copied canonical typed components.
    """
    if not initial_model:
        return []
    typed_components: list[Component] = []
    legacy_specs: list[LegacyModelSpec] = []
    for item in initial_model:
        if isinstance(item, Component):
            typed_components.append(item.model_copy(deep=True))
        else:
            legacy_specs.append(item)

    if typed_components and legacy_specs:
        msg = "initial_model must contain either typed components or legacy specs, not both."
        raise TypeError(msg)
    if typed_components:
        return typed_components
    return list2components(legacy_specs)


def components2legacy_specs(components: list[Component]) -> list[LegacyModelSpec]:
    """Project typed components to the legacy notebook/report initial-model shape.

    Args:
        components: Canonical typed component models.

    Returns:
        list[LegacyModelSpec]: Notebook/report boundary payload shaped as
            ``[{model_name: {parameter_name: constraint_dict}}]``.
    """
    return [
        {
            component.model: component.model_dump(
                mode="json",
                include={"parameters"},
                exclude_unset=True,
            )["parameters"]
        }
        for component in components
    ]


def remove_none_type(d: JsonValue) -> JsonValue:
    """Remove None type from dictionary in a recursive fashion.

    1. Remove None type from each value in the dictionary
    2. Remove None type from each element in the list

    Args:
        d: Dictionary, list, or scalar to be cleaned of ``None`` values.

    Returns:
        dict | list | scalar: Input with all ``None`` values removed recursively.

    """
    if isinstance(d, dict):
        return {k: remove_none_type(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [remove_none_type(v) for v in d if v is not None]
    return d

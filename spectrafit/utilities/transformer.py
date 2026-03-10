"""Transformer functions for the SpectraFit."""

from __future__ import annotations

from typing import TypedDict

from spectrafit.models.registry import REGISTRY


type LegacyConstraintScalar = float | int | bool | str | None
type JsonScalar = float | int | bool | str | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


LegacyParameterConstraint = dict[str, LegacyConstraintScalar]
LegacyModelParameters = dict[str, LegacyParameterConstraint]
LegacyModelSpec = dict[str, LegacyModelParameters]


class NotebookComponentSpec(TypedDict):
    """Legacy notebook component entry converted to v2 component schema."""

    id: str
    model: str
    parameters: LegacyModelParameters


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


def list2components(peak_list: list[LegacyModelSpec]) -> list[NotebookComponentSpec]:
    """Convert legacy notebook peak-list specs into v2 ``components`` entries.

    Args:
        peak_list: Legacy initial model list from notebook inputs.

    Returns:
        list[NotebookComponentSpec]: v2 component dictionaries accepted by
            ``UnifiedFittingConfig``.
    """
    components: list[NotebookComponentSpec] = []
    for i, peak in enumerate(peak_list, start=1):
        model_name = next(iter(peak))
        if model_name not in REGISTRY:
            continue
        parameters = peak[model_name]
        components.append(
            {
                "id": f"p{i}",
                "model": model_name,
                "parameters": parameters,
            }
        )
    return components


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

"""Transformer functions for the SpectraFit."""

from __future__ import annotations

from typing import TYPE_CHECKING

from spectrafit.models.registry import REGISTRY


if TYPE_CHECKING:
    from spectrafit.models.types import PeakModelSpec
    from spectrafit.models.types import PeaksDict


def list2dict(
    peak_list: list[PeakModelSpec],
) -> dict[str, PeaksDict]:
    """Convert the list of peaks to dictionary.

    Args:
        peak_list: List of dictionaries with the initial fitting parameters for the
            peaks.  Each dict maps a model name to its parameter constraints.

    Returns:
        dict: Dictionary with the initial fitting parameters for the peaks, keyed
            under ``"peaks"`` and indexed by 1-based string ordinals.

    """
    peaks_dict: dict[str, PeaksDict] = {"peaks": {}}
    for i, peak in enumerate(peak_list, start=1):
        model_name = next(iter(peak))
        if model_name in REGISTRY:
            peaks_dict["peaks"][f"{i}"] = peak
    return peaks_dict


def remove_none_type(d: object) -> dict[str, object] | list[object] | object:
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

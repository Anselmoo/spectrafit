"""Transformer functions for the SpectraFit."""

from __future__ import annotations

from typing import Any

from spectrafit.api.models_model import DistributionModelAPI


def list2dict(
    peak_list: list[dict[str, dict[str, dict[str, Any]]]],
) -> dict[str, dict[str, dict[str, Any]]]:
    """Convert the list of peaks to dictionary.

    Args:
        peak_list (List[Dict[str, Dict[str, Dict[str, Any]]]]): List of dictionary
             with the initial fitting parameters for the peaks.

    Returns:
        Dict[str, Dict[str, Dict[str, Any]]]: Dictionary with the initial fitting
             parameters for the peaks.

    """
    peaks_dict: dict[str, dict[str, dict[str, Any]]] = {"peaks": {}}
    for i, peak in enumerate(peak_list, start=1):
        if next(iter(peak)) in DistributionModelAPI().__dict__:
            peaks_dict["peaks"][f"{i}"] = peak
    return peaks_dict


def remove_none_type(d: Any) -> dict[str, Any] | list[Any]:
    """Remove None type from dictionary in a recursive fashion.

    1. Remove None type from each value in the dictionary
    2. Remove None type from each element in the list

    Args:
        d (Any): Dictionary to be cleaned.

    Returns:
        Union[Dict[str, Any], List[Any]]: Dictionary without None type.

    """
    if isinstance(d, dict):
        return {k: remove_none_type(v) for k, v in d.items() if v is not None}
    if isinstance(d, list):
        return [remove_none_type(v) for v in d if v is not None]
    return d

"""Test of the jupyter plugin."""

from __future__ import annotations

from typing import Any

import pytest

from spectrafit.utilities.transformer import list2dict
from spectrafit.utilities.transformer import remove_none_type


@pytest.fixture
def reference_dict() -> dict[str, dict[str, Any]]:
    """Check reference dictionary.

    Returns:
        Dict[str, Dict[str, Any]]: Reference dictionary of two peaks.

    """
    return {
        "peaks": {
            "1": {
                "pseudovoigt": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                    "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                    "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
                },
            },
            "2": {
                "pseudovoigt": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                    "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                    "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
                },
            },
        },
    }


@pytest.fixture
def reference_list() -> list[dict[str, Any]]:
    """Check reference list dictionary.

    Returns:
        Dict[str, Dict[str, Any]]: Reference list of dictionaries of two peaks.

    """
    return [
        {
            "pseudovoigt": {
                "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
            },
        },
        {
            "pseudovoigt": {
                "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
            },
        },
    ]


def test_converter(
    reference_list: list[dict[str, Any]],
    reference_dict: dict[str, dict[str, Any]],
) -> None:
    """Test of the converter from list to dict.

    Args:
        reference_list (List[Dict[str, Any]]): Reference list of dictionaries of
             two peaks.
        reference_dict (Dict[str, Dict[str, Any]]): Reference dictionary of two peaks.

    """
    assert list2dict(reference_list) == reference_dict


def test_remove_none_type() -> None:
    """Test remove_none_type function."""
    d = {"a": None, "b": {"c": None, "d": {"e": None, "f": [1, None]}}}
    assert remove_none_type(d) == {"b": {"d": {"f": [1]}}}

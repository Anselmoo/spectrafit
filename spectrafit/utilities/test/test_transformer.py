"""Test of the jupyter plugin."""
from typing import Any
from typing import Dict
from typing import List

import pytest

from spectrafit.utilities.transformer import list2dict


@pytest.fixture
def reference_dict() -> Dict[str, Dict[str, Any]]:
    """Reference dictionary.

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
                }
            },
            "2": {
                "pseudovoigt": {
                    "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                    "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                    "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
                }
            },
        },
    }


@pytest.fixture
def reference_list() -> List[Dict[str, Any]]:
    """Reference list dictionary.

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
            }
        },
        {
            "pseudovoigt": {
                "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
                "center": {"max": 2, "min": -2, "vary": True, "value": 0},
                "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
                "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
            }
        },
    ]


def test_converter(
    reference_list: List[Dict[str, Any]], reference_dict: Dict[str, Dict[str, Any]]
) -> None:
    """Test of the converter from list to dict.

    Args:
        reference_list (List[Dict[str, Any]]): Reference list of dictionaries of
             two peaks.
        reference_dict (Dict[str, Dict[str, Any]]): Reference dictionary of two peaks.
    """
    assert list2dict(reference_list) == reference_dict

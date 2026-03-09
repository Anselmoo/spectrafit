"""Unit tests for ``spectrafit.utilities.transformer`` helpers."""

from __future__ import annotations

import pytest

from spectrafit.utilities.transformer import list2components
from spectrafit.utilities.transformer import list2dict
from spectrafit.utilities.transformer import remove_none_type


_LEGACY_PEAKS = [
    {
        "gaussian": {
            "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
        }
    },
    {"not-a-model": {"amplitude": {"value": 0.5}}},
]


@pytest.mark.unit
def test_list2dict_filters_unknown_models() -> None:
    """Only registered model names are emitted in the legacy ``peaks`` mapping."""
    peaks = list2dict(_LEGACY_PEAKS)
    assert peaks == {"peaks": {"1": _LEGACY_PEAKS[0]}}


@pytest.mark.unit
def test_list2components_builds_component_entries() -> None:
    """Legacy peak rows are transformed into v2-style component dictionaries."""
    components = list2components(_LEGACY_PEAKS)
    assert components == [
        {
            "id": "p1",
            "model": "gaussian",
            "parameters": _LEGACY_PEAKS[0]["gaussian"],
        }
    ]


@pytest.mark.unit
def test_remove_none_type_recursively_prunes_none_values() -> None:
    """Nested dictionaries and lists have ``None`` values removed recursively."""
    cleaned = remove_none_type(
        {
            "a": 1,
            "b": None,
            "c": [{"x": None, "y": 2.0}, None],
            "d": {"keep": "ok", "drop": None},
        }
    )
    assert cleaned == {"a": 1, "c": [{"y": 2.0}], "d": {"keep": "ok"}}

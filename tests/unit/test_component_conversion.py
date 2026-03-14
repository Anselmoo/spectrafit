"""Unit tests for the canonical legacy-to-Component conversion boundary.

Covers :mod:`spectrafit.adapters.component_conversion` directly and verifies
that both :mod:`spectrafit.adapters.v1_config_migration` and
:mod:`spectrafit.utilities.transformer` correctly delegate to it.
"""

from __future__ import annotations

import pytest

from spectrafit.adapters.component_conversion import legacy_list_to_components
from spectrafit.adapters.component_conversion import spec_to_component
from spectrafit.models.peak_models import Component


# ---------------------------------------------------------------------------
# spec_to_component — atomic primitive
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_spec_to_component_constructs_typed_component() -> None:
    """spec_to_component wraps Component.model_validate consistently."""
    params = {"amplitude": {"value": 1.0, "min": 0.0, "max": 2.0, "vary": True}}
    component = spec_to_component("p1", "gaussian", params)

    assert isinstance(component, Component)
    assert component.id == "p1"
    assert component.model == "gaussian"
    assert component.parameters["amplitude"].value == pytest.approx(1.0)


@pytest.mark.unit
def test_spec_to_component_accepts_nested_parameters() -> None:
    """Deep parameter dicts are passed through to Component.model_validate."""
    params = {
        "amplitude": {"value": 2.5, "vary": False},
        "center": {"value": 0.0},
        "fwhmg": {"value": 0.5},
    }
    component = spec_to_component("peak_a", "gaussian", params)
    assert component.parameters["amplitude"].value == pytest.approx(2.5)
    assert component.parameters["amplitude"].vary is False


@pytest.mark.unit
def test_spec_to_component_raises_on_unknown_model() -> None:
    """Component.model_validate rejects unregistered model names."""
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        spec_to_component("p1", "not_a_real_model", {})


# ---------------------------------------------------------------------------
# legacy_list_to_components — notebook spec converter
# ---------------------------------------------------------------------------


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
def test_legacy_list_to_components_filters_unknown_models() -> None:
    """Entries with unregistered model names are silently skipped."""
    components = legacy_list_to_components(_LEGACY_PEAKS)
    assert len(components) == 1
    assert components[0].id == "p1"
    assert components[0].model == "gaussian"


@pytest.mark.unit
def test_legacy_list_to_components_assigns_sequential_ids() -> None:
    """Component IDs follow ``p{1-based-index}`` regardless of skipped entries."""
    specs = [
        {
            "lorentzian": {
                "amplitude": {"value": 1.0},
                "center": {"value": 0.0},
                "fwhml": {"value": 0.5},
            }
        },
        {
            "gaussian": {
                "amplitude": {"value": 2.0},
                "center": {"value": 1.0},
                "fwhmg": {"value": 0.3},
            }
        },
    ]
    components = legacy_list_to_components(specs)
    assert [c.id for c in components] == ["p1", "p2"]


@pytest.mark.unit
def test_legacy_list_to_components_empty_input_returns_empty_list() -> None:
    """Empty peak list produces empty component list without error."""
    assert legacy_list_to_components([]) == []


@pytest.mark.unit
def test_legacy_list_to_components_all_unknown_returns_empty() -> None:
    """All-unknown model list produces an empty result."""
    specs = [{"bad_model": {"param": {"value": 1.0}}}]
    assert legacy_list_to_components(specs) == []


# ---------------------------------------------------------------------------
# Delegation proof — transformer.list2components delegates here
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_transformer_list2components_delegates_to_canonical_conversion() -> None:
    """transformer.list2components must delegate to legacy_list_to_components."""
    from spectrafit.utilities.transformer import list2components

    transformer_result = list2components(_LEGACY_PEAKS)
    canonical_result = legacy_list_to_components(_LEGACY_PEAKS)

    assert transformer_result == canonical_result


# ---------------------------------------------------------------------------
# Delegation proof — v1_config_migration uses spec_to_component
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_v1_migration_component_ids_match_spec_to_component() -> None:
    """_migrate_legacy_components produces the same component as spec_to_component."""
    from spectrafit.adapters.v1_config_migration import migrate_v1_payload

    payload = {
        "peaks": {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2.0},
                }
            }
        }
    }
    migrated = migrate_v1_payload(payload)
    direct = spec_to_component(
        "p1",
        "gaussian",
        {
            "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
            "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2.0},
        },
    )

    assert migrated["components"][0]["id"] == direct.id
    assert migrated["components"][0]["model"] == direct.model

"""Unit tests for legacy v1 config migration helpers."""

from __future__ import annotations

import pytest

from spectrafit.adapters.unified_config_input import normalize_unified_config_input
from spectrafit.adapters.v1_config_migration import is_legacy_v1_payload
from spectrafit.adapters.v1_config_migration import migrate_v1_payload
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode


_MINIMAL_COMPONENTS = [
    {
        "id": "p1",
        "model": "gaussian",
        "parameters": {
            "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
            "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
            "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2.0},
        },
    }
]


@pytest.mark.unit
def test_is_legacy_v1_payload_detects_root_peaks_shape() -> None:
    payload = {"peaks": {"1": {"gaussian": {"amplitude": {"value": 1.0}}}}}

    assert is_legacy_v1_payload(payload) is True


@pytest.mark.unit
def test_migrate_v1_payload_converts_root_peaks_to_components() -> None:
    payload = {
        "infile": "data.csv",
        "peaks": {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2.0},
                }
            }
        },
    }

    migrated = migrate_v1_payload(payload)

    assert migrated["data"] == {"infile": "data.csv"}
    assert migrated["components"][0]["id"] == "p1"
    assert migrated["components"][0]["model"] == "gaussian"


@pytest.mark.unit
def test_normalize_unified_config_input_warns_on_legacy_shapes() -> None:
    payload = {
        "global": 1,
        "components": _MINIMAL_COMPONENTS,
    }

    with pytest.warns(
        FutureWarning, match="Legacy v1 configuration shapes are deprecated"
    ):
        normalized = normalize_unified_config_input(payload)

    assert normalized["context"]["mode"] == "global"


@pytest.mark.unit
def test_normalize_unified_config_input_converts_column_list_to_mapping() -> None:
    normalized = normalize_unified_config_input(
        {
            "components": _MINIMAL_COMPONENTS,
            "column": ["energy", 1],
        }
    )

    assert normalized["column"] == {"x": "energy", "y": "1"}


@pytest.mark.unit
def test_normalize_unified_config_input_migrates_legacy_peaks_payload() -> None:
    payload = {
        "infile": "data.csv",
        "global": 1,
        "peaks": {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2.0},
                }
            }
        },
    }

    with pytest.warns(
        FutureWarning, match="Legacy v1 configuration shapes are deprecated"
    ):
        normalized = normalize_unified_config_input(payload)

    assert normalized["data"] == {"infile": "data.csv"}
    assert normalized["context"]["mode"] == "global"
    assert normalized["components"][0]["id"] == "p1"


@pytest.mark.unit
def test_normalize_unified_config_input_serializes_typed_context_to_mapping() -> None:
    context = FittingContext(mode=FittingMode.GLOBAL, n_datasets=3)
    normalized = normalize_unified_config_input(
        {
            "components": _MINIMAL_COMPONENTS,
            "context": context,
        }
    )

    assert normalized["context"] == context.model_dump(mode="json", exclude_none=True)


@pytest.mark.unit
def test_normalize_unified_config_input_adapts_v2_data_block_from_canonical_data_config() -> (
    None
):
    normalized = normalize_unified_config_input(
        {
            "components": _MINIMAL_COMPONENTS,
            "data": {
                "infile": "data.csv",
                "x_col": 0,
                "y_col": 1,
                "separator": ",",
                "header": None,
                "decimal": ",",
                "comment": "#",
            },
        }
    )

    assert normalized["data"] == {
        "infile": "data.csv",
        "x_col": "0",
        "y_col": "1",
        "separator": ",",
        "header": None,
        "decimal": ",",
        "comment": "#",
    }
    assert normalized["column"] == {"x": "0", "y": "1"}


@pytest.mark.unit
def test_normalize_unified_config_input_adapts_v2_solver_block_to_canonical_models() -> (
    None
):
    normalized = normalize_unified_config_input(
        {
            "components": _MINIMAL_COMPONENTS,
            "solver": {
                "method": "least_squares",
                "max_nfev": 200,
                "nan_policy": "omit",
                "calc_covar": False,
                "xtol": 1e-6,
                "ftol": 1e-7,
            },
        }
    )

    assert normalized["minimizer"] == {"nan_policy": "omit", "calc_covar": False}
    assert normalized["optimizer"] == {
        "method": "least_squares",
        "max_nfev": 200,
        "xtol": 1e-6,
        "ftol": 1e-7,
    }


@pytest.mark.unit
def test_unified_fitting_config_from_legacy_dict_accepts_legacy_v1_payload() -> None:
    payload = {
        "infile": "data.csv",
        "global": 1,
        "peaks": {
            "1": {
                "gaussian": {
                    "amplitude": {"value": 1.0, "vary": True, "min": 0.0, "max": 2.0},
                    "center": {"value": 0.0, "vary": True, "min": -2.0, "max": 2.0},
                    "fwhmg": {"value": 0.5, "vary": True, "min": 0.01, "max": 2.0},
                }
            }
        },
    }

    with pytest.warns(
        FutureWarning, match="Legacy v1 configuration shapes are deprecated"
    ):
        config = UnifiedFittingConfig.from_legacy_dict(payload)

    assert config.context.mode.value == "global"
    assert config.data is not None
    assert config.data.infile.name == "data.csv"
    assert config.components[0].id == "p1"

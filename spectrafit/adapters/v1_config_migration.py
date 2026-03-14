"""Frozen compatibility helpers for migrating legacy v1 config payloads.

These functions quarantine the historical v1 payload shapes at an explicit
adapter boundary so canonical v2 runtime models can stay typed and focused.
Keep this module limited to compatibility translation; new config behavior
belongs in the v2 model layer instead of this legacy seam.
"""

from __future__ import annotations

from collections.abc import Mapping

from spectrafit.adapters.component_conversion import spec_to_component


type RawPayload = Mapping[str, object]
type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]


def _coerce_object_mapping(value: object) -> RawPayload | None:
    """Return a string-keyed object mapping when the input is mapping-like."""
    if not isinstance(value, Mapping):
        return None
    return {str(key): item for key, item in value.items()}


def is_legacy_v1_payload(payload: RawPayload) -> bool:
    """Return whether a config payload uses a quarantined legacy v1 shape."""
    if "peaks" in payload:
        return True
    fitting_block = _coerce_object_mapping(payload.get("fitting"))
    if fitting_block is not None:
        parameters_block = _coerce_object_mapping(fitting_block.get("parameters"))
        if parameters_block is not None and "peaks" in parameters_block:
            return True
    return False


def _normalize_component_id(raw_key: str) -> str:
    """Normalize legacy peak keys into canonical component ids."""
    cleaned = raw_key.strip()
    if cleaned.startswith("p"):
        return cleaned
    if cleaned.isdigit():
        return f"p{cleaned}"
    return cleaned


def _to_json_value(value: object) -> JsonValue:
    """Copy a legacy payload value into a JSON-shaped structure."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_json_value(item) for item in value]

    msg = f"Legacy v1 payload contains unsupported value type: {type(value).__name__}."
    raise TypeError(msg)


def _to_json_object(payload: Mapping[str, object]) -> JsonObject:
    """Copy a mapping into a JSON-shaped object."""
    return {str(key): _to_json_value(value) for key, value in payload.items()}


def _extract_legacy_peaks(payload: RawPayload) -> Mapping[str, JsonValue]:
    """Extract the legacy peaks mapping from a v1 payload."""
    raw_peaks = _coerce_object_mapping(payload.get("peaks"))
    if raw_peaks is not None:
        return _to_json_object(raw_peaks)

    fitting_block = _coerce_object_mapping(payload.get("fitting"))
    if fitting_block is not None:
        parameters_block = _coerce_object_mapping(fitting_block.get("parameters"))
        if parameters_block is not None:
            nested_peaks = _coerce_object_mapping(parameters_block.get("peaks"))
            if nested_peaks is not None:
                return _to_json_object(nested_peaks)

    msg = "Legacy v1 payload must contain a 'peaks' mapping."
    raise ValueError(msg)


def _migrate_legacy_components(peaks: Mapping[str, JsonValue]) -> list[JsonObject]:
    """Convert legacy peak specs into canonical v2 component payloads."""
    migrated: list[JsonObject] = []
    for raw_key, raw_spec in peaks.items():
        if not isinstance(raw_spec, Mapping) or len(raw_spec) != 1:
            msg = f"Legacy peak '{raw_key}' must map exactly one model name to parameters."
            raise ValueError(msg)

        model_name, raw_parameters = next(iter(raw_spec.items()))
        object_parameters = _coerce_object_mapping(raw_parameters)
        if not isinstance(model_name, str) or object_parameters is None:
            msg = f"Legacy peak '{raw_key}' must contain a string model name and mapping payload."
            raise TypeError(msg)

        component = spec_to_component(
            _normalize_component_id(str(raw_key)),
            model_name,
            _to_json_object(object_parameters),
        )
        migrated.append(component.model_dump(mode="json", exclude_none=True))
    return migrated


def migrate_v1_payload(payload: RawPayload) -> JsonObject:
    """Migrate a legacy v1 payload into canonical v2 config shape."""
    legacy = dict(payload)
    migrated: JsonObject = {}

    if data_block := _coerce_object_mapping(legacy.get("data")):
        migrated["data"] = _to_json_object(data_block)
    elif infile := legacy.get("infile"):
        migrated["data"] = {"infile": _to_json_value(infile)}

    for key in (
        "column",
        "preprocessing",
        "optimizer",
        "minimizer",
        "confidence_interval",
        "global_fitting",
        "context",
        "global",
        "global_",
    ):
        value = legacy.get(key)
        if value is not None:
            migrated[key] = _to_json_value(value)

    fitting_block = _coerce_object_mapping(legacy.get("fitting"))
    if fitting_block is not None:
        for key in (
            "optimizer",
            "minimizer",
            "preprocessing",
            "column",
            "global",
            "global_",
        ):
            if key not in migrated and key in fitting_block:
                migrated[key] = _to_json_value(fitting_block[key])

    migrated["components"] = _to_json_value(
        _migrate_legacy_components(_extract_legacy_peaks(legacy))
    )
    return migrated


__all__ = ["is_legacy_v1_payload", "migrate_v1_payload"]

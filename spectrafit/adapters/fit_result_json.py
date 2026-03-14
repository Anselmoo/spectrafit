"""JSON persistence adapter for canonical ``FitResult`` models.

This module owns the legacy JSON boundary for persisted fit results so that the
canonical model file stays focused on typed domain data. Compatibility coercion
required when reading older payloads lives here rather than in
``spectrafit.models.results.fit_result``.
"""

from __future__ import annotations

import json

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import model_validator

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import FitResult


type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]
type JsonObject = dict[str, JsonValue]


class PersistedFitResult(FitResult):
    """Typed JSON payload model for persisted fit results."""

    @model_validator(mode="before")
    @classmethod
    def normalize_legacy_payload(cls, data: object) -> object:
        """Coerce older persisted payloads into the canonical result shape."""
        if not isinstance(data, Mapping):
            return data

        payload: dict[str, Any] = {str(key): value for key, value in data.items()}
        global_fitting = payload.get("global_fitting")
        if isinstance(global_fitting, bool | int):
            payload["global_fitting"] = (
                FittingMode.GLOBAL.value
                if global_fitting
                else FittingMode.STANDARD.value
            )
        return payload


def serialize_fit_result(fit_result: FitResult) -> JsonObject:
    """Project a canonical result model into a JSON-ready mapping."""
    return fit_result.model_dump(mode="json")


def deserialize_fit_result(
    data: Mapping[str, Any] | PersistedFitResult,
) -> FitResult:
    """Load a canonical result model from a JSON-style mapping.

    This adapter accepts older payloads that still use integer or boolean
    ``global_fitting`` values and normalizes them before validation.
    """
    persisted = (
        data
        if isinstance(data, PersistedFitResult)
        else PersistedFitResult.model_validate(
            {str(key): value for key, value in data.items()}
        )
    )
    return FitResult.model_validate(persisted.model_dump(mode="python"))


def save_fit_result(fit_result: FitResult, path: Path | str) -> None:
    """Write a canonical result model to a JSON file."""
    Path(path).write_text(
        json.dumps(serialize_fit_result(fit_result), indent=2),
        encoding="utf-8",
    )


def load_fit_result(path: Path | str) -> FitResult:
    """Read a persisted fit result JSON payload into a canonical model."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        msg = "Fit result JSON payload must decode to an object."
        raise TypeError(msg)
    return deserialize_fit_result(raw)

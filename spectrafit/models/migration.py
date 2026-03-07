"""v1 → v2 input format migration helpers.

These functions normalise legacy SpectraFit v1.x input dictionaries into the
flat form expected by :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`
before Pydantic field validation runs.

The canonical v2 input format uses ``[[components]]`` TOML array-of-tables —
see ``prototype/input.toml``.  These helpers exist solely for backward
compatibility and will be superseded by the ``scripts/migrate_v1_to_v2.py``
tool in a future release.

!!! note "Scope"
    Only v1 → v2 migration logic lives here.  The ``[[components]]`` → internal
    representation transform (``_migrate_v2_format``) stays in
    :mod:`spectrafit.core.fitting_config` because it is part of the canonical
    input pipeline.
"""

from __future__ import annotations


# Keys that belong in the [data] section of a v2 config.
DATA_KEYS: frozenset[str] = frozenset(
    {"infile", "separator", "header", "decimal", "comment"},
)

# Keys that belong in the [preprocessing] section of a v2 config.
PREPROC_KEYS: frozenset[str] = frozenset(
    {"energy_start", "energy_stop", "smooth", "shift", "oversampling"},
)


def _migrate_v1_full_wrapper(data: dict[str, object]) -> dict[str, object]:
    """Unwrap ``{"fitting": {...}, "settings": {...}}`` (v1 Pattern 1).

    Args:
        data: Raw input dict containing a top-level ``fitting`` key.

    Returns:
        dict: Flattened dict with peaks/minimizer/optimizer at root.
    """
    fitting = data["fitting"]
    result: dict[str, object] = {}
    if "settings" in data:
        settings = data["settings"]
        if isinstance(settings, dict):
            result |= settings
    if isinstance(fitting, dict):
        if "peaks" in fitting:
            result["peaks"] = fitting["peaks"]
        params = fitting.get("parameters", {})
        if isinstance(params, dict):
            for key in ("minimizer", "optimizer"):
                if key in params:
                    result[key] = params[key]
    result.update({k: v for k, v in data.items() if k not in ("fitting", "settings")})
    return result


def _migrate_v1_inner(data: dict[str, object]) -> dict[str, object]:
    """Unwrap ``{"parameters": {...}, "peaks": {...}}`` (v1 Pattern 2).

    Args:
        data: Raw input dict with a ``parameters`` wrapper around
            minimizer/optimizer keys.

    Returns:
        dict: Flattened dict with minimizer/optimizer hoisted to root.
    """
    params = data["parameters"]
    result = {k: v for k, v in data.items() if k != "parameters"}
    if isinstance(params, dict):
        for key in ("minimizer", "optimizer"):
            if key in params:
                result[key] = params[key]
    return result


def _coerce_flat_data_keys(data: dict[str, object]) -> dict[str, object]:
    """Coerce flat data keys into a ``data`` sub-dict.

    Args:
        data: Mutable normalised dict (v1 or v2 flat form).

    Returns:
        dict: Updated dict, potentially with a new ``data`` key.
    """
    if isinstance(data.get("data"), dict):
        return data
    flat_data: dict[str, object] = {}
    for k in list(data):
        if k in DATA_KEYS:
            flat_data[k] = data.pop(k)
    if flat_data:
        col = data.get("column", [])
        if isinstance(col, list) and len(col) >= 2:  # noqa: PLR2004
            flat_data.setdefault("x_col", str(col[0]))
            flat_data.setdefault("y_col", str(col[1]))
        data["data"] = flat_data
    return data


def _coerce_flat_preproc_keys(data: dict[str, object]) -> dict[str, object]:
    """Coerce flat preprocessing keys into a ``preprocessing`` sub-dict.

    Args:
        data: Mutable normalised dict.

    Returns:
        dict: Updated dict, potentially with a new ``preprocessing`` key.
    """
    if isinstance(data.get("preprocessing"), dict):
        return data
    flat_preproc: dict[str, object] = {}
    for k in list(data):
        if k in PREPROC_KEYS:
            flat_preproc[k] = data.pop(k)
    if flat_preproc:
        data["preprocessing"] = flat_preproc
    return data


def migrate_v1_format(data: dict[str, object]) -> dict[str, object]:
    """Normalise a v1.x input dict to the form expected by UnifiedFittingConfig.

    Applies v1 unwrapping patterns in sequence, then coerces flat keys into
    the ``data`` / ``preprocessing`` sub-dicts.

    Args:
        data: Raw dict parsed from a v1 TOML/JSON file.

    Returns:
        dict: Normalised dict ready for UnifiedFittingConfig field validation.
    """
    if "fitting" in data:
        data = _migrate_v1_full_wrapper(data)
    elif "parameters" in data and "peaks" in data and "minimizer" not in data:
        data = _migrate_v1_inner(data)
    data = _coerce_flat_data_keys(data)
    return _coerce_flat_preproc_keys(data)

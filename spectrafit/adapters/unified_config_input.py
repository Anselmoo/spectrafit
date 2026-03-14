"""Typed parse-time adapter for canonical fitting configuration input."""

from __future__ import annotations

import warnings

from collections.abc import Mapping
from collections.abc import MutableMapping
from difflib import get_close_matches

from pydantic import ConfigDict
from pydantic import field_validator
from pydantic import model_validator

from spectrafit.adapters.v1_config_migration import is_legacy_v1_payload
from spectrafit.adapters.v1_config_migration import migrate_v1_payload
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import coerce_legacy_fitting_context
from spectrafit.models.fitting_context import coerce_legacy_fitting_mode
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig
from spectrafit.models.solver_config import SolverConfig


type RawConfigPayload = Mapping[str, object]
"""Read-only config payload accepted at the config input boundary."""


class V2DataBlock(DataConfig):
    """Thin parser for the optional v2 ``[data]`` block around ``DataConfig``."""

    model_config = ConfigDict(
        populate_by_name=True,
        extra="allow",  # intentional: parse-time adapter
    )

    infile: str | None = None

    @field_validator("x_col", "y_col", mode="before")
    @classmethod
    def _coerce_column_names(cls, value: object) -> str:
        """Accept integer column identifiers at the adapter boundary."""
        return str(value)


class V2SolverBlock(SolverConfig):
    """Thin parser for the optional v2 ``[solver]`` block around ``SolverConfig``."""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _normalize_flat_solver_block(cls, value: object) -> object:
        """Accept flat v2 solver fields and map them onto canonical sub-models."""
        if not isinstance(value, Mapping):
            return value
        return _normalize_solver_block_mapping(value, allow_optimizer_passthrough=True)


def _normalize_solver_block_mapping(
    value: Mapping[str, object],
    *,
    allow_optimizer_passthrough: bool,
) -> Mapping[str, object]:
    """Normalize flat solver keys into canonical minimizer/optimizer mappings."""
    if "minimizer" in value or "optimizer" in value:
        return value

    minimizer_fields = set(MinimizerConfig.model_fields)
    optimizer_fields = set(OptimizerConfig.model_fields)
    declared_fields = minimizer_fields | optimizer_fields
    minimizer: dict[str, object] = {}
    optimizer: dict[str, object] = {}
    for key, item in value.items():
        if key in minimizer_fields:
            minimizer[key] = item
            continue
        if key in optimizer_fields:
            optimizer[key] = item
            continue
        typo_target = get_close_matches(key, declared_fields, n=1, cutoff=0.85)
        if typo_target:
            msg = f"Unknown flat solver field: {key}. Did you mean {typo_target[0]}?"
            raise ValueError(msg)
        if not allow_optimizer_passthrough:
            msg = f"Unknown flat solver field: {key}"
            raise ValueError(msg)
        optimizer[key] = item
    return {"minimizer": minimizer, "optimizer": optimizer}


def _normalize_context_payload(data: MutableMapping[str, object]) -> None:
    """Own legacy context/global alias handling at the adapter boundary."""
    raw_context = data.get("context")
    raw_legacy_global = data.pop("global_", data.pop("global", None))
    legacy_global_provided = raw_legacy_global is not None

    if raw_context is not None:
        context = resolve_context_from_priority(raw_context, None)
        if legacy_global_provided:
            legacy_mode = coerce_legacy_fitting_mode(raw_legacy_global)
            if legacy_mode != context.mode:
                msg = "context and legacy global mode must agree"
                raise ValueError(msg)
        data["context"] = context.model_dump(mode="json", exclude_none=True)
        return

    if legacy_global_provided:
        data["context"] = resolve_context_from_priority(
            None, raw_legacy_global
        ).model_dump(
            mode="json",
            exclude_none=True,
        )


def resolve_column_pair(
    column: list[object] | tuple[object, ...] | None,
    default_x: str = "energy",
    default_y: str = "intensity",
) -> tuple[str, str]:
    """Resolve ``(x_col, y_col)`` from a column list or named fallbacks.

    This is the **canonical column-alias resolver** shared by the unified config
    ingress and the legacy args adapter.  Callers should not inline this logic.

    Args:
        column: Optional list/tuple ``[x, y]`` of column identifiers.  If
            ``None`` or has fewer than two elements the fallbacks are used.
        default_x: Fallback x-column name.  Defaults to ``"energy"``.
        default_y: Fallback y-column name.  Defaults to ``"intensity"``.

    Returns:
        A ``(x_col, y_col)`` pair of strings.

    Examples:
        >>> resolve_column_pair(["wavelength", 1])
        ('wavelength', '1')
        >>> resolve_column_pair(None)
        ('energy', 'intensity')
    """
    if isinstance(column, (list, tuple)) and len(column) >= 2:  # noqa: PLR2004
        return str(column[0]), str(column[1])
    return default_x, default_y


def resolve_context_from_priority(
    context: object | None,
    global_: object | None,
) -> FittingContext:
    """Resolve a :class:`FittingContext` from two optional legacy sources.

    Priority: explicit *context* wins over *global_*; when both are absent a
    default ``FittingContext(mode=STANDARD)`` is returned.  Conflict detection
    is **not** performed here — callers that need it (e.g. the config ingress)
    must check *before* calling this helper.

    Args:
        context: Optional context-like object (``FittingContext``, int, str, …).
        global_: Optional legacy global-flag-like object.

    Returns:
        FittingContext: Resolved fitting context.

    Examples:
        >>> resolve_context_from_priority(None, 0).mode.value
        'standard'
        >>> resolve_context_from_priority(None, 1).mode.value
        'global'
    """
    source = context if context is not None else (global_ if global_ is not None else 0)
    return coerce_legacy_fitting_context(source)


def _normalize_column_payload(data: MutableMapping[str, object]) -> None:
    """Translate legacy list-style column aliases into canonical mapping form."""
    raw_column = data.get("column")
    if isinstance(raw_column, (list, tuple)) and len(raw_column) >= 2:  # noqa: PLR2004
        x_col, y_col = resolve_column_pair(raw_column)
        data["column"] = {"x": x_col, "y": y_col}


def _normalize_v2_components_payload(
    data: RawConfigPayload,
    *,
    allow_optimizer_passthrough: bool,
) -> Mapping[str, object]:
    """Translate v2 ``[[components]]`` input into the canonical model payload."""
    normalized = dict(data)

    if "infile" in normalized:
        infile = normalized.pop("infile")
        data_block = normalized.get("data", {})
        if isinstance(data_block, Mapping):
            promoted_data_block = dict(data_block)
            if "infile" not in promoted_data_block:
                promoted_data_block["infile"] = infile
            normalized["data"] = promoted_data_block
        else:
            normalized["data"] = {"infile": infile}

    raw_data = normalized.get("data")
    if isinstance(raw_data, Mapping):
        data_block = V2DataBlock.model_validate(raw_data)
        normalized["data"] = data_block.model_dump(mode="json", exclude_unset=True)
        normalized.setdefault("column", {"x": data_block.x_col, "y": data_block.y_col})
    _normalize_column_payload(normalized)

    raw_solver = normalized.get("solver")
    if raw_solver is not None:
        if not isinstance(raw_solver, Mapping):
            msg = "Expected 'solver' to be a mapping"
            raise TypeError(msg)
        normalized.pop("solver")
        solver_block = V2SolverBlock.model_validate(
            _normalize_solver_block_mapping(
                raw_solver,
                allow_optimizer_passthrough=allow_optimizer_passthrough,
            )
        )
        normalized.setdefault(
            "minimizer",
            solver_block.minimizer.model_dump(mode="python", exclude_none=True),
        )
        normalized.setdefault(
            "optimizer",
            solver_block.optimizer.model_dump(mode="python", exclude_none=True),
        )

    for key in ("schema_version", "config_type"):
        normalized.pop(key, None)

    return normalized


def _collect_legacy_unified_config_aliases(data: RawConfigPayload) -> list[str]:
    """Return legacy ingress aliases that require explicit compatibility loading."""
    aliases: list[str] = []
    if is_legacy_v1_payload(data) or "fitting" in data:
        aliases.append("legacy v1 'peaks'/'fitting' payload")
    if "global_" in data or "global" in data:
        aliases.append("legacy 'global/global_' mode alias")
    if "infile" in data:
        aliases.append("root-level 'infile' alias")
    if isinstance(data.get("column"), list | tuple):
        aliases.append("list-style 'column' alias")
    return aliases


def normalize_strict_unified_config_input(
    data: RawConfigPayload,
) -> Mapping[str, object]:
    """Normalize only canonical v2 config input for strict ingress paths."""
    legacy_aliases = _collect_legacy_unified_config_aliases(data)
    if legacy_aliases:
        alias_list = ", ".join(legacy_aliases)
        msg = (
            "Legacy config aliases are not supported by strict "
            f"UnifiedFittingConfig validation: {alias_list}. "
            "Use UnifiedFittingConfig.from_legacy_dict() or "
            "UnifiedFittingConfig.from_legacy_file() for compatibility input."
        )
        raise ValueError(msg)

    normalized = dict(data)
    if isinstance(normalized.get("components"), list):
        return _normalize_v2_components_payload(
            normalized,
            allow_optimizer_passthrough=False,
        )
    return normalized


def normalize_unified_config_input(
    data: RawConfigPayload,
    *,
    allow_optimizer_passthrough: bool = True,
) -> Mapping[str, object]:
    """Normalize raw config input into the canonical ``UnifiedFittingConfig`` shape."""
    normalized = dict(data)
    legacy_v1_payload = is_legacy_v1_payload(normalized)
    legacy_fitting_provided = "fitting" in normalized
    legacy_global_provided = "global_" in normalized or "global" in normalized

    if legacy_v1_payload or legacy_fitting_provided or legacy_global_provided:
        warnings.warn(
            "Legacy v1 configuration shapes are deprecated; migrate to canonical "
            "v2 '[data]' / '[[components]]' configs. See docs/interface/migration-v2.md "
            "or use scripts/migrate_v1_config.py.",
            FutureWarning,
            stacklevel=3,
        )

    if legacy_v1_payload:
        normalized = migrate_v1_payload(normalized)

    _normalize_context_payload(normalized)

    if isinstance(normalized.get("components"), list):
        return _normalize_v2_components_payload(
            normalized,
            allow_optimizer_passthrough=allow_optimizer_passthrough,
        )

    _normalize_column_payload(normalized)
    return normalized


__all__ = [
    "RawConfigPayload",
    "normalize_strict_unified_config_input",
    "normalize_unified_config_input",
    "resolve_column_pair",
    "resolve_context_from_priority",
]

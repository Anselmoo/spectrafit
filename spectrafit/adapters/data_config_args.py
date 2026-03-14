"""Frozen compatibility adapter for canonical ``DataConfig`` models.

This module owns the legacy args-mapping ingress used by older callers so that
``spectrafit.models.data_config`` stays focused on typed model validation and
state. Treat this file as a quarantine boundary during the v2 transition: keep
new runtime parsing behavior in canonical typed surfaces instead of growing this
adapter.
"""

from __future__ import annotations

import pathlib  # noqa: TC003

from typing import TYPE_CHECKING

from pydantic import AliasChoices
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.adapters.unified_config_input import resolve_column_pair
from spectrafit.adapters.unified_config_input import resolve_context_from_priority
from spectrafit.models.data_config import DataConfig


if TYPE_CHECKING:
    from collections.abc import Mapping


class LegacyDataConfigArgs(BaseModel):
    """Typed compatibility payload for older data-loader argument shapes."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    infile: pathlib.Path
    x_col: str = "energy"
    y_col: str = "intensity"
    separator: str = r"\s+"
    header: int | str | None = None
    decimal: str = "."
    comment: str | None = None
    column: list[str | int] | tuple[str | int, ...] | None = None
    context: object | None = None
    legacy_global: object | None = Field(
        default=None,
        validation_alias=AliasChoices("global_", "global"),
    )


def data_config_from_args_dict(
    args: LegacyDataConfigArgs | Mapping[str, object],
) -> DataConfig:
    """Construct a canonical ``DataConfig`` from a legacy args mapping.

    Supports both the old ``column`` list format and the newer ``x_col`` /
    ``y_col`` keys so existing migration paths can stay explicit at the adapter
    boundary. This is a compatibility seam, not a canonical v2 runtime API.

    Column and context resolution delegates to
    :func:`~spectrafit.adapters.unified_config_input.resolve_column_pair` and
    :func:`~spectrafit.adapters.unified_config_input.resolve_context_from_priority`
    — the canonical shared ingress helpers — to avoid duplicating alias logic.
    """
    legacy_args = (
        args
        if isinstance(args, LegacyDataConfigArgs)
        else LegacyDataConfigArgs.model_validate(dict(args))
    )
    x_col, y_col = resolve_column_pair(
        legacy_args.column,
        default_x=str(legacy_args.x_col),
        default_y=str(legacy_args.y_col),
    )
    context = resolve_context_from_priority(
        legacy_args.context, legacy_args.legacy_global
    )
    return DataConfig(
        infile=legacy_args.infile,
        x_col=x_col,
        y_col=y_col,
        separator=legacy_args.separator,
        header=(
            int(str(legacy_args.header)) if legacy_args.header is not None else None
        ),
        decimal=legacy_args.decimal,
        comment=legacy_args.comment,
        context=context,
    )

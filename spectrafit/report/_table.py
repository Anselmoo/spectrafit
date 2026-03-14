"""Shared table hook for frozen report imports."""

from __future__ import annotations

import pandas as pd


def print_tabulate_df(df: pd.DataFrame, floatfmt: str = ".3f") -> None:
    """Retain the historical table-render hook without owning formatting logic.

    Note:
        This compatibility helper intentionally remains a no-op placeholder to
        preserve current user-visible behavior while keeping formatting ownership
        outside the legacy report package.

    Args:
        df: DataFrame to render.
        floatfmt: Floating-point format requested by the caller.
    """

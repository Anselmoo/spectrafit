"""Adapter-oriented boundary helpers for CLI, Jupyter, and API seams."""

from __future__ import annotations

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from spectrafit.adapters.preprocessing_boundary import NotebookPreprocessingProxy


_PREPROCESSING_EXPORTS = {
    "NotebookPreprocessingProxy",
    "notebook_boundary_columns",
    "preprocessing_from_boundary",
    "preprocessing_to_boundary",
}


def __getattr__(name: str) -> object:
    """Lazily expose preprocessing-boundary helpers without eager import cycles."""
    if name in _PREPROCESSING_EXPORTS:
        from spectrafit.adapters import preprocessing_boundary  # noqa: PLC0415

        return getattr(preprocessing_boundary, name)
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)


__all__ = [
    "NotebookPreprocessingProxy",
    "notebook_boundary_columns",
    "preprocessing_from_boundary",
    "preprocessing_to_boundary",
]

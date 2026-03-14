"""Boundary adapters for canonical notebook preprocessing ownership."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import PrivateAttr

from spectrafit.api.tools_model import DataPreProcessingAPI


if TYPE_CHECKING:
    from collections.abc import Callable

    from spectrafit.models.preprocessing_config import PreprocessingConfig


type NotebookBoundaryColumn = list[int | str]
"""Notebook/report compatibility column payload."""


class NotebookPreprocessingProxy(DataPreProcessingAPI):
    """Compatibility proxy that syncs DTO mutations into canonical ownership."""

    _sync_callback: Callable[[DataPreProcessingAPI], None] | None = PrivateAttr(
        default=None
    )
    _sync_enabled: bool = PrivateAttr(default=False)

    @classmethod
    def from_canonical(
        cls,
        preprocessing: PreprocessingConfig | None,
        *,
        column: NotebookBoundaryColumn,
        sync_callback: Callable[[DataPreProcessingAPI], None],
    ) -> NotebookPreprocessingProxy:
        """Project canonical preprocessing ownership into a writable proxy."""
        proxy = cls.model_validate(
            preprocessing_to_boundary(preprocessing, column=column).model_dump()
        )
        proxy.bind_sync(sync_callback)
        return proxy

    def bind_sync(self, sync_callback: Callable[[DataPreProcessingAPI], None]) -> None:
        """Attach the canonical write-back callback after proxy construction."""
        self._sync_callback = sync_callback
        self._sync_enabled = True

    def __setattr__(self, name: str, value: object) -> None:
        """Propagate public-field mutations back to the canonical owner."""
        super().__setattr__(name, value)
        if (
            name in type(self).model_fields
            and self._sync_enabled
            and self._sync_callback is not None
        ):
            self._sync_callback(
                DataPreProcessingAPI.model_validate(self.model_dump(mode="python"))
            )


def notebook_boundary_columns(
    x_column: str,
    y_column: str | list[str],
) -> NotebookBoundaryColumn:
    """Build the compatibility ``column`` payload for notebook/report DTOs."""
    return [x_column, *y_column] if isinstance(y_column, list) else [x_column, y_column]


def preprocessing_from_boundary(
    pre_processing: DataPreProcessingAPI,
) -> PreprocessingConfig:
    """Convert the compatibility DTO into canonical preprocessing ownership."""
    return pre_processing.to_preprocessing_config()


def preprocessing_to_boundary(
    preprocessing: PreprocessingConfig | None,
    *,
    column: NotebookBoundaryColumn,
) -> DataPreProcessingAPI:
    """Project canonical preprocessing config to the frozen notebook/report DTO."""
    return DataPreProcessingAPI.from_preprocessing_config(
        preprocessing,
        column=list(column),
    )


__all__ = [
    "NotebookBoundaryColumn",
    "NotebookPreprocessingProxy",
    "notebook_boundary_columns",
    "preprocessing_from_boundary",
    "preprocessing_to_boundary",
]

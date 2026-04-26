"""Tool boundary models built on canonical v2 config ownership.

Canonical definitions for solver and preprocessing state live in
``spectrafit.models``. This module keeps notebook/export boundary projections
close to the API layer without re-declaring runtime ownership here.
"""

from __future__ import annotations

from pydantic import Field

from spectrafit.models.column_names import ColumnNames as ColumnNamesAPI
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig


class DataPreProcessingAPI(PreprocessingConfig):
    """Compatibility preprocessing DTO layered on canonical config ownership."""

    column: list[int | str] = Field(
        min_length=1,
        default_factory=lambda: [0, 1],
        description="Column of the data.",
    )

    def to_preprocessing_config(self) -> PreprocessingConfig:
        """Project the compatibility DTO onto the canonical preprocessing model."""
        return PreprocessingConfig.model_validate(
            self.model_dump(mode="python", exclude={"column"})
        )

    @classmethod
    def from_preprocessing_config(
        cls,
        preprocessing: PreprocessingConfig | None,
        *,
        column: list[int | str],
    ) -> DataPreProcessingAPI:
        """Project canonical preprocessing ownership onto the DTO boundary."""
        canonical = (
            preprocessing if preprocessing is not None else PreprocessingConfig()
        )
        return cls(
            **canonical.model_dump(mode="python"),
            column=list(column),
        )


__all__ = [
    "ColumnNamesAPI",
    "DataPreProcessingAPI",
    "MinimizerConfig",
    "OptimizerConfig",
]

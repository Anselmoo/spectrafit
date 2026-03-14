"""Canonical column-name constants used across the fitting pipeline."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.naming import dataset_scoped_name


class ColumnNames(BaseModel):
    """Immutable column-name registry for fitting result DataFrames.

    These names are used consistently across preprocessing, postprocessing,
    and export to label energy, intensity, residual, and fit columns.

    Attributes:
        energy: Name of the independent variable (x-axis) column.
        intensity: Name of the observed intensity column.
        residual: Name of the fit residual column.
        fit: Name of the best-fit curve column.
    """

    model_config = ConfigDict(frozen=True)

    energy: str = Field(
        default="energy",
        description="Independent variable column name",
    )
    intensity: str = Field(
        default="intensity",
        description="Observed intensity column name",
    )
    residual: str = Field(default="residual", description="Fit residual column name")
    fit: str = Field(default="fit", description="Best-fit curve column name")

    @staticmethod
    def with_suffix(base: str, suffix: int | str | None = None) -> str:
        """Return a canonical column name with an optional suffix."""
        return base if suffix is None else dataset_scoped_name(base, suffix)

    def intensity_for_dataset(self, dataset_index: int | str | None = None) -> str:
        """Return the canonical intensity column for one global-fit dataset."""
        return self.with_suffix(self.intensity, dataset_index)

    def residual_for_dataset(self, dataset_index: int | str | None = None) -> str:
        """Return the canonical residual column for one global-fit dataset."""
        return self.with_suffix(self.residual, dataset_index)

    def fit_for_dataset(self, dataset_index: int | str | None = None) -> str:
        """Return the canonical fit column for one global-fit dataset."""
        return self.with_suffix(self.fit, dataset_index)

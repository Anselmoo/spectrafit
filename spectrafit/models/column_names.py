"""Canonical column-name constants used across the fitting pipeline."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


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

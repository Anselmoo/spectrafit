"""PreprocessResult — typed output of the preprocessing pipeline step."""

from __future__ import annotations

import pandas as pd  # noqa: TC002 — Pydantic resolves pd.DataFrame at runtime

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.split_frame import (
    SplitFrame,  # noqa: TC001 — Pydantic resolves at runtime
)


class PreprocessResult(BaseModel):
    """Typed result of the preprocessing pipeline step.

    Replaces the legacy ``tuple[pd.DataFrame, dict[str, Any]]`` return
    from :class:`~spectrafit.core.preprocessing.PreProcessing.__call__`.

    Attributes:
        df: Preprocessed DataFrame (energy range, shifted, oversampled, smoothed).
        data_statistic: Descriptive statistics of the *raw* input frame as a
            validated split-frame model.

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame = Field(..., description="Preprocessed DataFrame")
    data_statistic: SplitFrame = Field(
        ..., description="Descriptive statistics of the raw input frame"
    )

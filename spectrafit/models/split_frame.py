"""Validated split-orient frame model shared across runtime and reporting."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


if TYPE_CHECKING:
    import pandas as pd


type SplitFrameCell = float | int | str | None
type SplitFrameAxis = int | str


class SplitFrame(BaseModel):
    """Pandas ``orient='split'`` payload with validation.

    This model is the canonical owner for statistical frame payloads that move across
    preprocessing, postprocessing, reporting, and notebook boundaries.
    """

    model_config = ConfigDict(extra="forbid")

    data: list[list[SplitFrameCell]] = Field(default_factory=list)
    index: list[SplitFrameAxis] = Field(default_factory=list)
    columns: list[SplitFrameAxis] = Field(default_factory=list)

    @classmethod
    def empty(cls) -> SplitFrame:
        """Return an empty split frame."""
        return cls()

    @classmethod
    def from_dataframe(cls, frame: pd.DataFrame) -> SplitFrame:
        """Build a split frame from a pandas DataFrame."""
        return cls.model_validate(frame.to_dict(orient="split"))

    def to_dataframe(self) -> pd.DataFrame:
        """Materialize the validated split payload as a pandas DataFrame."""
        import pandas as pd  # noqa: PLC0415

        return pd.DataFrame(data=self.data, index=self.index, columns=self.columns)

    def to_split_dict(
        self,
    ) -> dict[str, list[SplitFrameAxis] | list[list[SplitFrameCell]]]:
        """Return a JSON-ready split-orient mapping."""
        return {
            "data": self.data,
            "index": self.index,
            "columns": self.columns,
        }

    def __getitem__(
        self,
        key: str,
    ) -> list[list[SplitFrameCell]] | list[SplitFrameAxis]:
        """Provide compatibility-style keyed access for migration seams."""
        return getattr(self, key)

    def __contains__(self, key: object) -> bool:
        """Return whether *key* refers to one of the split-frame fields."""
        return key in {"data", "index", "columns"}

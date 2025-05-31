"""Definition of the data file model."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from pydantic import BaseModel
from pydantic import Field
from pydantic.functional_validators import field_validator


class DataFileAPI(BaseModel):
    """Definition of a data file."""

    skiprows: int | None = Field(
        default=None,
        description="Number of lines to skip at the beginning of the file.",
    )
    skipfooter: int = Field(
        ...,
        description="Number of lines to skip at the end of the file.",
    )
    delimiter: str = Field(
        ...,
        description="Delimiter to use.",
    )
    comment: str | None = Field(
        default=None,
        description="Comment marker to use.",
    )
    names: Callable[[Path, str], list[str] | None] | None = Field(
        default=None,
        description="Column names can be provided by list of strings or a function",
    )
    header: int | list[str] | None = Field(
        default=None,
        description="Column headers to use.",
    )
    file_suffixes: list[str] = Field(
        ...,
        description="File suffixes to use.",
    )

    @field_validator("delimiter")
    @classmethod
    def check_delimiter(cls, v: str) -> str | None:
        """Check if the delimiter is valid."""
        if v in {" ", "\t", ",", ";", "|", r"\s+"}:
            return v
        msg = f" {v} is not a valid delimiter."
        raise ValueError(msg)

    @field_validator("comment")
    @classmethod
    def check_comment(cls, v: str) -> str | None:
        """Check if the comment marker is valid."""
        if v is None or v in {"#", "%"}:
            return v
        msg = f" {v} is not a valid comment marker."
        raise ValueError(msg)

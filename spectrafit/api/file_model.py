"""Definition of the data file model."""

from pathlib import Path
from typing import Callable
from typing import List
from typing import Optional
from typing import Union

from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


class DataFileAPI(BaseModel):
    """Definition of a data file."""

    skiprows: Optional[int] = Field(
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
    comment: Optional[str] = Field(
        default=None,
        description="Comment marker to use.",
    )
    names: Optional[Callable[[Path, str], Optional[List[str]]]] = Field(
        default=None,
        description="Column names can be provided by list of strings or a function",
    )
    header: Optional[Union[int, List[str]]] = Field(
        default=None,
        description="Column headers to use.",
    )
    file_suffixes: List[str] = Field(
        ...,
        description="File suffixes to use.",
    )

    @validator("delimiter")
    @classmethod
    def check_delimiter(cls, v: str) -> Optional[str]:
        """Check if the delimiter is valid."""
        if v in {" ", "\t", ",", ";", "|", r"\s+"}:
            return v
        else:
            raise ValueError(f" {v} is not a valid delimiter.")

    @validator("comment")
    @classmethod
    def check_comment(cls, v: str) -> Optional[str]:
        """Check if the comment marker is valid."""
        if v is None or v in {"#", "%"}:
            return v
        else:
            raise ValueError(f" {v} is not a valid comment marker.")

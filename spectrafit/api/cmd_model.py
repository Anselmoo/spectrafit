"""Reference model for the API of the command line interface."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from getpass import getuser
from hashlib import sha256
from socket import gethostname
from uuid import uuid4

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import HttpUrl
from pydantic.functional_validators import field_validator

from spectrafit import __version__


class DescriptionAPI(BaseModel):
    """Model for the description command line argument."""

    model_config = ConfigDict(extra="forbid")

    project_name: str = Field(
        default="FittingProject",
        alias="projectName",
        description="Name of the project",
    )
    project_details: str = Field(
        default=f"Fitting Project via SpectraFit v{__version__}",
        alias="projectDetails",
        description="Project details",
    )
    keywords: list[str] = Field(
        default=["spectra"],
        description="Keywords for the project",
    )
    authors: list[str] = Field(
        default=["authors"],
        description="Authors of the project",
    )
    references: list[str] = Field(
        default=["https://github.com/Anselmoo/spectrafit"],
        alias="refs",
        description="References for the project",
    )
    metadata: dict[str, object] | list[object] | None = Field(
        default=None,
        description="Arbitrary command metadata; structurally variable by command type.",
    )
    license: str = "BSD-3-Clause"
    version: str = __version__
    host_info: str = sha256(f"{getuser()}@{gethostname()}".encode()).hexdigest()
    timestamp: str = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M:%S")
    id_: str = Field(
        default=str(uuid4()),
        alias="id",
        description="Unique ID of the project",
    )

    @field_validator("references", mode="after")
    @classmethod
    def check_references(cls, v: list[str]) -> list[str] | None:
        """Check if the list of references have valid URLs."""
        return [str(HttpUrl(url)) for url in v]

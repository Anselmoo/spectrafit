"""MetaConfig — project metadata configuration.

Maps to the ``[meta]`` section of the v2 input TOML.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class MetaConfig(BaseModel):
    r"""Project metadata for a fitting run.

    Maps to the ``[meta]`` section in the v2 input TOML::

        [meta]
        description  = "XPS C 1s carbon fit"
        project_name = "Carbon Analysis"
        authors      = ["Author Name"]
        keywords     = ["XPS", "carbon"]

    Attributes:
        description: Free-text description of the fitting project.
        project_name: Short project identifier.
        authors: List of author names.
        keywords: Keyword tags for the project.
    """

    model_config = ConfigDict(extra="forbid")

    description: str = Field(
        default="SpectraFit project",
        description="Free-text description of the fitting project",
    )
    project_name: str = Field(
        default="FittingProject",
        description="Short project identifier",
    )
    authors: list[str] = Field(
        default_factory=list,
        description="Author names",
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keyword tags",
    )

"""Reference model for the API of the command line interface."""


from datetime import datetime
from getpass import getuser
from hashlib import sha256
from socket import gethostname
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from pydantic.functional_validators import field_validator
from spectrafit import __version__
from spectrafit.api.tools_model import AutopeakAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import GlobalFittingAPI


class DescriptionAPI(BaseModel):
    """Model for the description command line argument."""

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
    keywords: List[str] = Field(
        default=["spectra"], description="Keywords for the project"
    )
    authors: List[str] = Field(
        default=["authors"], description="Authors of the project"
    )
    references: List[str] = Field(
        default=["https://github.com/Anselmoo/spectrafit"],
        alias="refs",
        description="References for the project",
    )
    metadata: Optional[Union[Dict[Any, Any], List[Any]]] = Field(
        default=None, description="Metadata for the project"
    )
    license: str = "BSD-3-Clause"
    version: str = __version__
    host_info: str = sha256(f"{getuser()}@{gethostname()}".encode()).hexdigest()
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_: str = Field(
        default=str(uuid4()), alias="id", description="Unique ID of the project"
    )

    @field_validator("references")
    @classmethod
    def check_references(cls, v: List[str]) -> Optional[List[str]]:
        """Check if the list of references have valid URLs."""
        return [str(HttpUrl(url)) for url in v]


class CMDModelAPI(BaseModel):
    """Model for the model command line argument."""

    infile: str
    outfile: str = Field(default="spectrafit_results")
    input: str = Field(default="fitting_input.toml")
    oversampling: bool = DataPreProcessingAPI().oversampling
    energy_start: Optional[float] = DataPreProcessingAPI().energy_start
    energy_stop: Optional[float] = DataPreProcessingAPI().energy_stop
    smooth: Optional[int] = DataPreProcessingAPI().smooth
    shift: Optional[float] = DataPreProcessingAPI().shift
    column: List[Union[int, str]] = DataPreProcessingAPI().column
    separator: str = "\t"
    decimal: str = "."
    header: Optional[int] = None
    comment: Optional[str] = None
    global_: int = Field(GlobalFittingAPI().global_)
    autopeak: Union[AutopeakAPI, bool, Any] = False
    noplot: bool = False
    version: bool = False
    verbose: int = Field(default=0, ge=0, le=2)
    description: Optional[DescriptionAPI] = Field(DescriptionAPI())

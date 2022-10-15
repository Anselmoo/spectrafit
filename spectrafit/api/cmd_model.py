"""Reference model for the API of the command line interface."""


from datetime import datetime
from getpass import getuser
from socket import gethostname
from typing import Any
from typing import List
from typing import Optional
from typing import Union
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field
from pydantic import HttpUrl
from spectrafit import __version__
from spectrafit.api.tools_model import AutopeakAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import GlobalFittingAPI


class DescriptionAPI(BaseModel):
    """Model for the description command line argument."""

    project_name: str = Field(
        default="FittingProject",
        alias="projectNames",
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
    references: List[HttpUrl] = Field(
        default=["https://github.com/Anselmoo/spectrafit"],
        alias="refs",
        description="References for the project",
    )
    version: str = __version__
    user_system: str = f"{getuser()}@{gethostname()}"
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_: str = Field(
        default=str(uuid4()), alias="id", description="Unique ID of the project"
    )


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

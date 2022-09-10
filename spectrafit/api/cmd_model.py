"""Reference model for the API of the command line interface."""
from __future__ import annotations

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
from spectrafit import __version__
from spectrafit.api.tools_model import Autopeak
from spectrafit.api.tools_model import DataPreProcessing
from spectrafit.api.tools_model import GlobalFitting


class Description(BaseModel):
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
    authors: List[str] = Field(default=[], description="Authors of the project")
    references: List[str] = Field(default=[], description="References for the project")
    version: str = __version__
    user_system: str = f"{getuser()}@{gethostname()}"
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_: str = Field(
        default=str(uuid4()), alias="id", description="Unique ID of the project"
    )


class CMDModel(BaseModel):
    """Model for the model command line argument."""

    infile: str
    outfile: str = Field(default="spectrafit_results")
    input: str = Field(default="fitting_input.toml")
    oversampling: bool = DataPreProcessing().oversampling
    energy_start: Optional[float] = DataPreProcessing().energy_start
    energy_stop: Optional[float] = DataPreProcessing().energy_stop
    smooth: Optional[int] = DataPreProcessing().smooth
    shift: Optional[float] = DataPreProcessing().shift
    column: List[Union[int, str]] = Field(
        min_items=1, default=[0, 1], dtypes=[int, str]
    )
    separator: str = "\t"
    decimal: str = "."
    header: Optional[int] = None
    comment: Optional[str] = None
    global_: int = Field(GlobalFitting().global_, alias="global")
    autopeak: Union[Autopeak, bool, Any] = False
    noplot: bool = False
    version: bool = False
    verbose: int = Field(default=0, ge=0, le=2)
    description: Optional[Description] = Field(Description())

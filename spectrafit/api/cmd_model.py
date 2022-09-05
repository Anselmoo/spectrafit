"""Refernce model for the API of the comand line interface."""
from __future__ import annotations

from datetime import datetime
from getpass import getuser
from socket import gethostname
from typing import Optional
from typing import Union
from uuid import uuid4

from pydantic import BaseModel
from pydantic import Field
from spectrafit import __version__


class Autopeak(BaseModel):
    """Model for the autopeak command line argument."""

    model_type: str
    height: list[float]
    threshold: list[float]
    distance: int
    prominence: list[float]
    width: list[float]
    wlen: int


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
    keywords: list[str] = Field(
        default=["spectra"], description="Keywords for the project"
    )
    authors: list[str] = Field(default=[], description="Authors of the project")
    references: list[str] = Field(default=[], description="References for the project")
    version: str = __version__
    user_system: str = f"{getuser()}@{gethostname()}"
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    id_: str = Field(
        default=str(uuid4()), alias="id", description="Unique ID of the project"
    )


class Model(BaseModel):
    """Model for the model command line argument."""

    infile: str
    outfile: str = Field(default="spectrafit_results")
    input: str = Field(default="fitting_input.toml")
    oversampling: bool = False
    energy_start: Optional[int] = None
    energy_stop: Optional[int] = None
    smooth: int = Field(default=0, ge=0)
    shift: Union[int, float] = 0
    column: list[Union[int, str]] = Field(
        min_items=1, default=[0, 1], dtypes=[int, str]
    )
    separator: str = "\t"
    decimal: str = "."
    header: Optional[int] = None
    comment: Optional[str] = None
    global_: int = Field(default=0, ge=0, le=2, alias="global")
    autopeak: Union[Autopeak, bool] = False
    noplot: bool = False
    version: bool = False
    verbose: int = Field(default=0, ge=0, le=2)
    description: dict[str, Description] = Description().dict()

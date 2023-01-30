"""Reference model for the API of the Jupyter Notebook interface."""


from typing import Optional
from typing import Tuple

import numpy as np

from numpy.typing import NDArray
from pydantic import BaseModel
from pydantic import Field


class XAxisAPI(BaseModel):
    """Defintion of the X-Axis of the plotly figure."""

    name: str = Field(
        default="Incident Energy", description="Name of the x-axis of the plot."
    )
    unit: Optional[str] = Field(
        default="eV", description="Name of the x-axis units of the plot."
    )


class YAxisAPI(BaseModel):
    """Defintion of the Y-Axis of the plotly figure."""

    name: str = Field(
        default="Emission Energy", description="Name of the y-axis of the plot."
    )
    unit: Optional[str] = Field(
        default="eV", description="Name of the y-axis units of the plot."
    )


class ZAxisAPI(BaseModel):
    """Defintion of the Z-Axis of the plotly figure."""

    name: str = Field(
        default="Intensity", description="Name of the z-axis of the plot."
    )
    unit: Optional[str] = Field(
        default="a.u.", description="Name of the z-axis units of the plot."
    )


class MainTitleAPI(BaseModel):
    """Defintion of the main title of the plotly figure."""

    rixs: str = Field(default="RIXS", description="Name of the RIXS plot.")
    xes: str = Field(default="XES", description="Name of the XES plot.")
    xas: str = Field(default="XAS", description="Name of the XAS plot.")


class SizeRatioAPI(BaseModel):
    """Defintion of the size ratio of the plotly figure."""

    size: Tuple[int, int] = Field(
        default=(500, 500), description="Basic size of the plots in pixels."
    )
    ratio_rixs: Tuple[float, float] = Field(
        default=(2, 2), description="Ratio of the RIXS plot."
    )
    ratio_xes: Tuple[float, float] = Field(
        default=(3, 1), description="Ratio of the XES plot."
    )
    ratio_xas: Tuple[float, float] = Field(
        default=(3, 1), description="Ratio of the XAS plot."
    )


class RIXSModelAPI(BaseModel):
    """Definition of the RIXS model."""

    incident_energy: NDArray[np.float64] = Field(
        ..., description="Incident energy values."
    )
    emission_energy: NDArray[np.float64] = Field(
        ..., description="Emission energy values."
    )
    rixs_map: NDArray[np.float64] = Field(..., description="RIXS map values.")

    class Config:
        """Configurations for the RIXSModelAPI class."""

        arbitrary_types_allowed = True


class RIXSPlotAPI(BaseModel):
    """Definition of the plotly figure."""

    incident_energy: NDArray[np.float64] = Field(
        ..., description="Incident energy values."
    )
    emission_energy: NDArray[np.float64] = Field(
        ..., description="Emission energy values."
    )
    emission_intensity: NDArray[np.float64] = Field(
        ..., description="Emission intensity values (RIXS), which has to be a 2D array."
    )
    energy_loss: Optional[NDArray[np.float64]] = Field(
        default=None, description="Energy loss values."
    )
    energy_loss_intensity: Optional[NDArray[np.float64]] = Field(
        default=None,
        description="Energy loss intensity values (XES), which has to be a 2D array.",
    )
    x_axis: XAxisAPI = XAxisAPI()
    y_axis: YAxisAPI = YAxisAPI()
    z_axis: ZAxisAPI = ZAxisAPI()
    main_title: MainTitleAPI = MainTitleAPI()
    size_ratio: SizeRatioAPI = SizeRatioAPI()

    class Config:
        """Configurations for the RIXSPlotAPI class."""

        arbitrary_types_allowed = True

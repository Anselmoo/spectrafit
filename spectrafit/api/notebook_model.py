"""Reference model for the API of the Jupyter Notebook interface."""


from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from _plotly_utils.colors.carto import Burg
from _plotly_utils.colors.carto import Purp_r
from _plotly_utils.colors.carto import Teal_r
from _plotly_utils.colors.qualitative import Plotly as PlotlyColors
from pydantic import BaseModel
from pydantic import Field
from pydantic import validator


class XAxisAPI(BaseModel):
    """Defintion of the X-Axis of the plotly figure."""

    name: str = Field(default="Energy", description="Name of the x-axis of the plot.")
    unit: Optional[str] = Field(
        default="eV", description="Name of the x-axis units of the plot."
    )


class YAxisAPI(BaseModel):
    """Defintion of the Y-Axis of the plotly figure."""

    name: str = Field(
        default="Intensity", description="Name of the y-axis of the plot."
    )
    unit: Optional[str] = Field(
        default="a.u.", description="Name of the y-axis units of the plot."
    )


class ResidualAPI(BaseModel):
    """Definition of the residual plot (Y-Axis) of the plotly figure."""

    name: str = Field(
        default="Residuals", description="Name of the residual-axis of the plot."
    )
    unit: Optional[str] = Field(
        default="a.u.", description="Name of the residual-axis units of the plot."
    )


class MetricAPI(BaseModel):
    """Definition of the residual plot (Y-Axis) of the plotly figure."""

    name_0: str = Field(
        default="Metrics", description="Name of the first metrics-axis of the plot."
    )
    unit_0: Optional[str] = Field(
        default="a.u.", description="Name of the first metrics-axis units of the plot."
    )
    name_1: str = Field(
        default="Metrics", description="Name of the second metrics-axis of the plot."
    )
    unit_1: Optional[str] = Field(
        default="a.u.", description="Name of the second metrics-axis units of the plot."
    )


class RunAPI(BaseModel):
    """Definition of the residual plot (Y-Axis) of the plotly figure."""

    name: str = Field(default="Run", description="Name of the Run-axis of the plot.")
    unit: Optional[str] = Field(
        default="#", description="Name of the run-axis units of the plot."
    )


class FontAPI(BaseModel):
    """Definition of the used font of the plotly figure."""

    family: str = Field(
        default="Open Sans, monospace", description="Font family of the plot."
    )
    size: int = Field(default=12, description="Font size of the plot.")
    color: str = Field(default="black", description="Font color of the plot.")


class LegendAPI(BaseModel):
    """Definition of the legend of the plotly figure."""

    orientation: str = Field(default="h", description="Orientation of the legend.")
    yanchor: str = Field(default="bottom", description="Y anchor of the legend.")
    y: float = Field(default=1.02, description="Y position of the legend.")
    xanchor: str = Field(default="right", description="X anchor of the legend.")
    x: float = Field(default=1, description="X position of the legend.")


class GridAPI(BaseModel):
    """Definition of the grid of the plotly figure."""

    show: bool = Field(default=True, description="Show grid lines.")
    ticks: str = Field(default="outside", description="Show grid ticks.")
    dash: str = Field(default="dot", description="Show grid dashes.")


class ColorAPI(BaseModel):
    """Definition of the colors of the plotly figure."""

    intensity: str = Field(
        default=PlotlyColors[0], description="Color of the spectrum-intensity."
    )
    residual: str = Field(
        default=PlotlyColors[1], description="Color of the residuals."
    )
    fit: str = Field(default=PlotlyColors[5], description="Color of the fit.")
    components: str = Field(
        default=PlotlyColors[6], description="Color of the components, mainly peaks."
    )
    # Merging two color list to onw list with switchin the order of the colors
    bars: List[str] = Field(
        default=[i for j in zip(Teal_r, Purp_r) for i in j],
        description="Color of the bar plot of the metrics.",
    )
    lines: List[str] = Field(default=Burg, description="Color of the lines plot.")
    paper: str = Field(default="white", description="Color of the paper.")
    plot: str = Field(default="white", description="Color of the plot.")
    color: str = Field(default="black", description="Color of the text.")
    grid: str = Field(default="lightgrey", description="Color of the grid.")
    line: str = Field(default="black", description="Color of the bottom and side line.")
    zero_line: str = Field(default="grey", description="Color of the zero line.")
    ticks: str = Field(default="black", description="Color of the ticks.")
    font: str = Field(default="black", description="Font color of the plot.")

    @validator(
        "page",
        "layout",
        "grid",
        "line",
        "zero_line",
        "ticks",
        "font",
        check_fields=False,
    )
    @classmethod
    def transparent_rgb(cls, v: str) -> str:
        """Convert string to transparent RGB color.

        Args:
            v (str): One of the key-words of the validator decorator.

        Returns:
            str: Translate the word `transparent` to the rgb value `rgba(0,0,0,0)`.
        """
        return "rgba(0,0,0,0)" if "transparent" in v.lower() else v


class PlotAPI(BaseModel):
    """Definition of the plotly figure."""

    x: str = Field(..., description="Name of the x column to plot.")
    y: Union[str, List[str]] = Field(
        ..., description="List of the names of the y columns to plot."
    )
    title: Optional[str] = Field(None, description="Title of the plot.")
    xaxis_title: XAxisAPI = XAxisAPI()
    yaxis_title: YAxisAPI = YAxisAPI()
    residual_title: ResidualAPI = ResidualAPI()
    metric_title: MetricAPI = MetricAPI()
    run_title: RunAPI = RunAPI()
    legend_title: str = Field(default="Spectra", description="Title of the legend.")
    show_legend: bool = Field(default=True, description="Show legend.")
    legend: LegendAPI = LegendAPI()
    font: FontAPI = FontAPI()
    minor_ticks: bool = Field(default=True, description="Show minor ticks.")
    color: ColorAPI = ColorAPI()
    grid: GridAPI = GridAPI()
    size: Tuple[int, Tuple[int, int]] = Field(
        default=(800, (600, 300)), description="Size of the fit- and metric-plot."
    )


class FnameAPI(BaseModel):
    """Definition of the file name."""

    fname: str = Field(..., description="Name of the file to save.")
    suffix: str = Field(..., description="Suffix of the file to save.")
    prefix: Optional[str] = Field(
        default=None, description="Prefix of the file to save."
    )
    folder: Optional[str] = Field(default=None, description="Folder to save the file.")

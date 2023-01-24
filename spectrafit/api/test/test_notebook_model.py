"""Test of the notebook model."""

from _plotly_utils.colors.qualitative import Plotly as PlotlyColors
from spectrafit.api.notebook_model import ColorAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.notebook_model import FontAPI
from spectrafit.api.notebook_model import GridAPI
from spectrafit.api.notebook_model import LegendAPI
from spectrafit.api.notebook_model import MetricAPI
from spectrafit.api.notebook_model import PlotAPI
from spectrafit.api.notebook_model import ResidualAPI
from spectrafit.api.notebook_model import RunAPI
from spectrafit.api.notebook_model import XAxisAPI
from spectrafit.api.notebook_model import YAxisAPI


def test_xaxis_model() -> None:
    """Test the X-Axis model."""
    xaxis = XAxisAPI()
    assert xaxis.name == "Energy"
    assert xaxis.unit == "eV"


def test_yaxis_model() -> None:
    """Test the Y-Axis model."""
    yaxis = YAxisAPI()
    assert yaxis.name == "Intensity"
    assert yaxis.unit == "a.u."


def test_residual_model() -> None:
    """Test the Residual model."""
    residual = ResidualAPI()
    assert residual.name == "Residuals"
    assert residual.unit == "a.u."


def test_metric_model() -> None:
    """Test the Metric model."""
    metric = MetricAPI()
    assert metric.name_0 == "Metrics"
    assert metric.unit_0 == "a.u."
    assert metric.name_1 == "Metrics"
    assert metric.unit_1 == "a.u."


def test_run_model() -> None:
    """Test the Run model."""
    run = RunAPI()
    assert run.name == "Run"
    assert run.unit == "#"


def test_font_model() -> None:
    """Test the Font model."""
    font = FontAPI()
    assert font.family == "Open Sans, monospace"
    assert font.size == 12
    assert font.color == "black"


def test_legend_model() -> None:
    """Test the Legend model."""
    legend = LegendAPI()
    assert legend.orientation == "h"
    assert legend.x == 1
    assert legend.y == 1.02
    assert legend.xanchor == "right"
    assert legend.yanchor == "bottom"


def test_grid_model() -> None:
    """Test the Grid model."""
    grid = GridAPI()
    assert grid.show is True
    assert grid.ticks == "outside"
    assert grid.dash == "dot"


def test_fname_model() -> None:
    """Test the Fname model."""
    fname = FnameAPI(
        fname="test",
        suffix="png",
        prefix="test",
        folder="folder",
    )
    assert fname.fname == "test"
    assert fname.suffix == "png"
    assert fname.prefix == "test"
    assert fname.folder == "folder"


def test_plot_model() -> None:
    """Test the Plot model."""
    plot = PlotAPI(
        x="energy",
        y="intensity",
        title="test",
    )
    assert plot.x == "energy"
    assert plot.y == "intensity"
    assert plot.title == "test"
    assert isinstance(plot.xaxis_title, XAxisAPI)
    assert isinstance(plot.yaxis_title, YAxisAPI)


def test_color_model() -> None:
    """Test the Color model."""
    color = ColorAPI(paper="transparent")

    assert color.intensity == PlotlyColors[0]
    assert color.paper == "rgba(0,0,0,0)"

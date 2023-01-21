"""This module contains the RIXS visualizer class."""

from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dash import dcc
from dash import html
from dash_bootstrap_templates import ThemeChangerAIO
from dash_bootstrap_templates import template_from_url
from numpy.typing import NDArray
from spectrafit.api.RIXS_model import MainTitleAPI
from spectrafit.api.RIXS_model import SizeRatioAPI
from spectrafit.api.RIXS_model import XAxisAPI
from spectrafit.api.RIXS_model import YAxisAPI
from spectrafit.api.RIXS_model import ZAxisAPI
from spectrafit.plugins.notebook import DataFramePlot


class RIXSFigure:
    """Class to create the RIXS figure.

    !!! info "About the RIXS figure"

        The RIXS figure is composed of three subplots:

        - RIXS -> 3D plot
        - XES -> 2D plot
        - XAS -> 2D plot

    """

    def __init__(
        self,
        incident_energy: NDArray[np.float64],
        emission_energy: NDArray[np.float64],
        RIXS: NDArray[np.float64],
        size: SizeRatioAPI = SizeRatioAPI(
            size=(500, 500),
            ratio_rixs=(2, 2),
            ratio_xes=(3, 1),
            ratio_xas=(3, 1),
        ),
        x_axes: XAxisAPI = XAxisAPI(name="Incident Energy", unit="eV"),
        y_axes: YAxisAPI = YAxisAPI(name="Emission Energy", unit="eV"),
        z_axes: ZAxisAPI = ZAxisAPI(name="Intensity", unit="a.u."),
    ):
        """Initialize the RIXS figure.

        Args:
            incident_energy (NDArray[np.float64]): Incident energy.
            emission_energy (NDArray[np.float64]): Emission energy.
            RIXS (NDArray[np.float64]): RIXS data.
            size (SizeRatioAPI, optional): Size of the figure.
                 Defaults to SizeRatioAPI(size=(500, 500), ratio_rixs=(2, 2),
                 ratio_xes=(3, 1), ratio_xas=(3, 1)).
            x_axes (XAxisAPI, optional): X-Axis of the figure.
                 Defaults to XAxisAPI(name="Incident Energy", unit="eV").
            y_axes (YAxisAPI, optional): Y-Axis of the figure.
                 Defaults to YAxisAPI(name="Emission Energy", unit="eV").
            z_axes (ZAxisAPI, optional): Z-Axis of the figure.
                 Defaults to ZAxisAPI(name="Intensity", unit="a.u.").
        """
        self.incident_energy = incident_energy
        self.emission_energy = emission_energy
        self.RIXS = RIXS

        self.x_axes = x_axes
        self.y_axes = y_axes
        self.z_axes = z_axes
        self.initialize_figure_size(size)

    def initialize_figure_size(self, size: SizeRatioAPI) -> None:
        """Initialize the size of the figure.

        Args:
            size (SizeRatioAPI): Size of the figure.
        """
        self.rixs_width = int(size.size[0] * size.ratio_rixs[0])
        self.rixs_height = int(size.size[1] * size.ratio_rixs[1])
        self.xas_width = int(size.size[0] * size.ratio_xas[0])
        self.xas_height = int(size.size[1] * size.ratio_xas[1])
        self.xes_width = int(size.size[0] * size.ratio_xes[0])
        self.xes_height = int(size.size[1] * size.ratio_xes[1])

    def create_rixs(
        self,
        colorscale: str = "Viridis",
        opacity: float = 0.9,
        template: Optional[str] = None,
    ) -> go.Figure:
        """Create the RIXS figure.

        Args:
            colorscale (str, optional): Color scale. Defaults to "Viridis".
            opacity (float, optional): Opacity of the surface. Defaults to 0.9.
            template (str, optional): Template of the figure. Defaults to None.

        Returns:
            go.Figure: RIXS figure.
        """
        fig = go.Figure(
            data=[
                go.Surface(
                    x=self.incident_energy,
                    y=self.emission_energy,
                    z=self.RIXS,
                    colorscale=colorscale,
                    opacity=opacity,
                    contours_z=dict(
                        show=True,
                        usecolormap=True,
                        highlightcolor="limegreen",
                        project_z=True,
                    ),
                )
            ],
        )

        fig.update_layout(
            autosize=True,
            width=self.rixs_width,
            height=self.rixs_height,
            scene=dict(
                xaxis_title=DataFramePlot.title_text(
                    name=self.x_axes.name, unit=self.x_axes.unit
                ),
                yaxis_title=DataFramePlot.title_text(
                    name=self.y_axes.name, unit=self.y_axes.unit
                ),
                zaxis_title=DataFramePlot.title_text(
                    name=self.z_axes.name, unit=self.z_axes.unit
                ),
                aspectmode="cube",
            ),
            template=template,
        )
        fig.update_traces(
            contours_z=dict(
                show=True, usecolormap=True, highlightcolor="limegreen", project_z=True
            )
        )
        return fig

    def create_xes(
        self,
        x: NDArray[np.float64],
        y: NDArray[np.float64],
        template: Optional[str] = None,
    ) -> go.Figure:
        """Create the XES figure.

        Args:
            x (NDArray[np.float64]): X-axis of the figure.
            y (NDArray[np.float64]): Y-axis of the figure.
            template (str, optional): Template of the figure. Defaults to None.

        Returns:
            go.Figure: XES figure.
        """
        fig = px.line(x=x, y=y, template=template)
        fig.update_layout(
            autosize=True,
            width=self.xes_width,
            height=self.xes_height,
        )
        # Udate the xaxis title
        fig.update_xaxes(
            title_text=DataFramePlot.title_text(
                name=self.y_axes.name, unit=self.y_axes.unit
            )
        )
        # Update the yaxis title
        fig.update_yaxes(
            title_text=DataFramePlot.title_text(
                name=self.z_axes.name, unit=self.z_axes.unit
            )
        )
        return fig

    def create_xas(
        self,
        x: NDArray[np.float64],
        y: NDArray[np.float64],
        template: Optional[str] = None,
    ) -> go.Figure:
        """Create the XAS figure.

        Args:
            x (NDArray[np.float64]): X-axis of the figure.
            y (NDArray[np.float64]): Y-axis of the figure.
            template (str, optional): Template of the figure. Defaults to None.

        Returns:
            go.Figure: XAS figure.
        """
        fig = px.line(x=x, y=y, template=template)
        fig.update_layout(
            autosize=True,
            width=self.xas_width,
            height=self.xas_height,
        )
        fig.update_xaxes(
            title_text=DataFramePlot.title_text(
                name=self.x_axes.name, unit=self.x_axes.unit
            )
        )
        fig.update_yaxes(
            title_text=DataFramePlot.title_text(
                name=self.z_axes.name, unit=self.z_axes.unit
            )
        )
        return fig


class App(RIXSFigure):
    """Create the RIXS app.

    !!! info "About the RIXS app"

        The RIXS app is a web application that allows you to visualize the RIXS
        data. The app is based on the Dash framework. The app is composed of
        three figures: the RIXS figure, the XES figure and the XAS figure.

        The RIXS figure is a 3D surface plot. The XES figure is a line plot
        showing the XES spectrum. The XAS figure is a line plot showing the XAS
        spectrum.

        The RIXS figure is interactive. You can zoom in and out, rotate the
        figure, and change the color scale. The XES and XAS figures are not
        interactive.

    """

    def __init__(
        self,
        incident_energy: NDArray[np.float64],
        emission_energy: NDArray[np.float64],
        RIXS: NDArray[np.float64],
        size: SizeRatioAPI = SizeRatioAPI(
            size=(500, 500),
            ratio_rixs=(2, 2),
            ratio_xas=(3, 1),
            ratio_xes=(3, 1),
        ),
        main_title: MainTitleAPI = MainTitleAPI(rixs="RIXS", xes="XES", xas="XAS"),
        fdir: Path = Path("./"),
        mode: str = "server",
        debug: bool = False,
    ) -> None:
        """Create the RIXS app.

        Args:
            incident_energy (NDArray[np.float64]): Incident energy.
            emission_energy (NDArray[np.float64]): Emission energy.
            RIXS (NDArray[np.float64]): RIXS data.
            size (SizeRatioAPI, optional): Size of the figures. Defaults to
                 SizeRatioAPI(size=(500, 500), ratio_rixs=(2, 2), ratio_xas=(3, 1),
                 ratio_xes=(3, 1)).
            main_title (MainTitleAPI, optional): Main title of the figures.
                 Defaults to MainTitleAPI(rixs="RIXS", xes="XES", xas="XAS").
            fdir (Path, optional): Directory to save the figures. Defaults to
                 Path("./").
            mode (str, optional): Mode of the app. Defaults to "server".
            debug (bool, optional): Debug mode. Defaults to False.

        """
        super().__init__(
            incident_energy=incident_energy,
            emission_energy=emission_energy,
            RIXS=RIXS,
            size=size,
        )
        self.fdir = fdir
        self.main_title = main_title
        self.mode = mode
        self.debug = debug

    def colorscale(self) -> html.Div:
        """Create the color scale dropdown.

        Returns:
            html.Div: Color scale dropdown.
        """
        return html.Div(
            [
                dbc.Label("Color Scale"),
                dcc.Dropdown(
                    id="colorscale",
                    options=[
                        {"label": "Viridis", "value": "Viridis"},
                        {"label": "Plasma", "value": "Plasma"},
                        {"label": "Inferno", "value": "Inferno"},
                        {"label": "Magma", "value": "Magma"},
                        {"label": "Cividis", "value": "Cividis"},
                        {"label": "Greys", "value": "Greys"},
                        {"label": "Greens", "value": "Greens"},
                        {"label": "YlOrRd", "value": "YlOrRd"},
                        {"label": "Bluered", "value": "Bluered"},
                        {"label": "RdBu", "value": "RdBu"},
                        {"label": "Reds", "value": "Reds"},
                        {"label": "Blues", "value": "Blues"},
                        {"label": "Picnic", "value": "Picnic"},
                        {"label": "Rainbow", "value": "Rainbow"},
                        {"label": "Portland", "value": "Portland"},
                        {"label": "Jet", "value": "Jet"},
                        {"label": "Hot", "value": "Hot"},
                        {"label": "Blackbody", "value": "Blackbody"},
                        {"label": "Earth", "value": "Earth"},
                        {"label": "Electric", "value": "Electric"},
                        {"label": "Viridis", "value": "Viridis"},
                        {"label": "Cividis", "value": "Cividis"},
                    ],
                    value="Viridis",
                ),
            ],
            className="dbc",
        )

    def opacity(self) -> html.Div:
        """Create the opacity slider.

        Returns:
            html.Div: Opacity slider.
        """
        return html.Div(
            [
                dbc.Label("Opacity"),
                dcc.Slider(
                    id="opacity",
                    min=0,
                    max=1,
                    step=0.1,
                    value=1,
                    marks={i: str(i) for i in range(2)},
                ),
            ]
        )

    def header(self) -> dbc.Card:
        """Create the header.

        Returns:
            dbc.Card: Header as a bootstrap card.
        """
        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4(
                        "Theme Explorer Sample App",
                        className="bg-primary text-white p-2 mb-2 text-center",
                    )
                ]
            )
        )

    def pre_body(self) -> Tuple[html.Div, html.Div, html.Div]:
        """Create the body.

        Returns:
            Tuple[html.Div, html.Div, html.Div]: Body as a tuple of three plot parts.
        """
        rixs = html.Div(
            [
                dbc.Label(self.main_title.rixs),
                dcc.Graph(id="rixs-figure"),
            ]
        )
        xes = html.Div(
            [
                dbc.Label(self.main_title.xes),
                dcc.Graph(id="xes-figure"),
            ]
        )
        xas = html.Div(
            [
                dbc.Label(self.main_title.xas),
                dcc.Graph(id="xas-figure"),
            ]
        )
        return rixs, xes, xas

    def body(self) -> dbc.Card:
        """Create the body.

        Returns:
            dbc.Card: Body as a bootstrap card.
        """
        colorscale = self.colorscale()
        opacity = self.opacity()
        rixs, xes, xas = self.pre_body()

        return (
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row([ThemeChangerAIO(aio_id="theme")]),
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.H1("RIXS Viewer", className="text-center")
                                ),
                            ],
                            justify="left",
                        ),
                        html.Br(),
                        dbc.Row(
                            [
                                dbc.Col(colorscale),
                                dbc.Col(opacity),
                            ],
                        ),
                        html.Br(),
                        dbc.Row(
                            [
                                dbc.Col(rixs),
                                dbc.Col([xes, xas]),
                            ],
                            justify="left",
                        ),
                        html.Br(),
                    ],
                    fluent=True,
                ),
                class_name="mt-4",
            ),
        )[0]

    def footer(self) -> dbc.Card:
        """Create the footer.

        Returns:
            dbc.Card: Footer as a bootstrap card.
        """
        return (
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dcc.Markdown(
                                    """
                    ### RIXS Viewer
                    This is a simple RIXS viewer. It is based on the
                    [Dash](https://dash.plotly.com/)
                    framework and uses the [Plotly](https://plotly.com/python/) library
                    for plotting. The code is available on
                    [GitHub](https://github.com/anselmoo/spectrafit).
                    """
                                ),
                            ],
                            justify="left",
                        )
                    ]
                ),
                class_name="mt-4",
            ),
        )[0]

    def run(self) -> None:
        """Run the app."""
        dbc_css = (
            "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
        )
        app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.COSMO, dbc_css],
        )
        app.layout = dbc.Container(
            [
                self.header(),
                self.body(),
                self.footer(),
            ],
            fluid=True,
        )

        @app.callback(
            [
                dash.dependencies.Output("xes-figure", "figure"),
                dash.dependencies.Output("xas-figure", "figure"),
                dash.dependencies.Output("rixs-figure", "figure"),
            ],
            [
                dash.dependencies.Input("rixs-figure", "hoverData"),
                dash.dependencies.Input("rixs-figure", "clickData"),
                dash.dependencies.Input("colorscale", "value"),
                dash.dependencies.Input("opacity", "value"),
                dash.dependencies.Input(ThemeChangerAIO.ids.radio("theme"), "value"),
            ],
        )
        def update_hover_data(
            hoverData: Dict[str, List[Dict[str, float]]],
            clickData: Dict[str, List[Dict[str, float]]],
            colorscale: str,
            opacity: float,
            theme: str,
        ) -> Tuple[go.Figure, go.Figure, go.Figure]:
            if hoverData is None:
                return (
                    self.create_xes(
                        x=self.incident_energy,
                        y=self.RIXS[:, int(self.emission_energy.size / 2)],
                        template=template_from_url(theme),
                    ),
                    self.create_xas(
                        x=self.emission_energy,
                        y=self.RIXS[int(self.incident_energy.size / 2), :],
                        template=template_from_url(theme),
                    ),
                    self.create_rixs(
                        colorscale=colorscale,
                        opacity=opacity,
                        template=template_from_url(theme),
                    ),
                )
            x = hoverData["points"][0]["x"]
            y = hoverData["points"][0]["y"]
            xes_fig = self.create_xes(
                x=self.incident_energy,
                y=self.RIXS[:, int(y)],
                template=template_from_url(theme),
            )
            xas_fig = self.create_xas(
                x=self.emission_energy,
                y=self.RIXS[int(x), :],
                template=template_from_url(theme),
            )
            rixs_fig = self.create_rixs(
                colorscale=colorscale,
                opacity=opacity,
                template=template_from_url(theme),
            )
            if clickData is None:
                return xes_fig, xas_fig, rixs_fig
            cx = clickData["points"][0]["x"]
            cy = clickData["points"][0]["y"]
            pd.DataFrame(
                {"energy": self.incident_energy, "xes": self.RIXS[:, int(cy)]}
            ).to_csv(
                self.fdir / f"xes_cut_{cx}_{cy}.txt",
                index=False,
            )
            pd.DataFrame(
                {"energy": self.emission_energy, "xas": self.RIXS[int(cx), :]}
            ).to_csv(
                self.fdir / f"xas_cut_{cx}_{cy}.txt",
                index=False,
            )
            return xes_fig, xas_fig, rixs_fig

        if self.mode == "jupyterlab":
            app.run_server(mode="jupyterlab", debug=self.debug)
        else:
            app.run_server(debug=self.debug)

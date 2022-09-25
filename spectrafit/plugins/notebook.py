"""Jupyter Notebook plugin for SpectraFit."""
from __future__ import annotations
from __future__ import print_function

from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import pandas as pd
import plotly.express as px

from dtale import show as dtale_show
from IPython.display import display
from IPython.display import display_markdown
from itables import show as itables_show

# from plotly.graph_objs import Figure
from plotly.subplots import make_subplots
from spectrafit.api.models_model import DistributionModelAPI
from spectrafit.api.notebook_model import ColorAPI
from spectrafit.api.notebook_model import FontAPI
from spectrafit.api.notebook_model import GridAPI
from spectrafit.api.notebook_model import LegendAPI
from spectrafit.api.notebook_model import PlotAPI
from spectrafit.api.notebook_model import ResidualAPI
from spectrafit.api.notebook_model import XAxisAPI
from spectrafit.api.notebook_model import YAxisAPI
from spectrafit.api.tools_model import ColumnNamesAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.models import SolverModels
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing


class DataFrameDisplay:
    """Class for displaying a dataframe in different ways."""

    def __init__(self, df: pd.DataFrame) -> None:
        """Initialize the DataframeDisplay class.

        Args:
            df (pd.DataFrame): Dataframe to display.
        """
        self.df = df

    def __call__(self, mode: str) -> None:
        """Call the DataframeDisplay class.

        Args:
            mode (str): _description_

        Raises:
            ValueError: _description_
        """
        if mode == "regular":
            display(self.df)
        elif mode == "interactive":
            itables_show(self.df)
        elif mode == "dtale":
            dtale_show(self.df)
        elif mode == "markdown":
            display_markdown(self.df.to_markdown())
        else:
            raise ValueError(
                "mode must be one of 'regular', 'interactive', 'dtale', or 'markdown'"
            )


class DataFramePlot:
    """Class to plot a dataframe."""

    def __init__(self, args_plot: PlotAPI) -> None:
        """Initialize the DataFramePlot class.

        Args:
            args_plot (PlotAPI): _description_
        """
        self.args_plot = args_plot

    @staticmethod
    def post_process_plot(df_orginal: pd.DataFrame, df: pd.DataFrame) -> None:
        """Plot of the post processed datafrme.

        Args:
            df_orginal (pd.DataFrame): _description_
            df (pd.DataFrame): _description_
        """

    def plot_2dataframes(
        self, df_1: pd.DataFrame, df_2: Optional[pd.DataFrame] = None
    ) -> None:
        """Plot of two dataframes.

        !!! info "About the plot"

            The plot is a combination of two plots. The first plot is the
            can be the residual plot of a fit or the _modified_ data. The second
            plot can be the fit or the original data.

        !!! missing "`line_dash_map`"

            Currently, the `line_dash_map` is not working, and the dash is not
            plotted. Most likely, this is related to the fact that the columns
            are not labeled in the dataframe.

        Args:
            df_1 (pd.DataFrame): First dataframe to plot, which will generate
                 automatically a fit plot with residual plot. The ratio is 70% to 20%
                 with 10% space in between.
            df_2 (Optional[pd.DataFrame], optional): Second optional dataframe to
                 plot for comparsion. In this case, the ratio will between first
                 and second plot will be same. Defaults to None.
        """
        if df_2 is None:
            _fig1 = px.line(
                df_1,
                x=ColumnNamesAPI().energy,
                y=ColumnNamesAPI().residual,
                color_discrete_sequence=[self.args_plot.color.residual],
            )
            _y = df_1.columns.drop([ColumnNamesAPI().energy, ColumnNamesAPI().residual])
            _fig2 = px.line(
                df_1,
                x=ColumnNamesAPI().energy,
                y=_y,
                color_discrete_map={
                    ColumnNamesAPI().intensity: self.args_plot.color.intensity,
                    ColumnNamesAPI().fit: self.args_plot.color.fit,
                    **{
                        key: self.args_plot.color.components
                        for key in _y.drop(
                            [ColumnNamesAPI().intensity, ColumnNamesAPI().fit]
                        )
                    },
                },
                line_dash_map={
                    ColumnNamesAPI().intensity: "solid",
                    ColumnNamesAPI().fit: "longdash",
                    **{
                        key: "dash"
                        for key in _y.drop(
                            [ColumnNamesAPI().intensity, ColumnNamesAPI().fit]
                        )
                    },
                },
            )
        else:
            _fig1 = px.line(df_1, x=self.args_plot.x, y=self.args_plot.y)
            _fig2 = px.line(df_2, x=self.args_plot.x, y=self.args_plot.y)

        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True, shared_yaxes=True, vertical_spacing=0.05
        )

        for _spec_1 in _fig1["data"]:
            fig.append_trace(_spec_1, row=1, col=1)
        for _spec_2 in _fig2["data"]:
            fig.append_trace(_spec_2, row=2, col=1)

        fig.update_layout(
            title=self.args_plot.title,
            legend_title=self.args_plot.legend_title,
            legend=self.args_plot.legend.dict(),
            font=self.args_plot.font.dict(),
            showlegend=self.args_plot.show_legend,
            width=self.args_plot.size[0],
            height=self.args_plot.size[1],
            paper_bgcolor=self.args_plot.color.paper,
            plot_bgcolor=self.args_plot.color.plot,
        )
        fig.update_xaxes(
            minor=dict(
                tickcolor=self.args_plot.color.ticks,
                showgrid=self.args_plot.grid.show,
                ticks=self.args_plot.grid.ticks,
                griddash=self.args_plot.grid.dash,
            ),
            gridcolor=self.args_plot.color.grid,
            linecolor=self.args_plot.color.line,
            zerolinecolor=self.args_plot.color.zero_line,
            color=self.args_plot.color.color,
        )
        fig.update_yaxes(
            minor=dict(
                tickcolor=self.args_plot.color.ticks,
                showgrid=self.args_plot.grid.show,
                ticks=self.args_plot.grid.ticks,
                griddash=self.args_plot.grid.dash,
            ),
            gridcolor=self.args_plot.color.grid,
            linecolor=self.args_plot.color.line,
            zerolinecolor=self.args_plot.color.zero_line,
            color=self.args_plot.color.color,
        )

        xaxis_title = (
            f"{self.args_plot.xaxis_title.name} [{self.args_plot.xaxis_title.unit}]",
        )[0]
        yaxis_title = (
            f"{self.args_plot.yaxis_title.name} [{self.args_plot.yaxis_title.unit}]",
        )[0]

        fig.update_xaxes(title_text=xaxis_title, row=1, col=1)
        fig.update_xaxes(title_text=xaxis_title, row=2, col=1)
        if df_2 is None:
            residual_title = (
                f"{self.args_plot.residual_title.name}"
                f" [{self.args_plot.residual_title.unit}]",
            )[0]
            fig["layout"]["yaxis1"].update(domain=[0.8, 1])
            fig["layout"]["yaxis2"].update(domain=[0, 0.7])
            fig.update_yaxes(title_text=residual_title, row=1, col=1)
        else:
            fig.update_yaxes(title_text=yaxis_title, row=1, col=1)
        fig.update_yaxes(title_text=yaxis_title, row=2, col=1)
        fig.show()

    def plot_dataframe(self, df: pd.DataFrame) -> None:
        """Plot the dataframe according to the PlotAPI arguments.

        Args:
            df (pd.DataFrame): _description_
        """
        fig = px.line(df, x=self.args_plot.x, y=self.args_plot.y)
        xaxis_title = (
            f"{self.args_plot.xaxis_title.name} [{self.args_plot.xaxis_title.unit}]",
        )[0]
        yaxis_title = (
            f"{self.args_plot.yaxis_title.name} [{self.args_plot.yaxis_title.unit}]",
        )[0]
        fig.update_layout(
            title=self.args_plot.title,
            legend_title=self.args_plot.legend_title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            legend=self.args_plot.legend.dict(),
            font=self.args_plot.font.dict(),
            showlegend=self.args_plot.legend,
            width=self.args_plot.size[0],
            height=self.args_plot.size[1],
            paper_bgcolor=self.args_plot.color.paper,
            plot_bgcolor=self.args_plot.color.plot,
        )
        fig.update_xaxes(
            minor=dict(
                tickcolor=self.args_plot.color.ticks,
                showgrid=self.args_plot.grid.show,
                ticks=self.args_plot.grid.ticks,
                griddash=self.args_plot.grid.dash,
            ),
            gridcolor=self.args_plot.color.grid,
            linecolor=self.args_plot.color.line,
            zerolinecolor=self.args_plot.color.zero_line,
            color=self.args_plot.color.color,
        )
        fig.update_yaxes(
            minor=dict(
                tickcolor=self.args_plot.color.ticks,
                showgrid=self.args_plot.grid.show,
                ticks=self.args_plot.grid.ticks,
                griddash=self.args_plot.grid.dash,
            )
        )

        fig.show()


# class ExportResults:
#    ...


# class ExportReport:
#    ...


class SpectraFitNotebook(DataFramePlot):
    """Jupyter Notebook plugin for SpectraFit."""

    global_: Union[bool, int] = False
    autopeak: bool = False

    def __init__(
        self,
        df: pd.DataFrame,
        x_column: str,
        y_column: Union[str, List[str]],
        oversampling: bool = False,
        smooth: int = 0,
        shift: float = 0,
        energy_start: Optional[float] = None,
        energy_stop: Optional[float] = None,
        title: Optional[str] = None,
        xaxis_title: XAxisAPI = XAxisAPI(name="Energy", unit="eV"),
        yaxis_title: YAxisAPI = YAxisAPI(name="Intensity", unit="a.u."),
        residual_title: ResidualAPI = ResidualAPI(name="Residual", unit="a.u."),
        legend_title: str = "Spectra",
        show_legend: bool = True,
        legend: LegendAPI = LegendAPI(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        font: FontAPI = FontAPI(family="Open Sans, monospace", size=12, color="black"),
        minor_ticks: bool = True,
        color: ColorAPI = ColorAPI(),
        grid: GridAPI = GridAPI(),
        size: Tuple[int, int] = (800, 600),
    ) -> None:
        """Initialize the SpectraFitNotebook class.

        Args:
            df (pd.DataFrame): _description_
            x_column (str): _description_
            y_column (Union[str, List[str]]): _description_
            oversampling (bool, optional): _description_. Defaults to False.
            smooth (int, optional): _description_. Defaults to 0.
            shift (float, optional): _description_. Defaults to 0.
            energy_start (Optional[float], optional): _description_. Defaults to None.
            energy_stop (Optional[float], optional): _description_. Defaults to None.
            title (Optional[str], optional): _description_. Defaults to None.
            xaxis_title (XAxisAPI, optional): _description_.
                 Defaults to XAxisAPI(name="Energy", unit="eV").
            yaxis_title (YAxisAPI, optional): _description_.
                 Defaults to YAxisAPI(name="Intensity", unit="a.u.").
            residual_title (ResidualAPI, optional): _description_.
                 Defaults to ResidualAPI(name="Residual", unit="a.u.").
            legend_title (str, optional): _description_. Defaults to "Spectra".
            show_legend (bool, optional): _description_. Defaults to True.
            legend (LegendAPI, optional): _description_.
                 Defaults to LegendAPI( orientation="h", yanchor="bottom", y=1.02,
                 xanchor="right", x=1 ).
            font (FontAPI, optional): _description_.
                 Defaults to FontAPI(family="Open Sans, monospace", size=12,
                 color="black").
            minor_ticks (bool, optional): _description_. Defaults to True.
            color (ColorAPI, optional): _description_. Defaults to ColorAPI().
            grid (GridAPI, optional): _description_. Defaults to GridAPI().
            size (Tuple[int, int], optional): _description_. Defaults to (800, 600).

        Raises:
            ValueError: _description_
        """
        self.x_column = x_column
        self.y_column = y_column

        if isinstance(self.y_column, list):
            self.global_ = 1
            self.df = df[[self.x_column, *self.y_column]]
        else:
            self.df = df[[self.x_column, self.y_column]]
        self.df_original = self.df

        if self.df.shape[1] < 2:
            raise ValueError("The dataframe must have 2 or more columns.")

        self.args_pre = DataPreProcessingAPI(
            oversampling=oversampling,
            energy_start=energy_start,
            energy_stop=energy_stop,
            smooth=smooth,
            shift=shift,
            column=list(self.df.columns),
        ).dict()

        super().__init__(
            args_plot=PlotAPI(
                x=self.x_column,
                y=self.y_column,
                title=title,
                xaxis_title=xaxis_title,
                yaxis_title=yaxis_title,
                residual_title=residual_title,
                legend_title=legend_title,
                show_legend=show_legend,
                legend=legend,
                font=font,
                minor_ticks=minor_ticks,
                color=color,
                grid=grid,
                size=size,
            )
        )

        self.args_solver: Dict[str, Any] = {}
        self.pre_statistic: Dict[str, Any] = {}

    @property
    def pre_process(self) -> None:
        """Pre-processing class."""
        self.df, _pre_statistic = PreProcessing(df=self.df, args=self.args_pre)()
        self.pre_statistic = _pre_statistic["data_statistic"]

    @property
    def return_pre_statistic(self) -> Dict[str, Any]:
        """Return the pre-processing statistic."""
        return self.pre_statistic

    @property
    def return_df(self) -> pd.DataFrame:
        """Return the dataframe."""
        return self.df

    @property
    def plot_init_df(self) -> None:
        """Plot the initial spectra."""
        self.plot_dataframe(self.df_original)

    @property
    def plot_current_df(self) -> None:
        """Plot the initial spectra."""
        self.plot_dataframe(self.df)

    @property
    def plot_preprocessed_df(self) -> None:
        """Plot the current processed spectra."""
        self.plot_2dataframes(df_1=self.df, df_2=self.df_original)

    @property
    def plot_fit(self) -> None:
        """Plot the fit."""
        # self.plot_2dataframes(...)

    def solver_model(
        self, peaks_list: List[Dict[str, Dict[str, Dict[str, Any]]]]
    ) -> None:
        """Solver model class."""
        PostProcessing(
            self.df,
            {
                "global_": self.global_,
            },
            *SolverModels(
                df=self.df,
                args={
                    "global_": self.global_,
                    "column": list(self.df.columns),
                    "autopeak": self.autopeak,
                    **self.converter_list2dict(peaks_list=peaks_list),
                },
            )(),
        )()

    @staticmethod
    def converter_list2dict(
        peaks_list: List[Dict[str, Dict[str, Dict[str, Any]]]]
    ) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Convert the list of peaks to dictionary.

        # TODO: Using Pydantic DistributionModelAPI to check models
        """
        peaks_dict: Dict[str, Dict[Any, Any]] = {"peaks": {}}
        for i, peak in enumerate(peaks_list, start=1):
            if list(peak.keys())[0] in DistributionModelAPI().__dict__.keys():
                peaks_dict["peaks"][f"{i}"] = peak
        return peaks_dict

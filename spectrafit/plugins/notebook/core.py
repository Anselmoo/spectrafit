"""Core SpectraFitNotebook class for Jupyter notebooks.

This module contains the SpectraFitNotebook class which combines all notebook
functionality for data analysis in Jupyter notebooks.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.models_model import ConfIntervalAPI
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
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.models.builtin import SolverModels
from spectrafit.plugins.notebook.display import DataFrameDisplay
from spectrafit.plugins.notebook.export import ExportReport
from spectrafit.plugins.notebook.export import ExportResults
from spectrafit.plugins.notebook.plotting import DataFramePlot
from spectrafit.plugins.notebook.solver import SolverResults
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.utilities.transformer import list2dict


# Constants
MIN_DATAFRAME_COLUMNS = 2  # Minimum number of columns required in a dataframe


class SpectraFitNotebook(DataFramePlot, DataFrameDisplay, ExportResults):
    """Jupyter Notebook plugin for SpectraFit."""

    args: dict[str, Any]
    global_: bool | int = False
    autopeak: bool = False
    df_fit: pd.DataFrame
    df_pre: pd.DataFrame = pd.DataFrame()
    df_metric: pd.DataFrame = pd.DataFrame()
    df_peaks: pd.DataFrame = pd.DataFrame()
    initial_model: list[dict[str, dict[str, dict[str, Any]]]]

    def __init__(  # noqa: C901
        self,
        df: pd.DataFrame,
        x_column: str,
        y_column: str | list[str],
        oversampling: bool = False,
        smooth: int = 0,
        shift: float = 0,
        energy_start: float | None = None,
        energy_stop: float | None = None,
        title: str | None = None,
        xaxis_title: XAxisAPI | None = None,
        yaxis_title: YAxisAPI | None = None,
        residual_title: ResidualAPI | None = None,
        metric_title: MetricAPI | None = None,
        run_title: RunAPI | None = None,
        legend_title: str = "Spectra",
        show_legend: bool = True,
        legend: LegendAPI | None = None,
        font: FontAPI | None = None,
        minor_ticks: bool = True,
        color: ColorAPI | None = None,
        grid: GridAPI | None = None,
        size: tuple[int, tuple[int, int]] = (800, (600, 300)),
        fname: str = "results",
        folder: str | None = None,
        description: DescriptionAPI | None = None,
    ) -> None:
        """Initialize the SpectraFitNotebook class.

        !!! info "About `Pydantic`-Definition"

            For being consistent with the `SpectraFit` class, the `SpectraFitNotebook`
            class refers to the `Pydantic`-Definition of the `SpectraFit` class.
            Currently, the following definitions are used:

            - `XAxisAPI`: Definition of the x-axis including units
            - `YAxisAPI`: Definition of the y-axis including units
            - `ResidualAPI`: Definition of the residual including units
            - `LegendAPI`: Definition of the legend according to `Plotly`
            - `FontAPI`: Definition of the font according to `Plotly`, which can be
                replaced by _built-in_ definitions
            - `ColorAPI`: Definition of the colors according to `Plotly`, which can be
                replace by _built-in_ definitions
            - `GridAPI`: Definition of the grid according to `Plotly`
            - `DescriptionAPI`: Definition of the description of the fit project

            All classes can be replaced by the corresponding `dict`-definition.

            ```python
            LegendAPI(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            ```

            can be also

            ```python
            dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            ```

        Args:
            df (pd.DataFrame): Dataframe with the data to fit.
            x_column (str): Name of the x column.
            y_column (Union[str, List[str]]): Name of the y column(s).
            oversampling (bool, optional): Activate the oversampling options.
                 Defaults to False.
            smooth (int, optional): Activate the smoothing functions setting an
                 `int>0`. Defaults to 0.
            shift (float, optional): Apply shift to the x-column. Defaults to 0.
            energy_start (Optional[float], optional): Energy start. Defaults to None.
            energy_stop (Optional[float], optional): Energy stop. Defaults to None.
            title (Optional[str], optional): Plot title. Defaults to None.
            xaxis_title (XAxisAPI, optional): X-Axis title. Defaults to XAxisAPI().
            yaxis_title (YAxisAPI, optional): Y-Axis title. Defaults to YAxisAPI().
            residual_title (ResidualAPI, optional): Residual title. Defaults to
                 ResidualAPI().
            metric_title (MetricAPI, optional): Metric title for both axes, bar and
                 line plot. Defaults to MetricAPI().
            run_title (RunAPI, optional): Run title. Defaults to RunAPI().
            legend_title (str, optional): Legend title. Defaults to "Spectra".
            show_legend (bool, optional): Show legend. Defaults to True.
            legend (LegendAPI, optional): Legend options. Defaults to LegendAPI().
            font (FontAPI, optional): Font options. Defaults to FontAPI().
            minor_ticks (bool, optional): Show minor ticks. Defaults to True.
            color (ColorAPI, optional): Color options. Defaults to ColorAPI().
            grid (GridAPI, optional): Grid options. Defaults to GridAPI().
            size (Tuple[int, Tuple[int, int]] , optional): Size of the fit- and metric-
                 plot. First width defines the fit, the second the metrics.
                 Defaults to (800, (600,300)).
            fname (str, optional): Filename of the export. Defaults to "results".
            folder (Optional[str], optional): Folder of the export. Defaults to None.
            description (DescriptionAPI, optional): Description of the data. Defaults
                 to DescriptionAPI()..


        Raises:
            ValueError: If the dataframe only contains one column.

        """
        self.x_column = x_column
        self.y_column = y_column

        if df.shape[1] < MIN_DATAFRAME_COLUMNS:
            msg = f"The dataframe must have {MIN_DATAFRAME_COLUMNS} or more columns."
            raise ValueError(msg)

        if isinstance(self.y_column, list):
            self.global_ = 1
            self.df = df[[self.x_column, *self.y_column]]
        else:
            self.df = df[[self.x_column, self.y_column]]
        self.df_org = self.df.copy()

        self.args_pre = DataPreProcessingAPI(
            oversampling=oversampling,
            energy_start=energy_start,
            energy_stop=energy_stop,
            smooth=smooth,
            shift=shift,
            column=list(self.df.columns),
        )
        # Initialize default value for description if None
        if description is None:
            description = DescriptionAPI()
        self.args_desc = description

        # Initialize default values for all API objects if None
        if xaxis_title is None:
            xaxis_title = XAxisAPI(name="Energy", unit="eV")
        if yaxis_title is None:
            yaxis_title = YAxisAPI(name="Intensity", unit="a.u.")
        if residual_title is None:
            residual_title = ResidualAPI(name="Residual", unit="a.u.")
        if metric_title is None:
            metric_title = MetricAPI(
                name_0="Metrics",
                unit_0="a.u.",
                name_1="Metrics",
                unit_1="a.u.",
            )
        if run_title is None:
            run_title = RunAPI(name="Run", unit="#")
        if legend is None:
            legend = LegendAPI(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            )
        if font is None:
            font = FontAPI(family="Open Sans, monospace", size=12, color="black")
        if color is None:
            color = ColorAPI()
        if grid is None:
            grid = GridAPI()

        self.args_plot = PlotAPI(
            x=self.x_column,
            y=self.y_column,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            residual_title=residual_title,
            metric_title=metric_title,
            run_title=run_title,
            legend_title=legend_title,
            show_legend=show_legend,
            legend=legend,
            font=font,
            minor_ticks=minor_ticks,
            color=color,
            grid=grid,
            size=size,
        )
        self.export_args_df = FnameAPI(fname=fname, folder=folder, suffix="csv")
        self.export_args_out = FnameAPI(fname=fname, folder=folder, suffix="lock")

        self.settings_solver_models: SolverModelsAPI = SolverModelsAPI()
        self.pre_statistic: dict[str, Any] = {}

    @property
    def pre_process(self) -> None:
        """Pre-processing class."""
        self.df, _pre_statistic = PreProcessing(
            df=self.df,
            args=self.args_pre.model_dump(),
        )()
        self.pre_statistic = _pre_statistic["data_statistic"]
        self.df_pre = self.df.copy()

    @property
    def return_pre_statistic(self) -> dict[str, Any]:
        """Return the pre-processing statistic."""
        return self.pre_statistic

    @property
    def return_df_org(self) -> pd.DataFrame:
        """Return the original dataframe."""
        return self.df_org

    @property
    def return_df_pre(self) -> pd.DataFrame | None:
        """Return the pre-processed dataframe."""
        return self.df_pre

    @property
    def return_df(self) -> pd.DataFrame:
        """Return the dataframe."""
        return self.df

    @property
    def return_df_fit(self) -> pd.DataFrame:
        """Return the fit dataframe."""
        return self.df_fit

    @property
    def export_df_act(self) -> None:
        """Export the dataframe."""
        self.export_args_df.prefix = "act"
        self.export_df(df=self.df, args=self.export_args_df)

    @property
    def export_df_fit(self) -> None:
        """Export the dataframe."""
        self.export_args_df.prefix = "fit"
        self.export_df(df=self.df_fit, args=self.export_args_df)

    @property
    def export_df_org(self) -> None:
        """Export the dataframe."""
        self.export_args_df.prefix = "org"
        self.export_df(df=self.df_org, args=self.export_args_df)

    @property
    def export_df_pre(self) -> None:
        """Export the dataframe."""
        if self.df_pre.empty is False:
            self.export_args_df.prefix = "pre"
            self.export_df(df=self.df_pre, args=self.export_args_df)

    @property
    def export_df_metric(self) -> None:
        """Export the dataframe."""
        if self.df_metric.empty is False:
            self.export_args_df.prefix = "metric"
            self.export_df(df=self.df_metric, args=self.export_args_df)

    @property
    def export_df_peaks(self) -> None:
        """Export the dataframe."""
        if self.df_peaks.empty is False:
            self.export_args_df.prefix = "peaks"
            self.export_df(df=self.df_peaks, args=self.export_args_df)

    @property
    def plot_original_df(self) -> None:
        """Plot the original spectra."""
        self.plot_dataframe(args_plot=self.args_plot, df=self.df_org)

    @property
    def plot_current_df(self) -> None:
        """Plot the current spectra."""
        self.plot_dataframe(args_plot=self.args_plot, df=self.df)

    @property
    def plot_preprocessed_df(self) -> None:
        """Plot the current processed spectra."""
        self.plot_2dataframes(
            args_plot=self.args_plot,
            df_1=self.df_pre,
            df_2=self.df_org,
        )

    def plot_fit_df(self) -> None:
        """Plot the fit."""
        if self.global_ == 1:
            self.plot_global_fit(args_plot=self.args_plot, df=self.df_fit)
        else:
            self.plot_2dataframes(args_plot=self.args_plot, df_1=self.df_fit)

    def plot_current_metric(
        self,
        bar_criteria: str | list[str] | None = None,
        line_criteria: str | list[str] | None = None,
    ) -> None:
        """Plot the current metric.

        Args:
            bar_criteria (Optional[Union[str, List[str]]], optional): Criteria for the
                    bar plot. Defaults to None.
            line_criteria (Optional[Union[str, List[str]]], optional): Criteria for
                    the line plot. Defaults to None.

        """
        if bar_criteria is None:
            bar_criteria = [
                "akaike_information",
                "bayesian_information",
            ]

        if line_criteria is None:
            line_criteria = [
                "mean_squared_error",
            ]

        self.plot_metric(
            args_plot=self.args_plot,
            df_metric=self.df_metric,
            bar_criteria=bar_criteria,
            line_criteria=line_criteria,
        )

    @property
    def generate_report(self) -> None:
        """Generate the SpectraFit report of the final fit."""
        self.export_report(
            report=ExportReport(
                description=self.args_desc,
                initial_model=self.initial_model,
                pre_processing=self.args_pre,
                settings_solver_models=self.settings_solver_models,
                fname=self.export_args_out,
                args_out=self.args,
                df_org=self.df_org,
                df_pre=self.df_pre,
                df_fit=self.df_fit,
            )(),
            args=self.export_args_out,
        )

    def solver_model(
        self,
        initial_model: list[dict[str, dict[str, dict[str, Any]]]],
        *,
        show_plot: bool = True,
        show_metric: bool = True,
        show_df: bool = False,
        show_peaks: bool = False,
        conf_interval: bool | dict[str, Any] = False,
        bar_criteria: str | list[str] | None = None,
        line_criteria: str | list[str] | None = None,
        solver_settings: dict[str, Any] | None = None,
    ) -> None:
        """Solves the fit problem based on the proposed model.

        Args:
            initial_model (List[Dict[str, Dict[str, Dict[str, Any]]]]): List of
                 dictionary with the initial model and its fitting parameters and
                 options for the components.
            show_plot (bool, optional): Show current fit results as plot.
                 Defaults to True.
            show_metric (bool, optional): Show the metric of the fit. Defaults to True.
            show_df (bool, optional): Show current fit results as dataframe. Defaults
                 to False.
            show_peaks (bool, optional): Show the peaks of fit. Defaults to False.
            conf_interval (Union[bool,Dict[str, Any]], optional): Bool or dictionary for
                 the parameter with the parameter for calculating the confidence
                 interval. Using `conf_interval=False` turns of the calculation of
                 the confidence interval and accelerate its. Defaults to False.
            bar_criteria (Optional[Union[str, List[str]]], optional): Criteria for the
                bar plot. It is recommended to use attributes from `goodness of fit`
                module. Defaults to None.
            line_criteria (Optional[Union[str, List[str]]], optional): Criteria for
                the line plot. It is recommended to use attributes from
                `regression metric` module. Defaults to None.
            solver_settings (Optional[Dict[str, Any]], optional): Settings for
                the solver models, which is split into settings for `minimizer` and
                `optimizer`.  Defaults to None.

        !!! info: "About criteria"

            The criteria for the bar and line plot are defined as a list of strings.
            The supported keywords are defined by the built-in metrics for
            `goodness of fit` and `regression` and can be checked in [documentation](
                https://anselmoo.github.io/spectrafit/doc/statistics/
            ).

        """
        self.initial_model = initial_model

        if isinstance(conf_interval, bool):
            conf_interval = (
                ConfIntervalAPI().model_dump() if conf_interval is True else False
            )
        elif isinstance(conf_interval, dict):
            conf_interval = ConfIntervalAPI(**conf_interval).model_dump(
                exclude_none=True
            )

        if solver_settings is not None and isinstance(solver_settings, dict):
            self.settings_solver_models = SolverModelsAPI(**solver_settings)

        self.df_fit, self.args = PostProcessing(
            self.df,
            {
                "global_": self.global_,
                "conf_interval": conf_interval,
            },
            *SolverModels(
                df=self.df,
                args={
                    "global_": self.global_,
                    "column": list(self.df.columns),
                    "autopeak": self.autopeak,
                    **list2dict(peak_list=self.initial_model),
                    **self.settings_solver_models.model_dump(),
                },
            )(),
        )()
        self.update_metric()
        self.update_peaks()
        if show_plot:
            self.plot_fit_df()

        if show_metric:
            self.plot_current_metric(
                bar_criteria=bar_criteria,
                line_criteria=line_criteria,
            )

        if show_df:
            self.interactive_display(df=self.df_fit)

        if show_peaks:
            self.interactive_display(df=self.df_peaks)

    def update_peaks(self) -> None:
        """Update the peaks dataframe as multi-column dataframe.

        The multi-column dataframe is used for the interactive display of the
        peaks with initial, current (model), and best fit values.
        """
        tuples = []
        _list = []
        for key_1, _dict in self.args["fit_insights"]["variables"].items():
            tuples.extend([(key_1, key_2) for key_2, val in _dict.items()])
            _list.extend([val for _, val in _dict.items()])

        self.df_peaks = pd.concat(
            [
                self.df_peaks,
                pd.DataFrame(
                    pd.Series(
                        _list,
                        index=pd.MultiIndex.from_tuples(
                            tuples,
                            names=["component", "parameter"],
                        ),
                    ),
                ).T,
            ],
            ignore_index=True,
        )

    def update_metric(self) -> None:
        """Update the metric dataframe."""
        self.df_metric = pd.concat(
            [self.df_metric, SolverResults(self.args).get_current_metric],
            ignore_index=True,
        )

    def display_fit_df(self, mode: str | None = "regular") -> None:
        """Display the fit dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".

        """
        self.df_display(df=self.df_fit, mode=mode)

    def display_preprocessed_df(self, mode: str | None = "regular") -> None:
        """Display the preprocessed dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".

        """
        self.df_display(df=self.df_pre, mode=mode)

    def display_original_df(self, mode: str | None = "regular") -> None:
        """Display the original dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".

        """
        self.df_display(df=self.df_org, mode=mode)

    def display_current_df(self, mode: str | None = "regular") -> None:
        """Display the current dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".

        """
        self.df_display(df=self.df, mode=mode)

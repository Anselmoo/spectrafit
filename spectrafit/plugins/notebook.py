"""Jupyter Notebook plugin for SpectraFit."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

import pandas as pd
import plotly.express as px
import tomli_w

from dtale import show as dtale_show
from IPython.display import display
from IPython.display import display_markdown
from itables import show as itables_show
from plotly.subplots import make_subplots
from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.api.notebook_model import ColorAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.notebook_model import FontAPI
from spectrafit.api.notebook_model import GridAPI
from spectrafit.api.notebook_model import LegendAPI
from spectrafit.api.notebook_model import PlotAPI
from spectrafit.api.notebook_model import ResidualAPI
from spectrafit.api.notebook_model import XAxisAPI
from spectrafit.api.notebook_model import YAxisAPI
from spectrafit.api.report_model import FitMethodAPI
from spectrafit.api.report_model import InputAPI
from spectrafit.api.report_model import OutputAPI
from spectrafit.api.report_model import ReportAPI
from spectrafit.api.report_model import SolverAPI
from spectrafit.api.tools_model import ColumnNamesAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.models import SolverModels
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.utilities.transformer import list2dict


class DataFrameDisplay:
    """Class for displaying a dataframe in different ways."""

    def df_display(self, df: pd.DataFrame, mode: Optional[str] = None) -> None:
        """Call the DataframeDisplay class.

        !!! info "About `df_display`"

            This function is used to display a dataframe in two different ways.

            1. Regular display mode:
                1. Via `IPython.display` for regular sliced displaying of the dataframe
                   in the notebook.
                2. Via `IPython.display` as Markdown for regular displaying of the
                    complete dataframe in the notebook.
            2. Interactive display mode:
                1. Via `itables` for interactive displaying of the dataframe in the
                    notebook, which allows for sorting, filtering, and jumping. For
                    more information see [itables](https://github.com/mwouts/itables).
                2. Via `dtale` for interactive displaying of the dataframe in the
                    notebook, which allows advanced data analysis of the dataframe in
                    an external window. For more information see
                    [dtale](https://github.com/man-group/dtale).

        Args:
            df (pd.DataFrame): Dataframe to display.
            mode (str, Optional): Display mode. Defaults to None.

        Raises:
            ValueError: Raises ValueError if mode of displaying is not supported.
        """
        if mode == "regular":
            self.regular_display(df=df)
        elif mode == "markdown":
            self.markdown_display(df=df)
        elif mode == "interactive":
            self.interactive_display(df=df)
        elif mode == "dtale":
            self.dtale_display(df=df)
        elif mode is not None:
            raise ValueError(
                f"Invalid mode: {mode}. "
                "Valid modes are: regular, interactive, dtale, markdown."
            )

    @staticmethod
    def regular_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a regular way.

        Args:
            df (pd.DataFrame): Dataframe to display.
        """
        display(df)

    @staticmethod
    def interactive_display(df: pd.DataFrame) -> None:
        """Display the dataframe in an interactive way.

        Args:
            df (pd.DataFrame): Dataframe to display.
        """
        itables_show(df)

    @staticmethod
    def dtale_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a dtale way.

        Args:
            df (pd.DataFrame): Dataframe to display.
        """
        dtale_show(df)

    @staticmethod
    def markdown_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a markdown way.

        Args:
            df (pd.DataFrame): Dataframe to display.
        """
        display_markdown(df.to_markdown(), raw=True)


class DataFramePlot:
    """Class to plot a dataframe."""

    def __init__(self, args_plot: PlotAPI) -> None:
        """Initialize the DataFramePlot class.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
        """
        self.args_plot = args_plot

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
            minor=self.get_minor,
            gridcolor=self.args_plot.color.grid,
            linecolor=self.args_plot.color.line,
            zerolinecolor=self.args_plot.color.zero_line,
            color=self.args_plot.color.color,
        )
        fig.update_yaxes(
            minor=self.get_minor,
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
            showlegend=self.args_plot.show_legend,
            width=self.args_plot.size[0],
            height=self.args_plot.size[1],
            paper_bgcolor=self.args_plot.color.paper,
            plot_bgcolor=self.args_plot.color.plot,
        )

        fig.update_xaxes(
            minor=self.get_minor,
            gridcolor=self.args_plot.color.grid,
            linecolor=self.args_plot.color.line,
            zerolinecolor=self.args_plot.color.zero_line,
            color=self.args_plot.color.color,
        )
        fig.update_yaxes(minor=self.get_minor)

        fig.show()

    @property
    def get_minor(self) -> Dict[str, Union[str, bool]]:
        """Get the minor axis arguments."""
        return dict(
            tickcolor=self.args_plot.color.ticks,
            showgrid=self.args_plot.grid.show,
            ticks=self.args_plot.grid.ticks,
            griddash=self.args_plot.grid.dash,
        )


class ExportResults:
    """Class for exporting results as csv."""

    def export_df(self, df: pd.DataFrame, args: FnameAPI) -> None:
        """Export the dataframe as csv."""
        df.to_csv(
            self.fname2Path(
                fname=args.fname,
                prefix=args.prefix,
                suffix=args.suffix,
                folder=args.folder,
            ),
            index=False,
        )

    def export_report(self, report: Dict[Any, Any], args: FnameAPI) -> None:
        """Export the results as toml file.

        Args:
            report (Dict[Any, Any]): _description_
            args (FnameAPI): _description_
        """
        with open(
            self.fname2Path(
                fname=args.fname,
                prefix=args.prefix,
                suffix=args.suffix,
                folder=args.folder,
            ),
            "wb+",
        ) as f:
            tomli_w.dump(report, f)

    @staticmethod
    def fname2Path(
        fname: str,
        suffix: str,
        prefix: Optional[str] = None,
        folder: Optional[str] = None,
    ) -> Path:
        """Translate string to Path object.

        Args:
            fname (str): Filename
            suffix (str): Name of the suffix of the file.
            prefix (Optional[str], optional): Name of the prefix of the file. Defaults
                 to None.
            folder (Optional[str], optional): Folder, where it will be saved.
                 This folders will be created, if not exist. Defaults to None.

        Returns:
            Path: Path object of the file.
        """
        if prefix:
            fname = f"{prefix}_{fname}"
        _fname = Path(fname).with_suffix(f".{suffix}")
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)
            _fname = Path(folder) / _fname
        return _fname


class SolverResults:
    """Class for storing the results of the solver."""

    def __init__(self, args_out: Dict[str, Any]) -> None:
        """Initialize the SolverResults class.

        Args:
            args_out (Dict[str, Any]): Dictionary of SpectraFit settings and results.
        """
        self.args_out = args_out

    @property
    def settings_global_fitting(self) -> Union[bool, int]:
        """Global fitting settings.

        Returns:
            Union[bool, int]: Global fitting settings.
        """
        return self.args_out["global_"]

    @property
    def settings_configurations(self) -> Dict[str, Any]:
        """Configuration settings.

        Returns:
            Dict[str, Any]: Configuration settings.
        """
        return self.args_out["fit_insights"]["configurations"]

    @property
    def get_gof(self) -> Dict[str, float]:
        """Get the goodness of fit values.

        Args:
            export_df (bool, optional): Export the dictionary as dataframe, if True.
                 Defaults to False.

        Returns:
            Dict[str, float]: Goodness of fit values as dictionary.
        """
        return self.args_out["fit_insights"]["statistics"]

    @property
    def get_variables(self) -> Dict[str, Dict[str, float]]:
        """Get the variables of the fit.

        Returns:
            Dict[str, Dict[str, float]]: Variables of the fit.
        """
        return self.args_out["fit_insights"]["variables"]

    @property
    def get_errorbars(self) -> Dict[str, float]:
        """Get the comments about the error bars of fit values.

        Returns:
            Dict[str, float]: Comments about the error bars as dictionary or dataframe.
        """
        return self.args_out["fit_insights"]["errorbars"]

    @property
    def get_component_correlation(self) -> Dict[str, Any]:
        """Get the linear correlation of the components.

        Returns:
            Dict[str, Any]: Linear correlation of the components as dictionary.
        """
        return self.args_out["fit_insights"]["correlations"]

    @property
    def get_covariance_matrix(self) -> Dict[str, Any]:
        """Get the covariance matrix.

        Returns:
            Dict[str, Any]: Covariance matrix as dictionary.
        """
        return self.args_out["fit_insights"]["covariance_matrix"]

    @property
    def get_regression_metrics(self) -> Dict[str, Any]:
        """Get the regression metrics.

        Returns:
            Dict[str, Any]: Regression metrics as dictionary.
        """
        return self.args_out["regression_metrics"]

    @property
    def get_descriptive_statistic(self) -> Dict[str, Any]:
        """Get the descriptive statistic.

        Returns:
            Dict[str, Any]: Descriptive statistic as dictionary of the spectra, fit, and
                 components as dictionary.
        """
        return self.args_out["descriptive_statistic"]

    @property
    def get_linear_correlation(self) -> Dict[str, Any]:
        """Get the linear correlation.

        Returns:
            Dict[str, Any]: Linear correlation of the spectra, fit, and components
                 as dictionary.
        """
        return self.args_out["linear_correlation"]

    @property
    def settings_conf_interval(self) -> Dict[str, Any]:
        """Confidence interval settings.

        Returns:
            Dict[str, Any]: Confidence interval settings.
        """
        return self.args_out["conf_interval"]

    @property
    def get_confidence_interval(self) -> Dict[Any, Any]:
        """Get the confidence interval.

        Returns:
            Dict[Any, Any]: Confidence interval as dictionary.
        """
        return self.args_out["confidence_interval"]


class ExportReport(SolverResults):
    """Class for exporting results as toml."""

    def __init__(
        self,
        description: DescriptionAPI,
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
        pre_processing: DataPreProcessingAPI,
        fname: FnameAPI,
        args_out: Dict[str, Any],
        df_org: pd.DataFrame,
        df_fit: pd.DataFrame,
        df_pre: pd.DataFrame = pd.DataFrame(),
    ):
        """Initialize the ExportReport class.

        Args:
            description (DescriptionAPI): _description_
            initial_model (List[Dict[str, Dict[str, Dict[str, Any]]]]): _description_
            pre_processing (DataPreProcessingAPI): _description_
            fname (FnameAPI): _description_
            args_out (Dict[str, Any]): _description_
            df_org (pd.DataFrame): _description_
            df_fit (pd.DataFrame): _description_
            df_pre (Optional[pd.DataFrame], optional): _description_. Defaults to None.
        """
        super().__init__(args_out=args_out)
        self.description = description
        self.initial_model = initial_model
        self.pre_processing = pre_processing
        self.fname = fname

        self.df_org = df_org.to_dict(orient="list")
        self.df_fit = df_fit.to_dict(orient="list")
        self.df_pre = df_pre.to_dict(orient="list")

    @property
    def make_input_contribution(self) -> InputAPI:
        """Make input contribution of the report.

        Returns:
            InputAPI: Input contribution of the report as class.
        """
        return InputAPI(
            description=self.description,
            initial_model=self.initial_model,
            pre_processing=self.pre_processing,
            method=FitMethodAPI(
                global_fitting=self.settings_global_fitting,
                confidence_interval=self.settings_conf_interval,
                configurations=self.settings_configurations,
            ),
        )

    @property
    def make_solver_contribution(self) -> SolverAPI:
        """Make solver contribution of the report.

        Returns:
            SolverAPI: Solver contribution of the report as class.
        """
        return SolverAPI(
            goodness_of_fit=self.get_gof,
            regression_metrics=self.get_regression_metrics,
            descriptive_statistic=self.get_descriptive_statistic,
            linear_correlation=self.get_linear_correlation,
            component_correlation=self.get_component_correlation,
            confidence_interval=self.get_confidence_interval,
            covariance_matrix=self.get_component_correlation,
            variables=self.get_variables,
            errorbars=self.get_errorbars,
        )

    @property
    def make_output_contribution(self) -> OutputAPI:
        """Make output contribution of the report.

        Returns:
            OutputAPI: Output contribution of the report as class.
        """
        return OutputAPI(df_org=self.df_org, df_fit=self.df_fit, df_pre=self.df_pre)

    def __call__(self) -> Dict[str, Any]:
        """Get the complete report as dictionary.

        Returns:
            Dict[str, Any]: Report as dictionary by using the `.dict()` option of
                 pydantic. `None` is excluded.
        """
        return ReportAPI(
            input=self.make_input_contribution,
            solver=self.make_solver_contribution,
            output=self.make_output_contribution,
        ).dict(exclude_none=True)


class SpectraFitNotebook(DataFramePlot, DataFrameDisplay, ExportResults, ExportReport):
    """Jupyter Notebook plugin for SpectraFit."""

    global_: Union[bool, int] = False
    autopeak: bool = False
    df_fit: pd.DataFrame
    df_pre: pd.DataFrame = pd.DataFrame()
    initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]]

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
        fname: str = "results",
        folder: Optional[str] = None,
        description: DescriptionAPI = DescriptionAPI(),
    ) -> None:
        """Initialize the SpectraFitNotebook class.

        # TODO:
            - Export of the current component model
            - Export pictures
            - Showing current goodness of fit

        Args:
            df (pd.DataFrame): Dataframe with the data to fit.
            x_column (str): Name of the x column
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
            fname (str, optional): _description_. Defaults to "results".
            folder (Optional[str], optional): _description_. Defaults to None.

        Raises:
            ValueError: If the dataframe only contains one column.
        """
        self.x_column = x_column
        self.y_column = y_column

        if isinstance(self.y_column, list):
            self.global_ = 1
            self.df = df[[self.x_column, *self.y_column]]
        else:
            self.df = df[[self.x_column, self.y_column]]
        self.df_org = self.df.copy()

        if self.df.shape[1] < 2:
            raise ValueError("The dataframe must have 2 or more columns.")

        self.args_pre = DataPreProcessingAPI(
            oversampling=oversampling,
            energy_start=energy_start,
            energy_stop=energy_stop,
            smooth=smooth,
            shift=shift,
            column=list(self.df.columns),
        )
        self.args_desc = description
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
            ),
        )
        self.export_args_df = FnameAPI(fname=fname, folder=folder, suffix="csv")
        self.export_args_out = FnameAPI(fname=fname, folder=folder, suffix="lock")

        self.args_solver: Dict[str, Any] = {}
        self.pre_statistic: Dict[str, Any] = {}

    @property
    def pre_process(self) -> None:
        """Pre-processing class."""
        self.df, _pre_statistic = PreProcessing(df=self.df, args=self.args_pre.dict())()
        self.pre_statistic = _pre_statistic["data_statistic"]
        self.df_pre = self.df.copy()

    @property
    def return_pre_statistic(self) -> Dict[str, Any]:
        """Return the pre-processing statistic."""
        return self.pre_statistic

    @property
    def return_df_org(self) -> pd.DataFrame:
        """Return the original dataframe."""
        return self.df_org

    @property
    def return_df_pre(self) -> Union[pd.DataFrame, None]:
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
        if self.df_pre:
            self.export_args_df.prefix = "pre"
            self.export_df(df=self.df_pre, args=self.export_args_df)

    @property
    def plot_original_df(self) -> None:
        """Plot the original spectra."""
        self.plot_dataframe(self.df_org)

    @property
    def plot_current_df(self) -> None:
        """Plot the current spectra."""
        self.plot_dataframe(self.df)

    @property
    def plot_preprocessed_df(self) -> None:
        """Plot the current processed spectra."""
        self.plot_2dataframes(df_1=self.df_pre, df_2=self.df_org)

    @property
    def plot_df_fit(self) -> None:
        """Plot the fit."""
        self.plot_2dataframes(df_1=self.df_fit)

    @property
    def generate_report(self) -> None:
        """Generate the SpectraFit report of the final fit."""
        self.export_report(
            report=ExportReport(
                description=self.args_desc,
                initial_model=self.initial_model,
                pre_processing=self.args_pre,
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
        initial_model: List[Dict[str, Dict[str, Dict[str, Any]]]],
        show_plot: bool = True,
        show_df: bool = False,
        conf_interval: Dict[str, Any] = dict(),
    ) -> None:
        """Solves the fit problem based on the proposed model.

        Args:
            initial_model (List[Dict[str, Dict[str, Dict[str, Any]]]]): List of
                 dictionary with the initial model and its fitting parameters and
                 options for the components.
            show_plot (bool, optional): Show current fit results as plot.
                 Defaults to True.
            show_df (bool, optional): Show current fit results as dataframe. Defaults
                 to False.
            conf_interval (Dict[str, Any], optional): Dictionary for the parameter with
                 the parameter for calculating the confidence interval. Defaults to
                 dict().
        """
        self.initial_model = initial_model
        self.df_fit, self.args = PostProcessing(
            self.df,
            {
                "global_": self.global_,
                "conf_interval": ConfIntervalAPI(**conf_interval).dict(
                    exclude_none=True
                ),
            },
            *SolverModels(
                df=self.df,
                args={
                    "global_": self.global_,
                    "column": list(self.df.columns),
                    "autopeak": self.autopeak,
                    **list2dict(list_=self.initial_model),
                },
            )(),
        )()
        if show_plot:
            self.plot_df_fit
        if show_df:
            self.interactive_display(df=self.df_fit)

    def display_df_fit(self, mode: Optional[str] = "regular") -> None:
        """Display the fit dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".
        """
        self.df_display(df=self.df_fit, mode=mode)

    def display_preprocessed_df(self, mode: Optional[str] = "regular") -> None:
        """Display the preprocessed dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".
        """
        self.df_display(df=self.df_pre, mode=mode)

    def display_original_df(self, mode: Optional[str] = "regular") -> None:
        """Display the original dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".
        """
        self.df_display(df=self.df_org, mode=mode)

    def display_current_df(self, mode: Optional[str] = "regular") -> None:
        """Display the current dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".
        """
        self.df_display(df=self.df, mode=mode)

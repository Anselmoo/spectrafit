"""Jupyter Notebook plugin for SpectraFit."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import tomli_w

from IPython.display import display
from IPython.display import display_markdown
from dtale import show as dtale_show
from itables import show as itables_show
from plotly.subplots import make_subplots

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
from spectrafit.api.report_model import FitMethodAPI
from spectrafit.api.report_model import InputAPI
from spectrafit.api.report_model import OutputAPI
from spectrafit.api.report_model import ReportAPI
from spectrafit.api.report_model import SolverAPI
from spectrafit.api.tools_model import ColumnNamesAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.models.builtin import SolverModels
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.tools import exclude_none_dictionary
from spectrafit.tools import transform_nested_types
from spectrafit.utilities.transformer import list2dict


if TYPE_CHECKING:
    from plotly.graph_objects import Figure

# Constants
MIN_DATAFRAME_COLUMNS = 2  # Minimum number of columns required in a dataframe


class DataFrameDisplay:
    """Class for displaying a dataframe in different ways."""

    def df_display(self, df: pd.DataFrame, mode: str | None = None) -> Any | None:
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

        Returns:
            Optional[Any]: Returns the dtale object for plotting in the Jupyter
                 notebook, if mode is `dtale`.

        """
        if mode == "regular":
            self.regular_display(df=df)
        elif mode == "markdown":
            self.markdown_display(df=df)
        elif mode == "interactive":
            self.interactive_display(df=df)
        elif mode == "dtale":
            return self.dtale_display(df=df)
        elif mode is not None:
            msg = (
                f"Invalid mode: {mode}. "
                "Valid modes are: regular, interactive, dtale, markdown."
            )
            raise ValueError(
                msg,
            )
        return None

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
    def dtale_display(df: pd.DataFrame) -> Any:
        """Display the dataframe in a dtale way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        Returns:
            Any: Returns the dtale object for plotting in the Jupyter notebook.

        """
        return dtale_show(df)

    @staticmethod
    def markdown_display(df: pd.DataFrame) -> None:
        """Display the dataframe in a markdown way.

        Args:
            df (pd.DataFrame): Dataframe to display.

        """
        display_markdown(df.to_markdown(), raw=True)


class DataFramePlot:
    """Class to plot a dataframe."""

    def plot_2dataframes(
        self,
        args_plot: PlotAPI,
        df_1: pd.DataFrame,
        df_2: pd.DataFrame | None = None,
    ) -> None:
        """Plot two dataframes.

        !!! info "About the plot"

            The plot is a combination of two plots. The first plot can be the
            residual plot of a fit or the _modified_ data. The second plot can be the
            fit or the original data.

        !!! missing "`line_dash_map`"

            Currently, the `line_dash_map` is not working, and the dash is not
            plotted. This is likely due to the columns not being labeled in the
            dataframe.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df_1 (pd.DataFrame): First dataframe to plot, which will generate
                a fit plot with residual plot. The ratio is 70% to 20% with
                10% space in between.
            df_2 (Optional[pd.DataFrame], optional): Second optional dataframe to
                plot for comparison. In this case, the ratio between the first
                and second plot will be the same. Defaults to None.

        """
        if df_2 is None:
            fig = self._plot_single_dataframe(args_plot, df_1)
        else:
            fig = self._plot_two_dataframes(args_plot, df_1, df_2)

        fig.show(
            config={
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": "plot_of_2_dataframes",
                    "scale": 4,
                },
            },
        )

    def _plot_single_dataframe(self, args_plot: PlotAPI, df: pd.DataFrame) -> Figure:
        """Plot a single dataframe with residuals."""
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.05,
        )

        residual_fig = self._create_residual_plot(df, args_plot)
        fit_fig = self._create_fit_plot(df, args_plot)

        for trace in residual_fig["data"]:
            fig.add_trace(trace, row=1, col=1)
        for trace in fit_fig["data"]:
            fig.add_trace(trace, row=2, col=1)

        self._update_plot_layout(fig, args_plot, df_2_provided=False)
        return fig

    def _plot_two_dataframes(
        self,
        args_plot: PlotAPI,
        df_1: pd.DataFrame,
        df_2: pd.DataFrame,
    ) -> Figure:
        """Plot two dataframes for comparison."""
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            shared_yaxes=True,
            vertical_spacing=0.05,
        )

        fig1 = px.line(df_1, x=args_plot.x, y=args_plot.y)
        fig2 = px.line(df_2, x=args_plot.x, y=args_plot.y)

        for trace in fig1["data"]:
            fig.add_trace(trace, row=1, col=1)
        for trace in fig2["data"]:
            fig.add_trace(trace, row=2, col=1)

        self._update_plot_layout(fig, args_plot, df_2_provided=True)
        return fig

    def _create_residual_plot(self, df: pd.DataFrame, args_plot: PlotAPI) -> Figure:
        """Create the residual plot."""
        return px.line(
            df,
            x=ColumnNamesAPI().energy,
            y=ColumnNamesAPI().residual,
            color_discrete_sequence=[args_plot.color.residual],
        )

    def _create_fit_plot(self, df: pd.DataFrame, args_plot: PlotAPI) -> Figure:
        """Create the fit plot."""
        y_columns = df.columns.drop(
            [ColumnNamesAPI().energy, ColumnNamesAPI().residual],
        )
        color_map = {
            ColumnNamesAPI().intensity: args_plot.color.intensity,
            ColumnNamesAPI().fit: args_plot.color.fit,
            **dict.fromkeys(
                y_columns.drop([ColumnNamesAPI().intensity, ColumnNamesAPI().fit]),
                args_plot.color.components,
            ),
        }
        line_dash_map = {
            ColumnNamesAPI().intensity: "solid",
            ColumnNamesAPI().fit: "longdash",
            **dict.fromkeys(
                y_columns.drop([ColumnNamesAPI().intensity, ColumnNamesAPI().fit]),
                "dash",
            ),
        }
        return px.line(
            df,
            x=ColumnNamesAPI().energy,
            y=y_columns,
            color_discrete_map=color_map,
            line_dash_map=line_dash_map,
        )

    def _update_plot_layout(
        self,
        fig: Figure,
        args_plot: PlotAPI,
        df_2_provided: bool,
    ) -> None:
        """Update the plot layout."""
        height = args_plot.size[1][0]
        self.update_layout_axes(fig, args_plot, height)

        xaxis_title = self.title_text(
            name=args_plot.xaxis_title.name,
            unit=args_plot.xaxis_title.unit,
        )
        yaxis_title = self.title_text(
            name=args_plot.yaxis_title.name,
            unit=args_plot.yaxis_title.unit,
        )

        fig.update_xaxes(title_text=xaxis_title, row=1, col=1)
        fig.update_xaxes(title_text=xaxis_title, row=2, col=1)

        if not df_2_provided:
            residual_title = self.title_text(
                name=args_plot.residual_title.name,
                unit=args_plot.residual_title.unit,
            )
            fig["layout"]["yaxis1"].update(domain=[0.8, 1])
            fig["layout"]["yaxis2"].update(domain=[0, 0.7])
            fig.update_yaxes(title_text=residual_title, row=1, col=1)
            fig.update_yaxes(title_text=yaxis_title, row=2, col=1)

            # Apply y-axis inversion if requested (for main spectrum)
            if args_plot.yaxis_title.invert:
                fig.update_yaxes(autorange="reversed", row=2, col=1)
        else:
            fig.update_yaxes(title_text=yaxis_title, row=1, col=1)
            fig.update_yaxes(title_text=yaxis_title, row=2, col=1)

            # Apply y-axis inversion if requested (for both plots in this layout)
            if args_plot.yaxis_title.invert:
                fig.update_yaxes(autorange="reversed", row=1, col=1)
                fig.update_yaxes(autorange="reversed", row=2, col=1)

    def plot_dataframe(self, args_plot: PlotAPI, df: pd.DataFrame) -> None:
        """Plot the dataframe according to the PlotAPI arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df (pd.DataFrame): Dataframe to plot.

        """
        fig = px.line(df, x=args_plot.x, y=args_plot.y)
        height = args_plot.size[1][0]
        self.update_layout_axes(fig, args_plot, height)

        fig.update_xaxes(
            title_text=self.title_text(
                name=args_plot.xaxis_title.name,
                unit=args_plot.xaxis_title.unit,
            ),
        )
        fig.update_yaxes(
            title_text=self.title_text(
                name=args_plot.yaxis_title.name,
                unit=args_plot.yaxis_title.unit,
            ),
        )
        fig.show(
            config={
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": "plot_dataframe",
                    "scale": 4,
                },
            },
        )

    def plot_global_fit(self, args_plot: PlotAPI, df: pd.DataFrame) -> None:
        """Plot the global dataframe according to the PlotAPI arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df (pd.DataFrame): Dataframe to plot.

        """
        num_fits = df.columns.str.startswith(ColumnNamesAPI().fit).sum()
        for i in range(1, num_fits + 1):
            cols = [col for col in df.columns if col.endswith(f"_{i}")]
            cols.append(ColumnNamesAPI().energy)
            df_subset = df[cols].rename(
                columns={
                    f"{ColumnNamesAPI().intensity}_{i}": ColumnNamesAPI().intensity,
                    f"{ColumnNamesAPI().fit}_{i}": ColumnNamesAPI().fit,
                    f"{ColumnNamesAPI().residual}_{i}": ColumnNamesAPI().residual,
                },
            )
            self.plot_2dataframes(args_plot, df_subset)

    def plot_metric(
        self,
        args_plot: PlotAPI,
        df_metric: pd.DataFrame,
        bar_criteria: str | list[str],
        line_criteria: str | list[str],
    ) -> None:
        """Plot the metric according to the PlotAPI arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            df_metric (pd.DataFrame): Metric dataframe to plot.
            bar_criteria (Union[str, List[str]]): Criteria to plot as bars.
            line_criteria (Union[str, List[str]]): Criteria to plot as lines.

        """
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig_bar = px.bar(
            df_metric,
            y=bar_criteria,
            color_discrete_sequence=args_plot.color.bars,
        )
        fig_line = px.line(
            df_metric,
            y=line_criteria,
            color_discrete_sequence=args_plot.color.lines,
        )
        fig_line.update_traces(mode="lines+markers", yaxis="y2")

        for trace in fig_bar.data:
            fig.add_trace(trace)
        for trace in fig_line.data:
            fig.add_trace(trace)

        fig.update_layout(xaxis_type="category")
        height = args_plot.size[1][1]
        self.update_layout_axes(fig, args_plot, height)

        fig.update_xaxes(
            title_text=self.title_text(
                name=args_plot.run_title.name,
                unit=args_plot.run_title.unit,
            ),
        )
        fig.update_yaxes(
            title_text=self.title_text(
                name=args_plot.metric_title.name_0,
                unit=args_plot.metric_title.unit_0,
            ),
            secondary_y=False,
        )
        fig.update_yaxes(
            title_text=self.title_text(
                name=args_plot.metric_title.name_1,
                unit=args_plot.metric_title.unit_1,
            ),
            secondary_y=True,
        )
        fig.show(
            config={
                "toImageButtonOptions": {
                    "format": "png",
                    "filename": "plot_metric",
                    "scale": 4,
                },
            },
        )

    def update_layout_axes(
        self,
        fig: Figure,
        args_plot: PlotAPI,
        height: int,
    ) -> Figure:
        """Update the layout of the plot.

        Args:
            fig (Figure): Figure to update.
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.
            height (int): Height of the plot.

        Returns:
            Figure: Updated figure.

        """
        fig.update_layout(
            title=args_plot.title,
            legend_title=args_plot.legend_title,
            legend=args_plot.legend.model_dump(),
            font=args_plot.font.model_dump(),
            showlegend=args_plot.show_legend,
            width=args_plot.size[0],
            height=height,
            paper_bgcolor=args_plot.color.paper,
            plot_bgcolor=args_plot.color.plot,
        )

        minor_ticks = self.get_minor(args_plot)

        fig.update_xaxes(
            minor=minor_ticks,
            gridcolor=args_plot.color.grid,
            linecolor=args_plot.color.line,
            zerolinecolor=args_plot.color.zero_line,
            color=args_plot.color.color,
        )
        fig.update_yaxes(
            minor=minor_ticks,
            gridcolor=args_plot.color.grid,
            linecolor=args_plot.color.line,
            zerolinecolor=args_plot.color.zero_line,
            color=args_plot.color.color,
        )
        return fig

    @staticmethod
    def title_text(name: str, unit: str | None = None) -> str:
        """Return the title text.

        Args:
            name (str): Name of the variable.
            unit (Optional[str], optional): Unit of the variable. Defaults to None.

        Returns:
            str: Title text.

        """
        return f"{name} [{unit}]" if unit else name

    def get_minor(self, args_plot: PlotAPI) -> dict[str, str | bool]:
        """Get the minor axis arguments.

        Args:
            args_plot (PlotAPI): PlotAPI object for the settings of the plot.

        Returns:
            Dict[str, Union[str, bool]]: Dictionary with the minor axis arguments.

        """
        return {
            "tickcolor": args_plot.color.ticks,
            "showgrid": args_plot.grid.show,
            "ticks": args_plot.grid.ticks,
            "griddash": args_plot.grid.dash,
        }


class ExportResults:
    """Class for exporting results as csv."""

    def export_df(self, df: pd.DataFrame, args: FnameAPI) -> None:
        """Export the dataframe as csv.

        Args:
            df (pd.DataFrame): Dataframe to export.
            args (FnameAPI): Arguments for the file export including the path, prefix,
                 and suffix.

        """
        df.to_csv(
            self.fname2path(
                fname=args.fname,
                prefix=args.prefix,
                suffix=args.suffix,
                folder=args.folder,
            ),
            index=False,
        )

    def export_report(self, report: dict[Any, Any], args: FnameAPI) -> None:
        """Export the results as toml file.

        Args:
            report (Dict[Any, Any]): Results as dictionary to export.
            args (FnameAPI): Arguments for the file export including the path, prefix,
                 and suffix.

        """
        with self.fname2path(
            fname=args.fname,
            prefix=args.prefix,
            suffix=args.suffix,
            folder=args.folder,
        ).open("wb+") as f:
            tomli_w.dump(report, f)

    @staticmethod
    def fname2path(
        fname: str,
        suffix: str,
        prefix: str | None = None,
        folder: str | None = None,
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

    def __init__(self, args_out: dict[str, Any]) -> None:
        """Initialize the SolverResults class.

        Args:
            args_out (Dict[str, Any]): Dictionary of SpectraFit settings and results.

        """
        self.args_out = args_out

    @property
    def settings_global_fitting(self) -> bool | int:
        """Global fitting settings.

        Returns:
            Union[bool, int]: Global fitting settings.

        """
        return self.args_out["global_"]

    @property
    def settings_configurations(self) -> dict[str, Any]:
        """Configure settings.

        Returns:
            Dict[str, Any]: Configuration settings.

        """
        return self.args_out["fit_insights"]["configurations"]

    @property
    def get_gof(self) -> dict[str, float]:
        """Get the goodness of fit values.

        Returns:
            Dict[str, float]: Goodness of fit values as dictionary.

        """
        return self.args_out["fit_insights"]["statistics"]

    @property
    def get_variables(self) -> dict[str, dict[str, float]]:
        """Get the variables of the fit.

        Returns:
            Dict[str, Dict[str, float]]: Variables of the fit.

        """
        return self.args_out["fit_insights"]["variables"]

    @property
    def get_errorbars(self) -> dict[str, float]:
        """Get the comments about the error bars of fit values.

        Returns:
            Dict[str, float]: Comments about the error bars as dictionary or dataframe.

        """
        return self.args_out["fit_insights"]["errorbars"]

    @property
    def get_component_correlation(self) -> dict[str, Any]:
        """Get the linear correlation of the components.

        Returns:
            Dict[str, Any]: Linear correlation of the components as dictionary.

        """
        return self.args_out["fit_insights"]["correlations"]

    @property
    def get_covariance_matrix(self) -> dict[str, Any]:
        """Get the covariance matrix.

        Returns:
            Dict[str, Any]: Covariance matrix as dictionary.

        """
        return self.args_out["fit_insights"]["covariance_matrix"]

    @property
    def get_regression_metrics(self) -> dict[str, Any]:
        """Get the regression metrics.

        Returns:
            Dict[str, Any]: Regression metrics as dictionary.

        """
        return self.args_out["regression_metrics"]

    @property
    def get_descriptive_statistic(self) -> dict[str, Any]:
        """Get the descriptive statistic.

        Returns:
            Dict[str, Any]: Descriptive statistic as dictionary of the spectra, fit, and
                 components as dictionary.

        """
        return self.args_out["descriptive_statistic"]

    @property
    def get_linear_correlation(self) -> dict[str, Any]:
        """Get the linear correlation.

        Returns:
            Dict[str, Any]: Linear correlation of the spectra, fit, and components
                 as dictionary.

        """
        return self.args_out["linear_correlation"]

    @property
    def get_computational(self) -> dict[str, Any]:
        """Get the computational time.

        Returns:
            Dict[str, Any]: Computational time as dictionary.

        """
        return self.args_out["fit_insights"]["computational"]

    @property
    def settings_conf_interval(self) -> bool | dict[str, Any]:
        """Confidence interval settings.

        Returns:
            Union[bool, Dict[str, Any]]: Confidence interval settings.

        """
        if isinstance(self.args_out["conf_interval"], dict):
            self.args_out["conf_interval"] = {
                key: value if value is not None else {}
                for key, value in self.args_out["conf_interval"].items()
            }
        return self.args_out["conf_interval"]

    @property
    def get_confidence_interval(self) -> dict[Any, Any]:
        """Get the confidence interval.

        Returns:
            Dict[Any, Any]: Confidence interval as dictionary with or without the
                    confidence interval results.

        """
        if self.args_out["conf_interval"] is False:
            return {}
        return self.args_out["confidence_interval"]

    @property
    def get_current_metric(self) -> pd.DataFrame:
        """Get the current metric.

        !!! note "About the regression metrics"

            For using the regression metrics, the `regression_metrics` must be averaged
            to merge the results of the different configurations together with the
            `goodness_of_fit` and `variables` results.

        Returns:
            pd.DataFrame: Current metric based on `regression_metrics` and
            `goodness_of_fit` as dataframe.

        """
        gof = {key: [value] for key, value in self.get_gof.items()}
        reg = {
            key: [np.average(val)]
            for key, val in zip(
                self.get_regression_metrics["index"],
                self.get_regression_metrics["data"],
            )
        }
        metric = {**gof, **reg}
        return pd.DataFrame(metric)


class ExportReport(SolverResults):
    """Class for exporting results as toml."""

    def __init__(
        self,
        description: DescriptionAPI,
        initial_model: list[dict[str, dict[str, dict[str, Any]]]],
        pre_processing: DataPreProcessingAPI,
        settings_solver_models: SolverModelsAPI,
        fname: FnameAPI,
        args_out: dict[str, Any],
        df_org: pd.DataFrame,
        df_fit: pd.DataFrame,
        df_pre: pd.DataFrame | None = None,
    ) -> None:
        """Initialize the ExportReport class.

        Args:
            description (DescriptionAPI): Description of the fit project.
            initial_model (List[Dict[str, Dict[str, Dict[str, Any]]]]): Initial model
                 for the fit.
            pre_processing (DataPreProcessingAPI): Data pre-processing settings.
            settings_solver_models (SolverModelsAPI): Solver models settings.
            fname (FnameAPI): Filename of the fit project including the path, prefix,
                 and suffix.
            args_out (Dict[str, Any]): Dictionary of SpectraFit settings and results.
            df_org (pd.DataFrame): Dataframe of the original data for performing
                 the fit.
            df_fit (pd.DataFrame): Dataframe of the final fit data.
            df_pre (Optional[pd.DataFrame], optional): Dataframe of the pre-processed data.
                 Defaults to None (empty DataFrame).

        """
        super().__init__(args_out=args_out)
        self.description = description
        self.initial_model = initial_model
        self.pre_processing = pre_processing
        self.settings_solver_models = settings_solver_models
        self.fname = fname

        self.df_org = df_org.to_dict(orient="list")
        self.df_fit = df_fit.to_dict(orient="list")
        if df_pre is None:  # pragma: no cover
            df_pre = pd.DataFrame()
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
                settings_solver_models=self.settings_solver_models.model_dump(
                    exclude_none=True,
                ),
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
            covariance_matrix=self.get_covariance_matrix,
            variables=self.get_variables,
            errorbars=self.get_errorbars,
            computational=self.get_computational,
        )

    @property
    def make_output_contribution(self) -> OutputAPI:
        """Make output contribution of the report.

        Returns:
            OutputAPI: Output contribution of the report as class.

        """
        return OutputAPI(df_org=self.df_org, df_fit=self.df_fit, df_pre=self.df_pre)

    def __call__(self) -> dict[str, Any]:
        """Get the complete report as dictionary.

        !!! info "About the report and `exclude_none_dictionary`"

            The report is generated by using the `ReportAPI` class, which is a
            `Pydantic`-definition of the report. The `Pydantic`-definition is
            converted to a dictionary by using the `.model_dump()` option of `Pydantic`.
            The `recursive_exclude_none` function is used to remove all `None` values
            from the dictionary, which are hidden in the nested dictionaries.

        Returns:
            Dict[str, Any]: Report as dictionary by using the `.dict()` option of
                 pydantic. `None` is excluded.

        """
        report = ReportAPI(
            input=self.make_input_contribution,
            solver=self.make_solver_contribution,
            output=self.make_output_contribution,
        ).model_dump(exclude_none=True)
        report = exclude_none_dictionary(report)
        return transform_nested_types(report)


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
            conf_interval = ConfIntervalAPI(**conf_interval).dict(exclude_none=True)

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

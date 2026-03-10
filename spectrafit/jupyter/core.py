"""Core SpectraFitNotebook class for Jupyter notebooks.

This module contains the SpectraFitNotebook class which combines all notebook
functionality for data analysis in Jupyter notebooks.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

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
from spectrafit.core import PostProcessing
from spectrafit.core import PreProcessing
from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.config_io import build_notebook_from_config
from spectrafit.jupyter.config_io import export_notebook_config_toml
from spectrafit.jupyter.config_io import load_notebook_config
from spectrafit.jupyter.config_io import notebook_args_to_config
from spectrafit.jupyter.display import DataFrameDisplay
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.plotting import DataFramePlot
from spectrafit.jupyter.result_projection import append_metric_dataframe
from spectrafit.jupyter.result_projection import append_peaks_dataframe
from spectrafit.jupyter.solver import SolverResults
from spectrafit.jupyter.solver_orchestration import apply_solver_settings
from spectrafit.jupyter.solver_orchestration import build_fit_result
from spectrafit.jupyter.solver_orchestration import resolve_solver_options
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.functions.builtin import SolverModels
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.types import DataSplitDict
from spectrafit.utilities.transformer import LegacyModelSpec


if TYPE_CHECKING:
    from pathlib import Path


# Constants
MIN_DATAFRAME_COLUMNS = 2  # Minimum number of columns required in a dataframe
_PREPROCESS_PLACEHOLDER_COMPONENTS: list[
    dict[
        str, object
    ]  # intentional: nbformat-style component spec for legacy pre-processing bridge
] = [  # intentional: legacy bridge
    {
        "id": "pre",
        "model": "gaussian",
        "parameters": {
            "amplitude": {"value": 1.0, "vary": False},
            "center": {"value": 0.0, "vary": False},
            "fwhmg": {"value": 1.0, "vary": False},
        },
    }
]


def _coerce_split_cell(raw_cell: object) -> float | str | None:
    """Normalize one split-orient cell value."""
    if isinstance(raw_cell, bool):
        return str(raw_cell)
    if isinstance(raw_cell, int | float):
        return float(raw_cell)
    if isinstance(raw_cell, str) or raw_cell is None:
        return raw_cell
    return None


def _coerce_split_rows(raw_rows: object) -> list[list[float | str | None]]:
    """Normalize split-orient data rows."""
    if not isinstance(raw_rows, list):
        return []

    rows: list[list[float | str | None]] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, list):
            continue
        rows.append([_coerce_split_cell(raw_cell) for raw_cell in raw_row])
    return rows


def _coerce_split_axis(raw_axis: object) -> list[int | str]:
    """Normalize split-orient index/column arrays."""
    if not isinstance(raw_axis, list):
        return []
    return [value for value in raw_axis if isinstance(value, int | str)]


def _to_data_split_dict(value: object) -> DataSplitDict:
    """Coerce split-orient payloads into ``DataSplitDict``."""
    if not isinstance(value, dict):
        return DataSplitDict(data=[], index=[], columns=[])

    return DataSplitDict(
        data=_coerce_split_rows(value.get("data", [])),
        index=_coerce_split_axis(value.get("index", [])),
        columns=_coerce_split_axis(value.get("columns", [])),
    )


class SpectraFitNotebook(  # intentional: Facade
    DataFramePlot, DataFrameDisplay, ExportResults
):
    """Jupyter Notebook plugin for SpectraFit."""

    global_: FittingMode
    df_fit: pd.DataFrame
    df_pre: pd.DataFrame
    df_metric: pd.DataFrame
    df_peaks: pd.DataFrame
    initial_model: list[LegacyModelSpec]
    fit_result: FitResult
    _solver_results: SolverResults
    _resolved_ci: ConfIntervalAPI | ConfIntervalConfig | None

    def __init__(  # noqa: C901  # intentional: complex init pending NotebookConfig facade (R8)
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
        self.global_ = FittingMode.STANDARD
        self.df_fit = pd.DataFrame()
        self.df_pre = pd.DataFrame()
        self.df_metric = pd.DataFrame()
        self.df_peaks = pd.DataFrame()

        if df.shape[1] < MIN_DATAFRAME_COLUMNS:
            msg = f"The dataframe must have {MIN_DATAFRAME_COLUMNS} or more columns."
            raise ValueError(msg)

        if isinstance(self.y_column, list):
            self.global_ = FittingMode.GLOBAL
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
        if (
            description is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            description = DescriptionAPI()
        self.args_desc = description

        if (
            xaxis_title is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            xaxis_title = XAxisAPI(name="Energy", unit="eV")
        if (
            yaxis_title is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            yaxis_title = YAxisAPI(name="Intensity", unit="a.u.")
        if residual_title is None:  # intentional: plot API default (R8 facade)
            residual_title = ResidualAPI(name="Residual", unit="a.u.")
        if (
            metric_title is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            metric_title = MetricAPI(
                name_0="Metrics",
                unit_0="a.u.",
                name_1="Metrics",
                unit_1="a.u.",
            )
        if (
            run_title is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            run_title = RunAPI(name="Run", unit="#")
        if (
            legend is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            legend = LegendAPI(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            )
        if (
            font is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            font = FontAPI(family="Open Sans, monospace", size=12, color="black")
        if (
            color is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
            color = ColorAPI()
        if (
            grid is None
        ):  # intentional: plot API default pending NotebookConfig facade (R8)
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
        self.pre_statistic: DataSplitDict = DataSplitDict(data=[], index=[], columns=[])

    @classmethod
    def from_config(
        cls,
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
        **kwargs: object,
    ) -> SpectraFitNotebook:
        """Create a SpectraFitNotebook from a UnifiedFittingConfig.

        This factory method extracts column names and solver settings from the
        unified configuration, allowing a single config object to drive
        notebook construction.

        Args:
            df (pd.DataFrame): Dataframe with the data to fit.
            config (UnifiedFittingConfig): Unified fitting configuration
                containing column mapping, solver settings, and global
                fitting mode.
            **kwargs (object): Additional keyword arguments forwarded to
                ``SpectraFitNotebook.__init__`` (e.g. ``title``, ``fname``).

        Returns:
            SpectraFitNotebook: Configured notebook instance.

        """
        return build_notebook_from_config(
            notebook_cls=cls,
            df=df,
            config=config,
            **kwargs,
        )

    def args_to_config(self) -> UnifiedFittingConfig:
        """Convert the current notebook state to a UnifiedFittingConfig.

        This enables round-tripping between the notebook's internal dict-based
        state and the validated Pydantic configuration model used by the CLI
        and pipeline interfaces.

        Returns:
            UnifiedFittingConfig: Validated configuration reflecting the
                notebook's current components, solver settings, and global mode.

        """
        return notebook_args_to_config(self)

    def preprocess_df(self) -> None:
        """Run pre-processing and update notebook dataframe state."""
        pre_config = UnifiedFittingConfig(
            components=_PREPROCESS_PLACEHOLDER_COMPONENTS,
            column=ColumnConfig(
                x=str(self.args_pre.column[0]),
                y=str(self.args_pre.column[1])
                if len(self.args_pre.column) > 1
                else str(self.args_pre.column[0]),
            ),
            preprocessing=PreprocessingConfig(
                energy_start=self.args_pre.energy_start,
                energy_stop=self.args_pre.energy_stop,
                shift=self.args_pre.shift,
                oversampling=self.args_pre.oversampling,
                smooth=self.args_pre.smooth,
            ),
        )
        pre_result = PreProcessing(
            df=self.df,
            config=pre_config,
        )()
        self.df = pre_result.df
        self.pre_statistic = _to_data_split_dict(pre_result.data_statistic)
        self.df_pre = self.df.copy()

    @property  # intentional: compat shim (R8 will deprecate)
    def pre_process(self) -> None:
        """Compatibility shim for legacy pre-processing property access."""
        self.preprocess_df()

    @property
    def return_pre_statistic(self) -> DataSplitDict:
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

    def export_active_df(self) -> None:
        """Export the current dataframe."""
        self.export_args_df.prefix = "act"
        self.export_df(df=self.df, args=self.export_args_df)

    @property  # intentional: export compat shim (R8 will deprecate)
    def export_df_act(self) -> None:
        """Compatibility shim for active-data export property access."""
        self.export_active_df()

    def export_fit_dataframe(self) -> None:
        """Export the fit dataframe."""
        self.export_args_df.prefix = "fit"
        self.export_df(df=self.df_fit, args=self.export_args_df)

    @property  # intentional: export compat shim (R8 will deprecate)
    def export_df_fit(self) -> None:
        """Compatibility shim for fit-data export property access."""
        self.export_fit_dataframe()

    def export_original_df(self) -> None:
        """Export the original dataframe."""
        self.export_args_df.prefix = "org"
        self.export_df(df=self.df_org, args=self.export_args_df)

    @property  # intentional: export compat shim (R8 will deprecate)
    def export_df_org(self) -> None:
        """Compatibility shim for original-data export property access."""
        self.export_original_df()

    def export_preprocessed_df(self) -> None:
        """Export the pre-processed dataframe when available."""
        if self.df_pre.empty is False:
            self.export_args_df.prefix = "pre"
            self.export_df(df=self.df_pre, args=self.export_args_df)

    @property  # intentional: export compat shim (R8 will deprecate)
    def export_df_pre(self) -> None:
        """Compatibility shim for preprocessed-data export property access."""
        self.export_preprocessed_df()

    def export_metric_df(self) -> None:
        """Export the metrics dataframe when available."""
        if self.df_metric.empty is False:
            self.export_args_df.prefix = "metric"
            self.export_df(df=self.df_metric, args=self.export_args_df)

    @property  # intentional: export compat shim (R8 will deprecate)
    def export_df_metric(self) -> None:
        """Compatibility shim for metric-data export property access."""
        self.export_metric_df()

    def export_peaks_df(self) -> None:
        """Export the peaks dataframe when available."""
        if self.df_peaks.empty is False:
            self.export_args_df.prefix = "peaks"
            self.export_df(df=self.df_peaks, args=self.export_args_df)

    @property  # intentional: export compat shim (R8 will deprecate)
    def export_df_peaks(self) -> None:
        """Compatibility shim for peaks-data export property access."""
        self.export_peaks_df()

    def plot_original(self) -> None:
        """Plot the original spectra."""
        self.plot_dataframe(args_plot=self.args_plot, df=self.df_org)

    @property  # intentional: plot compat shim (R8 will deprecate)
    def plot_original_df(self) -> None:
        """Compatibility shim for original-data plotting property access."""
        self.plot_original()

    def plot_current(self) -> None:
        """Plot the current spectra."""
        self.plot_dataframe(args_plot=self.args_plot, df=self.df)

    @property  # intentional: plot compat shim (R8 will deprecate)
    def plot_current_df(self) -> None:
        """Compatibility shim for current-data plotting property access."""
        self.plot_current()

    def plot_preprocessed(self) -> None:
        """Plot original and preprocessed spectra together."""
        self.plot_2dataframes(
            args_plot=self.args_plot,
            df_1=self.df_pre,
            df_2=self.df_org,
        )

    @property  # intentional: plot compat shim (R8 will deprecate)
    def plot_preprocessed_df(self) -> None:
        """Compatibility shim for preprocessed plotting property access."""
        self.plot_preprocessed()

    def plot_fit_df(self) -> None:
        """Plot the fit."""
        if self.global_ != FittingMode.STANDARD:
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
        if bar_criteria is None:  # intentional: mutable default sentinel
            bar_criteria = [
                "akaike_information",
                "bayesian_information",
            ]

        if line_criteria is None:  # intentional: mutable default sentinel
            line_criteria = [
                "mean_squared_error",
            ]

        self.plot_metric(
            args_plot=self.args_plot,
            df_metric=self.df_metric,
            bar_criteria=bar_criteria,
            line_criteria=line_criteria,
        )

    def generate_fit_report(self) -> None:
        """Generate the SpectraFit report for the final fit."""
        self.export_report(
            report=ExportReport(
                description=self.args_desc,
                initial_model=self.initial_model,
                pre_processing=self.args_pre,
                settings_solver_models=self.settings_solver_models,
                fname=self.export_args_out,
                solver=self._solver_results,
                df_org=self.df_org,
                df_pre=self.df_pre,
                df_fit=self.df_fit,
            )(),
            args=self.export_args_out,
        )

    @property  # intentional: report compat shim (R8 will deprecate)
    def generate_report(self) -> None:
        """Compatibility shim for report-generation property access."""
        self.generate_fit_report()

    def solver_model(
        self,
        initial_model: list[LegacyModelSpec],
        *,
        show_plot: bool = True,
        show_metric: bool = True,
        show_df: bool = False,
        show_peaks: bool = False,
        conf_interval: bool | ConfIntervalAPI | ConfIntervalConfig = False,
        bar_criteria: str | list[str] | None = None,
        line_criteria: str | list[str] | None = None,
        solver_settings: SolverModelsAPI | None = None,
        config: UnifiedFittingConfig | None = None,
    ) -> None:
        """Solves the fit problem based on the proposed model.

        Args:
            initial_model (list[LegacyModelSpec]): List of
                 dictionary with the initial model and its fitting parameters and
                 options for the components.
            show_plot (bool, optional): Show current fit results as plot.
                 Defaults to True.
            show_metric (bool, optional): Show the metric of the fit. Defaults to True.
            show_df (bool, optional): Show current fit results as dataframe. Defaults
                 to False.
            show_peaks (bool, optional): Show the peaks of fit. Defaults to False.
            conf_interval (bool | ConfIntervalAPI | ConfIntervalConfig, optional):
                 Bool or typed model for configuring confidence interval calculation.
                 Using ``conf_interval=False`` turns off the calculation of the
                 confidence interval and accelerates the fit. Defaults to False.
            bar_criteria (Optional[Union[str, List[str]]], optional): Criteria for the
                bar plot. It is recommended to use attributes from `goodness of fit`
                module. Defaults to None.
            line_criteria (Optional[Union[str, List[str]]], optional): Criteria for
                the line plot. It is recommended to use attributes from
                `regression metric` module. Defaults to None.
            solver_settings (SolverModelsAPI | None, optional): Settings for the
                solver models, which is split into settings for ``minimizer`` and
                ``optimizer``. Defaults to None.
            config (UnifiedFittingConfig | None, optional): Unified fitting
                configuration that provides ``conf_interval`` and solver settings.
                When provided, its values override the ``conf_interval`` and
                ``solver_settings`` parameters. Defaults to None.

        !!! info: "About criteria"

            The criteria for the bar and line plot are defined as a list of strings.
            The supported keywords are defined by the built-in metrics for
            `goodness of fit` and `regression` and can be checked in [documentation](
                https://anselmoo.github.io/spectrafit/doc/statistics/
            ).

        """
        self.initial_model = initial_model

        resolved_ci, resolved_solver_settings = resolve_solver_options(
            conf_interval=conf_interval,
            solver_settings=solver_settings,
            config=config,
        )
        self.settings_solver_models = apply_solver_settings(
            current_settings=self.settings_solver_models,
            solver_settings=resolved_solver_settings,
        )

        solver_config = self.args_to_config()
        solver_config.minimizer = self.settings_solver_models.minimizer
        solver_config.optimizer = self.settings_solver_models.optimizer

        minimizer, result = SolverModels(
            df=self.df,
            config=solver_config,
        )()
        post_result = PostProcessing(
            self.df,
            minimizer,
            result,
            is_global=self.global_ != FittingMode.STANDARD,
            conf_interval=(
                resolved_ci.model_dump(exclude_none=True)
                if resolved_ci is not None
                else False
            ),
        )()
        self.df_fit = post_result.df
        self._resolved_ci = resolved_ci

        self.fit_result = build_fit_result(
            global_mode=self.global_,
            minimizer_result=result,
            post_result=post_result,
            resolved_ci=resolved_ci,
        )
        self._solver_results = SolverResults(result=self.fit_result)
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
        self.df_peaks = append_peaks_dataframe(
            df_peaks=self.df_peaks,
            fit_result=self.fit_result,
        )

    def update_metric(self) -> None:
        """Update the metric dataframe."""
        self.df_metric = append_metric_dataframe(
            df_metric=self.df_metric,
            fit_result=self.fit_result,
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

    def export_config_toml(self, path: Path | str, *, force: bool = False) -> None:
        """Serialise the current fit configuration as a v2 TOML file.

        The produced TOML uses the ``[[components]]`` array-of-tables format
        accepted by :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`.
        It can be reloaded via :meth:`load_cli_config` or used directly as
        input for the ``spectrafit fit`` CLI command.

        Args:
            path: Destination path for the ``.toml`` file.
            force: If ``True``, overwrite an existing file without prompting.
                Defaults to ``False``.

        Raises:
            FileExistsError: If *path* already exists and ``force=False``.
        """
        export_notebook_config_toml(
            config=self.args_to_config(),
            path=path,
            force=force,
        )

    @classmethod
    def load_cli_config(cls, path: Path | str) -> UnifiedFittingConfig:
        """Load a v2 TOML config file into a UnifiedFittingConfig.

        This is a lightweight factory that reads a ``.toml`` file produced by
        ``spectrafit new-config``, :meth:`export_config_toml`, or manually
        authored in v2 format, and returns a validated
        :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`.

        Args:
            path: Path to the v2 ``.toml`` (or ``.json``) config file.

        Returns:
            Validated :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If the file cannot be validated as v2 format.

        Examples:
            >>> cfg = SpectraFitNotebook.load_cli_config("config.toml")
            >>> len(cfg.components)
            2
        """
        return load_notebook_config(path=path)

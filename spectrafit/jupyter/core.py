"""Core SpectraFitNotebook class for Jupyter notebooks.

This module contains the SpectraFitNotebook class which combines all notebook
functionality for data analysis in Jupyter notebooks.
"""

from __future__ import annotations

import warnings

from dataclasses import replace
from typing import TYPE_CHECKING

import pandas as pd

from spectrafit.adapters.preprocessing_boundary import NotebookPreprocessingProxy
from spectrafit.adapters.preprocessing_boundary import notebook_boundary_columns
from spectrafit.adapters.preprocessing_boundary import preprocessing_from_boundary
from spectrafit.api.cmd_model import DescriptionAPI
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
from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.core.pipeline import PipelineDependencies
from spectrafit.core.preprocessing import preprocess
from spectrafit.jupyter.config_io import build_notebook_from_config
from spectrafit.jupyter.config_io import export_notebook_config_toml
from spectrafit.jupyter.config_io import load_notebook_config
from spectrafit.jupyter.config_io import notebook_args_to_config
from spectrafit.jupyter.display import DataFrameDisplay
from spectrafit.jupyter.export import ExportReport
from spectrafit.jupyter.export import ExportResults
from spectrafit.jupyter.export import ReportDocument
from spectrafit.jupyter.plotting import DataFramePlot
from spectrafit.jupyter.solver import SolverResults
from spectrafit.jupyter.solver_orchestration import apply_solver_settings
from spectrafit.jupyter.solver_orchestration import resolve_solver_options
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.peak_models import Component
from spectrafit.models.plot_config import PlotConfig
from spectrafit.models.preprocess_result import PreprocessResult
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.split_frame import SplitFrame
from spectrafit.plotting import PlotSpectra
from spectrafit.utilities.transformer import InitialModelLike
from spectrafit.utilities.transformer import LegacyModelSpec
from spectrafit.utilities.transformer import components2legacy_specs
from spectrafit.utilities.transformer import normalize_components


if TYPE_CHECKING:
    from pathlib import Path

    from spectrafit.api.models_model import ConfIntervalAPI


# Constants
MIN_DATAFRAME_COLUMNS = 2  # Minimum number of columns required in a dataframe
_DEFAULT_BAR_CRITERIA = [
    "akaike_information",
    "bayesian_information",
]
_DEFAULT_LINE_CRITERIA = [
    "mean_squared_error",
]
_LEGACY_ACTION_SHIMS = {
    "pre_process": "preprocess_df",
    "export_df_act": "export_active_df",
    "export_df_fit": "export_fit_dataframe",
    "export_df_org": "export_original_df",
    "export_df_pre": "export_preprocessed_df",
    "export_df_metric": "export_metric_df",
    "export_df_peaks": "export_peaks_df",
    "plot_original_df": "plot_original",
    "plot_current_df": "plot_current",
    "plot_preprocessed_df": "plot_preprocessed",
    "generate_report": "generate_fit_report",
}
_PREPROCESS_PLACEHOLDER_COMPONENTS: list[Component] = [
    Component.model_validate(
        {
            "id": "pre",
            "model": "gaussian",
            "parameters": {
                "amplitude": {"value": 1.0, "vary": False},
                "center": {"value": 0.0, "vary": False},
                "fwhmg": {"value": 1.0, "vary": False},
            },
        }
    )
]


def _normalize_y_columns(y_column: str | list[str]) -> list[str]:
    """Normalize notebook y-column input to the canonical internal list shape."""
    return [y_column] if isinstance(y_column, str) else [str(item) for item in y_column]


def _compat_y_column(y_columns: list[str]) -> str | list[str]:
    """Project canonical y-columns to the legacy notebook boundary shape."""
    return y_columns[0] if len(y_columns) == 1 else list(y_columns)


def _warn_legacy_notebook_shim(*, legacy_name: str, canonical_name: str) -> None:
    """Emit a deprecation warning for legacy notebook compatibility shims."""
    warnings.warn(
        (
            f"SpectraFitNotebook.{legacy_name} is a legacy compatibility shim in v2.x; "
            f"use SpectraFitNotebook.{canonical_name} instead. "
            "The shim will be removed in v3.0.0."
        ),
        FutureWarning,
        stacklevel=3,
    )


def _resolve_description(description: DescriptionAPI | None) -> DescriptionAPI:
    """Resolve the notebook description boundary to a concrete API model."""
    return description if description is not None else DescriptionAPI()


def _resolve_plot_api(
    *,
    x_column: str,
    y_column: str | list[str],
    title: str | None,
    xaxis_title: XAxisAPI | None,
    yaxis_title: YAxisAPI | None,
    residual_title: ResidualAPI | None,
    metric_title: MetricAPI | None,
    run_title: RunAPI | None,
    legend_title: str,
    show_legend: bool,
    legend: LegendAPI | None,
    font: FontAPI | None,
    minor_ticks: bool,
    color: ColorAPI | None,
    grid: GridAPI | None,
    size: tuple[int, tuple[int, int]],
) -> PlotAPI:
    """Build the notebook plot API with concrete defaults."""
    return PlotAPI(
        x=x_column,
        y=y_column,
        title=title,
        xaxis_title=(
            xaxis_title
            if xaxis_title is not None
            else XAxisAPI(name="Energy", unit="eV")
        ),
        yaxis_title=(
            yaxis_title
            if yaxis_title is not None
            else YAxisAPI(name="Intensity", unit="a.u.")
        ),
        residual_title=(
            residual_title
            if residual_title is not None
            else ResidualAPI(name="Residual", unit="a.u.")
        ),
        metric_title=(
            metric_title
            if metric_title is not None
            else MetricAPI(
                name_0="Metrics",
                unit_0="a.u.",
                name_1="Metrics",
                unit_1="a.u.",
            )
        ),
        run_title=run_title if run_title is not None else RunAPI(name="Run", unit="#"),
        legend_title=legend_title,
        show_legend=show_legend,
        legend=(
            legend
            if legend is not None
            else LegendAPI(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            )
        ),
        font=(
            font
            if font is not None
            else FontAPI(family="Open Sans, monospace", size=12, color="black")
        ),
        minor_ticks=minor_ticks,
        color=color if color is not None else ColorAPI(),
        grid=grid if grid is not None else GridAPI(),
        size=size,
    )


def _resolve_metric_criteria(
    *,
    bar_criteria: str | list[str] | None,
    line_criteria: str | list[str] | None,
) -> tuple[str | list[str], str | list[str]]:
    """Resolve default plotting criteria for notebook metrics."""
    resolved_bar = (
        bar_criteria if bar_criteria is not None else list(_DEFAULT_BAR_CRITERIA)
    )
    resolved_line = (
        line_criteria if line_criteria is not None else list(_DEFAULT_LINE_CRITERIA)
    )
    return resolved_bar, resolved_line


class SpectraFitNotebook(DataFramePlot):  # intentional: Facade
    """Jupyter Notebook plugin for SpectraFit."""

    _fitting_mode: FittingMode
    df_fit: pd.DataFrame
    df_pre: pd.DataFrame
    df_metric: pd.DataFrame
    df_peaks: pd.DataFrame
    initial_model: list[LegacyModelSpec]
    _initial_components: list[Component]
    fit_result: FitResult
    _solver_results: SolverResults
    _resolved_ci: ConfIntervalConfig | None
    _pipeline_deps: PipelineDependencies
    _preprocessing_config: PreprocessingConfig
    _y_columns: list[str]
    _context_n_datasets: int

    def __init__(  # intentional: complex init pending NotebookConfig facade (R8)
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
            y_column (str | list[str]): Name of the y column(s).
            oversampling (bool, optional): Activate the oversampling options.
                 Defaults to False.
            smooth (int, optional): Activate the smoothing functions setting an
                 `int>0`. Defaults to 0.
            shift (float, optional): Apply shift to the x-column. Defaults to 0.
            energy_start (float | None, optional): Energy start. Defaults to None.
            energy_stop (float | None, optional): Energy stop. Defaults to None.
            title (str | None, optional): Plot title. Defaults to None.
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
            size (tuple[int, tuple[int, int]], optional): Size of the fit- and metric-
                 plot. First width defines the fit, the second the metrics.
                 Defaults to (800, (600,300)).
            fname (str, optional): Filename of the export. Defaults to "results".
            folder (str | None, optional): Folder of the export. Defaults to None.
            description (DescriptionAPI, optional): Description of the data. Defaults
                 to DescriptionAPI()..


        Raises:
            ValueError: If the dataframe only contains one column.

        """
        self.x_column = x_column
        self.y_column = y_column
        self.df_fit = pd.DataFrame()
        self.df_pre = pd.DataFrame()
        self.df_metric = pd.DataFrame()
        self.df_peaks = pd.DataFrame()

        if df.shape[1] < MIN_DATAFRAME_COLUMNS:
            msg = f"The dataframe must have {MIN_DATAFRAME_COLUMNS} or more columns."
            raise ValueError(msg)

        self.df = df[[self.x_column, *self.y_columns]]
        self.df_org = self.df.copy()

        self.preprocessing_config = PreprocessingConfig(
            oversampling=oversampling,
            energy_start=energy_start,
            energy_stop=energy_stop,
            smooth=smooth,
            shift=shift,
        )
        self.args_desc = _resolve_description(description)

        self.args_plot = _resolve_plot_api(
            x_column=self.x_column,
            y_column=self.y_column,
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
        self.pre_statistic: SplitFrame = SplitFrame.empty()
        self._pipeline_deps = PipelineDependencies()
        self._initial_components = []

    def df_display(self, df: pd.DataFrame, mode: str | None = None) -> object | None:
        """Delegate dataframe display behavior through the display helper."""
        return DataFrameDisplay.df_display(self, df=df, mode=mode)

    @staticmethod
    def regular_display(df: pd.DataFrame) -> None:
        """Delegate regular dataframe display through the display helper."""
        DataFrameDisplay.regular_display(df)

    @staticmethod
    def interactive_display(df: pd.DataFrame) -> None:
        """Delegate interactive dataframe display through the display helper."""
        DataFrameDisplay.interactive_display(df)

    @staticmethod
    def dtale_display(df: pd.DataFrame) -> object:
        """Delegate dtale dataframe display through the display helper."""
        return DataFrameDisplay.dtale_display(df)

    @staticmethod
    def markdown_display(df: pd.DataFrame) -> None:
        """Delegate markdown dataframe display through the display helper."""
        DataFrameDisplay.markdown_display(df)

    def export_df(self, df: pd.DataFrame, args: FnameAPI) -> None:
        """Delegate dataframe export through the export helper."""
        ExportResults.export_df(self, df=df, args=args)

    def export_report(self, report: ReportDocument, args: FnameAPI) -> None:
        """Delegate report export through the export helper."""
        ExportResults.export_report(self, report=report, args=args)

    @staticmethod
    def fname2path(
        fname: str,
        suffix: str,
        prefix: str | None = None,
        folder: str | None = None,
    ) -> Path:
        """Delegate path construction through the export helper."""
        return ExportResults.fname2path(
            fname=fname,
            suffix=suffix,
            prefix=prefix,
            folder=folder,
        )

    @property
    def fitting_mode(self) -> FittingMode:
        """Canonical fitting mode for notebook runtime flow."""
        return self._fitting_mode

    @fitting_mode.setter
    def fitting_mode(self, value: FittingMode) -> None:
        """Update the canonical fitting mode for notebook runtime flow."""
        self._fitting_mode = value
        if value == FittingMode.STANDARD:
            self._context_n_datasets = 1
        else:
            self._context_n_datasets = max(
                self._context_n_datasets, len(self.y_columns), 2
            )

    @property
    def global_(self) -> FittingMode:
        """Legacy notebook mode alias retained for compatibility."""
        _warn_legacy_notebook_shim(
            legacy_name="global_",
            canonical_name="fitting_mode",
        )
        return self.fitting_mode

    @global_.setter
    def global_(self, value: FittingMode) -> None:
        """Route legacy notebook mode assignments through the canonical field."""
        _warn_legacy_notebook_shim(
            legacy_name="global_",
            canonical_name="fitting_mode",
        )
        self.fitting_mode = value

    @property
    def is_global(self) -> bool:
        """Whether the notebook is currently configured for global fitting."""
        return self.fitting_mode != FittingMode.STANDARD

    @property
    def y_columns(self) -> list[str]:
        """Canonical notebook ownership for y-columns."""
        return list(getattr(self, "_y_columns", []))

    @property
    def y_column(self) -> str | list[str]:
        """Legacy y-column boundary projected from the canonical list state."""
        return _compat_y_column(self.y_columns)

    @y_column.setter
    def y_column(self, value: str | list[str]) -> None:
        """Normalize y-column input into canonical notebook ownership."""
        normalized = _normalize_y_columns(value)
        self._y_columns = normalized
        self._context_n_datasets = len(normalized)
        self._fitting_mode = (
            FittingMode.GLOBAL if len(normalized) > 1 else FittingMode.STANDARD
        )
        args_plot = getattr(self, "args_plot", None)
        if args_plot is not None:
            args_plot.y = _compat_y_column(normalized)

    @property
    def n_datasets(self) -> int:
        """Canonical dataset count for notebook/config round-trips."""
        if self.fitting_mode == FittingMode.STANDARD:
            return 1
        return max(getattr(self, "_context_n_datasets", 1), len(self.y_columns), 2)

    @n_datasets.setter
    def n_datasets(self, value: int) -> None:
        """Preserve explicit dataset-count context for notebook round-trips."""
        self._context_n_datasets = max(int(value), 1)

    def _set_initial_components(
        self,
        value: InitialModelLike,
        *,
        warn_legacy: bool,
    ) -> None:
        """Store canonical typed initial components, optionally warning on legacy use."""
        if warn_legacy:
            _warn_legacy_notebook_shim(
                legacy_name="initial_model",
                canonical_name="initial_components",
            )
        self._initial_components = normalize_components(value)

    @property
    def initial_components(self) -> list[Component]:
        """Canonical typed ownership for notebook initial components."""
        return [
            component.model_copy(deep=True) for component in self._initial_components
        ]

    @initial_components.setter
    def initial_components(self, value: list[Component]) -> None:
        """Store canonical typed initial components on the notebook runtime."""
        self._set_initial_components(value, warn_legacy=False)

    @property
    def initial_model(self) -> list[LegacyModelSpec]:
        """Legacy notebook boundary projected from canonical typed components."""
        _warn_legacy_notebook_shim(
            legacy_name="initial_model",
            canonical_name="initial_components",
        )
        return components2legacy_specs(self._initial_components)

    @initial_model.setter
    def initial_model(self, value: list[LegacyModelSpec] | list[Component]) -> None:
        """Normalize notebook initial-model inputs into canonical typed components."""
        self._set_initial_components(value, warn_legacy=True)

    @property
    def preprocessing_config(self) -> PreprocessingConfig:
        """Canonical notebook ownership for preprocessing runtime state."""
        return getattr(self, "_preprocessing_config", PreprocessingConfig())

    @preprocessing_config.setter
    def preprocessing_config(self, value: PreprocessingConfig) -> None:
        """Store canonical preprocessing runtime state with notebook ownership."""
        self._preprocessing_config = value.model_copy(deep=True)

    def __getattr__(self, name: str) -> object:
        """Dispatch legacy side-effect attributes through method-first APIs."""
        try:
            canonical_name = _LEGACY_ACTION_SHIMS[name]
        except KeyError:
            msg = f"{type(self).__name__!s} object has no attribute {name!r}"
            raise AttributeError(msg) from None
        _warn_legacy_notebook_shim(
            legacy_name=name,
            canonical_name=f"{canonical_name}()",
        )
        getattr(self, canonical_name)()
        return None

    def _require_solver_results(self, action: str) -> SolverResults:
        """Return solver results or raise a clear session-state error."""
        if "_solver_results" not in self.__dict__:
            msg = f"Run solver_model() before {action}."
            raise RuntimeError(msg)
        return self.__dict__["_solver_results"]

    def _require_dataframe_state(
        self,
        attr_name: str,
        *,
        action: str,
        required_step: str,
    ) -> pd.DataFrame:
        """Return a populated dataframe or raise a clear session-state error."""
        dataframe = getattr(self, attr_name, None)
        if not isinstance(dataframe, pd.DataFrame) or dataframe.empty:
            msg = f"Run {required_step} before {action}."
            raise RuntimeError(msg)
        return dataframe

    @property
    def args_pre(self) -> DataPreProcessingAPI:
        """Compatibility preprocessing proxy backed by canonical notebook state."""
        _warn_legacy_notebook_shim(
            legacy_name="args_pre",
            canonical_name="preprocessing_config",
        )
        return NotebookPreprocessingProxy.from_canonical(
            self.preprocessing_config,
            column=notebook_boundary_columns(self.x_column, self.y_columns),
            sync_callback=self._apply_args_pre_boundary,
        )

    @args_pre.setter
    def args_pre(self, value: DataPreProcessingAPI) -> None:
        """Compatibility setter that updates canonical preprocessing ownership."""
        _warn_legacy_notebook_shim(
            legacy_name="args_pre",
            canonical_name="preprocessing_config",
        )
        self._apply_args_pre_boundary(value)

    def _apply_args_pre_boundary(self, value: DataPreProcessingAPI) -> None:
        """Update canonical notebook state from the compatibility DTO boundary."""
        column = value.column
        if column:
            self.x_column = str(column[0])
            self.y_column = [str(item) for item in column[1:]] or [str(column[0])]
        self.preprocessing_config = preprocessing_from_boundary(value)

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

    def _build_runtime_data_config(
        self,
        config: UnifiedFittingConfig,
    ) -> DataConfig:
        """Build a placeholder loader config for notebook-owned in-memory runs."""
        return DataConfig.from_unified(
            config,
            infile=config.infile
            if config.infile is not None
            else "notebook-runtime.csv",
        )

    def _load_runtime_dataframe(self, _: DataConfig) -> pd.DataFrame:
        """Serve the current notebook dataframe as the pipeline input source."""
        return self.df

    def _passthrough_preprocessor(
        self,
        df: pd.DataFrame,
        _: UnifiedFittingConfig,
    ) -> PreprocessResult:
        """Keep notebook runtime on its current dataframe instead of re-preprocessing."""
        current_statistic = getattr(self, "pre_statistic", SplitFrame.empty())
        return PreprocessResult(
            df=df,
            data_statistic=current_statistic.model_copy(deep=True),
        )

    def _build_runtime_pipeline_deps(self) -> PipelineDependencies:
        """Project notebook-owned runtime state onto the canonical pipeline seams."""
        base_deps = getattr(self, "_pipeline_deps", PipelineDependencies())
        return replace(
            base_deps,
            data_config_factory=self._build_runtime_data_config,
            data_loader=self._load_runtime_dataframe,
            preprocessor=self._passthrough_preprocessor,
        )

    def preprocess_df(self) -> None:
        """Run pre-processing and update notebook dataframe state."""
        pre_config = UnifiedFittingConfig(
            components=_PREPROCESS_PLACEHOLDER_COMPONENTS,
            column=ColumnConfig(
                x=self.x_column,
                y=self.y_columns[0],
            ),
            preprocessing=self.preprocessing_config,
        )
        pre_result = preprocess(
            df=self.df,
            config=pre_config,
        )
        self.df = pre_result.df
        self.pre_statistic = pre_result.data_statistic
        self.df_pre = self.df.copy()

    def export_active_df(self) -> None:
        """Export the current dataframe."""
        self.export_args_df.prefix = "act"
        self.export_df(df=self.df, args=self.export_args_df)

    def export_fit_dataframe(self) -> None:
        """Export the fit dataframe."""
        df_fit = self._require_dataframe_state(
            "df_fit",
            action="exporting fit notebook data",
            required_step="solver_model()",
        )
        self.export_args_df.prefix = "fit"
        self.export_df(df=df_fit, args=self.export_args_df)

    def export_original_df(self) -> None:
        """Export the original dataframe."""
        self.export_args_df.prefix = "org"
        self.export_df(df=self.df_org, args=self.export_args_df)

    def export_preprocessed_df(self) -> None:
        """Export the pre-processed dataframe when available."""
        df_pre = self._require_dataframe_state(
            "df_pre",
            action="exporting preprocessed notebook data",
            required_step="preprocess_df()",
        )
        self.export_args_df.prefix = "pre"
        self.export_df(df=df_pre, args=self.export_args_df)

    def export_metric_df(self) -> None:
        """Export the metrics dataframe when available."""
        df_metric = self._require_dataframe_state(
            "df_metric",
            action="exporting notebook metrics",
            required_step="solver_model()",
        )
        self.export_args_df.prefix = "metric"
        self.export_df(df=df_metric, args=self.export_args_df)

    def export_peaks_df(self) -> None:
        """Export the peaks dataframe when available."""
        df_peaks = self._require_dataframe_state(
            "df_peaks",
            action="exporting notebook peaks",
            required_step="solver_model()",
        )
        self.export_args_df.prefix = "peaks"
        self.export_df(df=df_peaks, args=self.export_args_df)

    def export_fit_plot_html(self) -> None:
        """Export the current fit as a standalone HTML Plotly artifact."""
        df_fit = self._require_dataframe_state(
            "df_fit",
            action="exporting notebook fit plots",
            required_step="solver_model()",
        )
        PlotSpectra(
            df=df_fit,
            config=PlotConfig(
                noplot=True,
                global_fitting=self.fitting_mode,
                data_statistic=self.pre_statistic,
            ),
        ).write_html(
            self.fname2path(
                fname=self.export_args_df.fname,
                prefix="fit",
                suffix="html",
                folder=self.export_args_df.folder,
            )
        )

    def plot_original(self) -> None:
        """Plot the original spectra."""
        self.plot_dataframe(args_plot=self.args_plot, df=self.df_org)

    def plot_current(self) -> None:
        """Plot the current spectra."""
        self.plot_dataframe(args_plot=self.args_plot, df=self.df)

    def plot_preprocessed(self) -> None:
        """Plot original and preprocessed spectra together."""
        df_pre = self._require_dataframe_state(
            "df_pre",
            action="plotting preprocessed notebook data",
            required_step="preprocess_df()",
        )
        self.plot_2dataframes(
            args_plot=self.args_plot,
            df_1=df_pre,
            df_2=self.df_org,
        )

    def plot_fit_df(self) -> None:
        """Plot the fit."""
        df_fit = self._require_dataframe_state(
            "df_fit",
            action="plotting fit notebook data",
            required_step="solver_model()",
        )
        if self.is_global:
            self.plot_global_fit(args_plot=self.args_plot, df=df_fit)
        else:
            self.plot_2dataframes(args_plot=self.args_plot, df_1=df_fit)

    def plot_current_metric(
        self,
        bar_criteria: str | list[str] | None = None,
        line_criteria: str | list[str] | None = None,
    ) -> None:
        """Plot the current metric.

        Args:
            bar_criteria (str | list[str] | None, optional): Criteria for the
                    bar plot. Defaults to None.
            line_criteria (str | list[str] | None, optional): Criteria for
                    the line plot. Defaults to None.

        """
        bar_criteria, line_criteria = _resolve_metric_criteria(
            bar_criteria=bar_criteria,
            line_criteria=line_criteria,
        )

        df_metric = self._require_dataframe_state(
            "df_metric",
            action="plotting notebook metrics",
            required_step="solver_model()",
        )
        self.plot_metric(
            args_plot=self.args_plot,
            df_metric=df_metric,
            bar_criteria=bar_criteria,
            line_criteria=line_criteria,
        )

    def generate_fit_report(self) -> None:
        """Generate the SpectraFit report for the final fit."""
        self._require_solver_results("generating a fit report")
        self.export_report(
            report=ExportReport(
                description=self.args_desc,
                fname=self.export_args_out,
                solver=self._solver_results,
                df_org=self.df_org,
                df_pre=self.df_pre,
                df_fit=self.df_fit,
            )(),
            args=self.export_args_out,
        )

    def solver_model(
        self,
        initial_model: list[Component] | list[LegacyModelSpec],
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
            initial_model (list[Component] | list[LegacyModelSpec]): Canonical
                 typed components or legacy component dictionaries defining the
                 initial fit model.
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
            bar_criteria (str | list[str] | None, optional): Criteria for the
                bar plot. It is recommended to use attributes from `goodness of fit`
                module. Defaults to None.
            line_criteria (str | list[str] | None, optional): Criteria for
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
        self._set_initial_components(initial_model, warn_legacy=False)

        resolved_ci, resolved_solver_settings = resolve_solver_options(
            conf_interval=conf_interval,
            solver_settings=solver_settings,
            config=config,
        )
        self.settings_solver_models = apply_solver_settings(
            current_settings=self.settings_solver_models,
            solver_settings=resolved_solver_settings,
        )

        solver_config = self.args_to_config().model_copy(
            update={
                "minimizer": self.settings_solver_models.minimizer,
                "optimizer": self.settings_solver_models.optimizer,
                "conf_interval": resolved_ci if resolved_ci is not None else False,
            }
        )
        pipeline_result = FittingPipeline(
            request=FittingRequest.from_config(solver_config),
            deps=self._build_runtime_pipeline_deps(),
        ).run()

        self.df_fit = pipeline_result.df
        self.pre_statistic = pipeline_result.data_statistic
        self._resolved_ci = resolved_ci
        self.fit_result = pipeline_result.fit_result
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
        self._require_solver_results("updating peak tables")
        self.df_peaks = self._solver_results.peaks_projection.append_to_dataframe(
            self.df_peaks
        )

    def update_metric(self) -> None:
        """Update the metric dataframe."""
        self._require_solver_results("updating metric tables")
        self.df_metric = self._solver_results.metric_projection.append_to_dataframe(
            self.df_metric
        )

    def display_fit_df(self, mode: str | None = "regular") -> None:
        """Display the fit dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".

        """
        df_fit = self._require_dataframe_state(
            "df_fit",
            action="displaying fit notebook data",
            required_step="solver_model()",
        )
        self.df_display(df=df_fit, mode=mode)

    def display_preprocessed_df(self, mode: str | None = "regular") -> None:
        """Display the preprocessed dataframe.

        Args:
            mode (str, optional): Display mode. Defaults to "regular".

        """
        df_pre = self._require_dataframe_state(
            "df_pre",
            action="displaying preprocessed notebook data",
            required_step="preprocess_df()",
        )
        self.df_display(df=df_pre, mode=mode)

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

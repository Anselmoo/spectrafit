"""Export utilities for Jupyter notebooks.

This module contains the ExportResults and ExportReport classes for
exporting results from Jupyter notebooks.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import tomli_w

from pydantic import BaseModel
from pydantic import ConfigDict

from spectrafit.adapters.preprocessing_boundary import NotebookBoundaryColumn
from spectrafit.adapters.preprocessing_boundary import preprocessing_from_boundary
from spectrafit.adapters.preprocessing_boundary import preprocessing_to_boundary
from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.core.result_bridge import resolve_fit_result_input_config
from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.peak_models import Component
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import SolverConfig
from spectrafit.reporting.service import CanonicalReportSchema
from spectrafit.reporting.service import ConfidenceSettingValue
from spectrafit.reporting.service import SolverReportProjection
from spectrafit.utilities.transformer import InitialModelLike
from spectrafit.utilities.transformer import components2legacy_specs
from spectrafit.utilities.transformer import normalize_components


__all__ = ["ExportReport", "ExportResults"]

type ReportDocument = dict[str, object]  # intentional: report serialization boundary
type DataCell = float | int | str | bool | None
type DataFrameListDict = dict[str, list[DataCell]]
type ReportConfidenceSettings = bool | dict[str, ConfidenceSettingValue]

_UNSET_DF_PRE = object()
_UNSET_COLUMN = object()


class NotebookExportDocument(BaseModel):
    """Thin notebook export adapter over the canonical reporting owner."""

    model_config = ConfigDict(extra="forbid")

    input: dict[str, object]
    solver: SolverReportProjection
    output: dict[str, DataFrameListDict]


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

    def export_report(self, report: ReportDocument, args: FnameAPI) -> None:
        """Export the results as toml file.

        Args:
            report (ReportDocument): Results to export.
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
            prefix (str | None, optional): Name of the prefix of the file. Defaults
                 to None.
            folder (str | None, optional): Folder, where it will be saved.
                 This folders will be created, if not exist. Defaults to None.

        Returns:
            Path: Path object of the file.

        """
        if prefix:
            fname = prefix + "_" + fname
        _fname = Path(fname).with_suffix(f".{suffix}")
        if folder:
            Path(folder).mkdir(parents=True, exist_ok=True)
            _fname = Path(folder) / _fname
        return _fname


class ExportReport:
    """Class for exporting results as toml.

    Uses composition over inheritance — wraps a ``SolverResults`` instance
    rather than subclassing it.  All fit-result accessors delegate to the
    underlying typed ``FitResult`` via ``SolverResults``.
    """

    def __init__(
        self,
        description: DescriptionAPI,
        fname: FnameAPI,
        solver: SolverResults,
        df_org: pd.DataFrame,
        df_fit: pd.DataFrame,
        *,
        initial_model: InitialModelLike | None = None,
        pre_processing: DataPreProcessingAPI | PreprocessingConfig | None = None,
        settings_solver_models: SolverConfig | None = None,
        df_pre: pd.DataFrame | object = _UNSET_DF_PRE,
        column: NotebookBoundaryColumn | object = _UNSET_COLUMN,
    ) -> None:
        """Initialize the ExportReport class.

        Args:
            description (DescriptionAPI): Description of the fit project.
            initial_model: Initial notebook model payload for the fit.
            pre_processing: Data pre-processing settings. Canonical notebook/runtime
                 flows pass ``PreprocessingConfig``; compatibility callers may still
                 pass ``DataPreProcessingAPI`` directly.
            settings_solver_models (SolverConfig): Solver settings.
            fname (FnameAPI): Filename of the fit project including the path, prefix,
                 and suffix.
            solver (SolverResults): Typed solver results from the fitting pipeline.
            df_org (pd.DataFrame): Dataframe of the original data for performing
                 the fit.
            df_fit (pd.DataFrame): Dataframe of the final fit data.
            df_pre (pd.DataFrame | None, optional): Dataframe of the pre-processed
                 data. Defaults to None (empty DataFrame).
            column: Compatibility column payload used when projecting canonical
                 preprocessing settings to the report boundary.

        """
        self._solver = solver
        self.description = description
        self._input_config = resolve_fit_result_input_config(self._solver.result)
        self._initial_components = self._resolve_initial_components(
            initial_model=initial_model
        )
        (
            self._preprocessing,
            self._preprocessing_column,
        ) = self._resolve_pre_processing_owner(
            pre_processing=pre_processing,
            column=column,
        )
        self.settings_solver_models = self._resolve_solver_models(
            settings_solver_models=settings_solver_models
        )
        self.fname = fname

        self.df_org = df_org.to_dict(orient="list")
        self.df_fit = df_fit.to_dict(orient="list")
        resolved_df_pre = (
            df_pre if isinstance(df_pre, pd.DataFrame) else pd.DataFrame()
        )  # intentional: compat shim
        self.df_pre = resolved_df_pre.to_dict(orient="list")

    @staticmethod
    def _snapshot_column(
        column: NotebookBoundaryColumn | object,
    ) -> NotebookBoundaryColumn | None:
        """Normalize optional notebook-boundary column input."""
        if isinstance(column, list):
            normalized_column = [
                item for item in column if isinstance(item, (int, str))
            ]
            if len(normalized_column) == len(column):
                return normalized_column
        return None

    def _resolve_initial_components(
        self,
        *,
        initial_model: InitialModelLike | None,
    ) -> list[Component]:
        """Prefer the typed FitResult snapshot for notebook input ownership."""
        if self._input_config is not None and self._input_config.components:
            return list(self._input_config.components)
        return normalize_components(initial_model) if initial_model is not None else []

    def _resolve_solver_models(
        self,
        *,
        settings_solver_models: SolverConfig | None,
    ) -> SolverConfig:
        """Prefer typed solver settings captured in the canonical FitResult."""
        if self._input_config is not None:
            return SolverConfig(
                minimizer=self._input_config.minimizer,
                optimizer=self._input_config.optimizer,
            )
        return settings_solver_models or SolverConfig()

    def _resolve_pre_processing_owner(
        self,
        pre_processing: DataPreProcessingAPI | PreprocessingConfig | None,
        *,
        column: NotebookBoundaryColumn | object,
    ) -> tuple[PreprocessingConfig, NotebookBoundaryColumn]:
        """Capture canonical preprocessing ownership plus report-boundary columns."""
        if self._input_config is not None:
            return (
                self._input_config.preprocessing.model_copy(deep=True)
                if self._input_config.preprocessing is not None
                else PreprocessingConfig(),
                [
                    self._input_config.x_column,
                    self._input_config.y_column,
                ],
            )

        if pre_processing is None:
            return (
                PreprocessingConfig(),
                self._snapshot_column(column) or list(DataPreProcessingAPI().column),
            )
        if isinstance(pre_processing, DataPreProcessingAPI):
            return (
                preprocessing_from_boundary(pre_processing),
                list(pre_processing.column),
            )
        resolved_column = self._snapshot_column(column)
        if resolved_column is None:
            msg = "column is required when pre_processing is a PreprocessingConfig"
            raise ValueError(msg)
        return pre_processing.model_copy(deep=True), resolved_column

    @property
    def pre_processing(self) -> DataPreProcessingAPI:
        """Project canonical preprocessing ownership to the report DTO boundary."""
        return preprocessing_to_boundary(
            self._preprocessing,
            column=self._preprocessing_column,
        )

    @property
    def canonical_report(self) -> CanonicalReportSchema:
        """Canonical reporting owner shared by notebook export adapters."""
        return self._solver.canonical_report

    def _serialize_conf_interval(self) -> ReportConfidenceSettings:
        """Serialize confidence settings to the plain report boundary."""
        return self.canonical_report.confidence_settings

    def _fit_global_mode(self) -> FittingMode:
        """Return the canonical fitting mode for the report bridge."""
        return self._solver.fitting_mode

    @property
    def make_input_contribution(self) -> dict[str, object]:
        """Make input contribution of the report.

        Returns:
            dict[str, object]: Input contribution projected from canonical ownership.

        """
        canonical_report = self.canonical_report
        return {
            "description": self.description,
            "initial_model": self._initial_components,
            "method": {
                "global_fitting": self._fit_global_mode().value,
                "confidence_interval": self._serialize_conf_interval(),
                "configurations": canonical_report.configurations,
                "settings_solver_models": self.settings_solver_models,
            },
            "pre_processing": self.pre_processing,
        }

    @property
    def make_solver_contribution(self) -> SolverReportProjection:
        """Make solver contribution of the report.

        Returns:
            SolverReportProjection: Solver contribution as a typed report section.

        """
        return self.canonical_report.solver

    @property
    def make_output_contribution(self) -> dict[str, DataFrameListDict]:
        """Make output contribution of the report.

        Returns:
            dict[str, DataFrameListDict]: Notebook dataframe payloads.

        """
        return {
            "df_org": self.df_org,
            "df_fit": self.df_fit,
            "df_pre": self.df_pre,
        }

    def __call__(self) -> dict[str, object]:  # intentional: TOML serialization boundary
        """Get the complete report as dictionary.

        Returns:
            ReportDocument: Report as dictionary using ``.model_dump()``.
                ``None`` is excluded.

        """
        report = NotebookExportDocument(
            input=self.make_input_contribution,
            solver=self.make_solver_contribution,
            output=self.make_output_contribution,
        )
        serialized = report.model_dump(mode="json", exclude_none=True)
        serialized["input"]["initial_model"] = components2legacy_specs(
            self._initial_components
        )
        return serialized

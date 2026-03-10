"""Export utilities for Jupyter notebooks.

This module contains the ExportResults and ExportReport classes for
exporting results from Jupyter notebooks.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import tomli_w

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.report_model import ComputationalInfo
from spectrafit.api.report_model import FitConfigurationsAPI
from spectrafit.api.report_model import FitMethodAPI
from spectrafit.api.report_model import InputAPI
from spectrafit.api.report_model import OutputAPI
from spectrafit.api.report_model import ParameterSpec
from spectrafit.api.report_model import ReportAPI
from spectrafit.api.report_model import SolverAPI
from spectrafit.api.report_model import VariableResult
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.core import exclude_none_dictionary
from spectrafit.core import transform_nested_types
from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.fitting_context import FittingMode
from spectrafit.utilities.transformer import LegacyModelSpec


__all__ = ["ExportReport", "ExportResults"]

type ReportDocument = dict[str, object]  # intentional: report serialization boundary


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

    def export_report(self, report: ReportDocument | ReportAPI, args: FnameAPI) -> None:
        """Export the results as toml file.

        Args:
            report (ReportDocument | ReportAPI): Results to export.
            args (FnameAPI): Arguments for the file export including the path, prefix,
                 and suffix.

        """
        report_dict = (
            report.model_dump(exclude_none=True)
            if isinstance(report, ReportAPI)
            else report
        )
        with self.fname2path(
            fname=args.fname,
            prefix=args.prefix,
            suffix=args.suffix,
            folder=args.folder,
        ).open("wb+") as f:
            tomli_w.dump(report_dict, f)

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
            fname = f"{prefix}_{fname}"  # intentional: prefix construction
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
        initial_model: list[LegacyModelSpec],
        pre_processing: DataPreProcessingAPI,
        settings_solver_models: SolverModelsAPI,
        fname: FnameAPI,
        solver: SolverResults,
        df_org: pd.DataFrame,
        df_fit: pd.DataFrame,
        df_pre: pd.DataFrame | None = None,
    ) -> None:
        """Initialize the ExportReport class.

        Args:
            description (DescriptionAPI): Description of the fit project.
            initial_model (list[LegacyModelSpec]): Initial model for the fit.
            pre_processing (DataPreProcessingAPI): Data pre-processing settings.
            settings_solver_models (SolverModelsAPI): Solver models settings.
            fname (FnameAPI): Filename of the fit project including the path, prefix,
                 and suffix.
            solver (SolverResults): Typed solver results from the fitting pipeline.
            df_org (pd.DataFrame): Dataframe of the original data for performing
                 the fit.
            df_fit (pd.DataFrame): Dataframe of the final fit data.
            df_pre (Optional[pd.DataFrame], optional): Dataframe of the pre-processed
                 data. Defaults to None (empty DataFrame).

        """
        self._solver = solver
        self.description = description
        self.initial_model = initial_model
        self.pre_processing = pre_processing
        self.settings_solver_models = settings_solver_models
        self.fname = fname

        self.df_org = df_org.to_dict(orient="list")
        self.df_fit = df_fit.to_dict(orient="list")
        df_pre = (
            df_pre if df_pre is not None else pd.DataFrame()
        )  # intentional: compat shim
        self.df_pre = df_pre.to_dict(orient="list")

    @staticmethod
    def _coerce_report_document(value: object) -> ReportDocument:
        """Convert a generic nested object into a report-compatible dictionary."""
        if not isinstance(value, dict):
            return {}
        report_document: ReportDocument = {}
        for key, item in value.items():
            report_document[str(key)] = item
        return report_document

    @staticmethod
    def _serialize_initial_model(
        initial_model: list[LegacyModelSpec],
    ) -> list[dict[str, dict[str, ParameterSpec]]]:
        """Convert legacy initial-model specs into report-model parameter specs."""
        serialized: list[dict[str, dict[str, ParameterSpec]]] = []
        for peak in initial_model:
            model_block: dict[str, dict[str, ParameterSpec]] = {}
            for model_name, model_parameters in peak.items():
                model_block[model_name] = {
                    parameter_name: ParameterSpec.model_validate(parameter_value)
                    for parameter_name, parameter_value in model_parameters.items()
                }
            serialized.append(model_block)
        return serialized

    def _serialize_conf_interval(self) -> bool | ConfIntervalAPI:
        """Serialize confidence settings to report API contract."""
        settings = self._solver.settings_conf_interval
        if isinstance(settings, bool):
            return settings

        filtered_settings = {
            key: value
            for key, value in settings.items()
            if key in {"p_names", "trace", "maxiter", "verbose", "prob_func"}
        }
        prob_func = filtered_settings.get("prob_func")
        if prob_func is not None and not callable(prob_func):
            filtered_settings.pop("prob_func", None)
        return ConfIntervalAPI.model_validate(filtered_settings)

    def _serialize_variables(self) -> dict[str, VariableResult]:
        """Map ``VariableFitResult`` entries into ``VariableResult`` report entries."""
        return {
            key: VariableResult.model_validate(value.model_dump(exclude_none=True))
            for key, value in self._solver.get_variables.items()
        }

    def _fit_global_mode(self) -> FittingMode:
        """Map legacy integer global-flag values to ``FittingMode``."""
        return (
            FittingMode.GLOBAL
            if self._solver.settings_global_fitting
            else FittingMode.STANDARD
        )

    @property
    def make_input_contribution(self) -> InputAPI:
        """Make input contribution of the report.

        Returns:
            InputAPI: Input contribution of the report as class.

        """
        return InputAPI(
            description=self.description,
            initial_model=self._serialize_initial_model(self.initial_model),
            pre_processing=self.pre_processing,
            method=FitMethodAPI(
                global_fitting=self._fit_global_mode(),
                confidence_interval=self._serialize_conf_interval(),
                configurations=FitConfigurationsAPI.model_validate(
                    self._solver.settings_configurations
                ),
                settings_solver_models=self.settings_solver_models,
            ),
        )

    @property
    def make_solver_contribution(self) -> SolverAPI:
        """Make solver contribution of the report.

        Returns:
            SolverAPI: Solver contribution of the report as class.

        """
        return SolverAPI(
            goodness_of_fit=self._solver.get_gof,
            regression_metrics=self._solver.get_regression_metrics,
            descriptive_statistic=self._solver.get_descriptive_statistic,
            linear_correlation=self._solver.get_linear_correlation,
            component_correlation=self._solver.get_component_correlation,
            confidence_interval=self._solver.get_confidence_interval,
            covariance_matrix=self._solver.get_covariance_matrix,
            variables=self._serialize_variables(),
            errorbars=self._solver.get_errorbars,
            computational=ComputationalInfo.model_validate(
                self._solver.get_computational
            ),
        )

    @property
    def make_output_contribution(self) -> OutputAPI:
        """Make output contribution of the report.

        Returns:
            OutputAPI: Output contribution of the report as class.

        """
        return OutputAPI(df_org=self.df_org, df_fit=self.df_fit, df_pre=self.df_pre)

    def __call__(self) -> dict[str, object]:  # intentional: TOML serialization boundary
        """Get the complete report as dictionary.

        !!! info "About the report and ``exclude_none_dictionary``"

            The report is generated by using the ``ReportAPI`` class, which is a
            Pydantic definition of the report. The Pydantic definition is converted
            to a dictionary by using the ``.model_dump()`` option of Pydantic.
            The ``recursive_exclude_none`` function is used to remove all ``None``
            values from the dictionary, which are hidden in the nested dictionaries.

        Returns:
            ReportDocument: Report as dictionary using ``.model_dump()``.
                ``None`` is excluded.

        """
        report = ReportAPI(
            input=self.make_input_contribution,
            solver=self.make_solver_contribution,
            output=self.make_output_contribution,
        ).model_dump(exclude_none=True)
        report = exclude_none_dictionary(report)
        transformed_report = transform_nested_types(report)
        return self._coerce_report_document(transformed_report)

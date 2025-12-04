"""Export utilities for Jupyter notebooks.

This module contains the ExportResults and ExportReport classes for
exporting results from Jupyter notebooks.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import tomli_w

from spectrafit.api.cmd_model import DescriptionAPI
from spectrafit.api.notebook_model import FnameAPI
from spectrafit.api.report_model import FitMethodAPI
from spectrafit.api.report_model import InputAPI
from spectrafit.api.report_model import OutputAPI
from spectrafit.api.report_model import ReportAPI
from spectrafit.api.report_model import SolverAPI
from spectrafit.api.tools_model import DataPreProcessingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.plugins.notebook.solver import SolverResults
from spectrafit.tools import exclude_none_dictionary
from spectrafit.tools import transform_nested_types


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
            report (dict[Any, Any]): Results as dictionary to export.
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
            initial_model (List[dict[str, Dict[str, Dict[str, Any]]]]): Initial model
                 for the fit.
            pre_processing (DataPreProcessingAPI): Data pre-processing settings.
            settings_solver_models (SolverModelsAPI): Solver models settings.
            fname (FnameAPI): Filename of the fit project including the path, prefix,
                 and suffix.
            args_out (dict[str, Any]): Dictionary of SpectraFit settings and results.
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
            dict[str, Any]: Report as dictionary by using the `.model_dump()` option of
                 pydantic. `None` is excluded.

        """
        report = ReportAPI(
            input=self.make_input_contribution,
            solver=self.make_solver_contribution,
            output=self.make_output_contribution,
        ).model_dump(exclude_none=True)
        report = exclude_none_dictionary(report)
        return transform_nested_types(report)

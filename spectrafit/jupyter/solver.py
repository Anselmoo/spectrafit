"""Solver results utilities for Jupyter notebooks.

This module contains the SolverResults class for storing and accessing
solver results as a typed Pydantic model wrapping ``FitResult``.

The class replaces the legacy ``SolverResults(args_out: FittingArgs)`` pattern
where raw dict key access was used for all result fields.  All properties now
delegate to typed ``FitResult`` fields.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field

from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.types import DataSplitDict


class SolverResults(BaseModel):
    """Jupyter-facing result view — wraps FitResult with typed property access.

    Usage::

        solver = SolverResults(result=fit_result)
        solver.get_gof             # dict[str, float]
        solver.get_current_metric  # pd.DataFrame

    """

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    result: FitResult

    # ------------------------------------------------------------------
    # Settings / configuration
    # ------------------------------------------------------------------

    @computed_field
    @property
    def settings_global_fitting(self) -> int:
        """Global fitting flag as legacy integer (0 = standard, 1 = global).

        Returns:
            int: ``0`` for :attr:`~FittingMode.STANDARD`, ``1`` for
            :attr:`~FittingMode.GLOBAL`.  The integer form is preserved for
            backward compatibility with the API layer.

        """
        return 0 if self.result.global_fitting == FittingMode.STANDARD else 1

    @computed_field
    @property
    def settings_configurations(self) -> dict[str, object]:  # intentional: report layer
        """Fit method and solver configuration snapshot.

        Returns:
            Serialized configuration dict from ``FitConfigurations``.

        """
        return self.result.fit_insights.configurations.model_dump()

    @computed_field
    @property
    def settings_conf_interval(
        self,
    ) -> bool | dict[str, object]:  # intentional: CI settings
        """Confidence interval settings.

        ``None`` values inside a dict are replaced with empty dicts to match the
        legacy behaviour expected by ``InputAPI`` / ``FitMethodAPI``.

        Returns:
            CI settings dict (or ``False`` when disabled).

        """
        settings = self.result.confidence.settings
        if isinstance(settings, dict):
            return {k: (v if v is not None else {}) for k, v in settings.items()}
        return settings

    # ------------------------------------------------------------------
    # Fit quality
    # ------------------------------------------------------------------

    @computed_field
    @property
    def get_gof(self) -> dict[str, float]:
        """Goodness-of-fit statistics.

        Returns:
            dict[str, float]: Goodness of fit values.

        """
        return self.result.fit_insights.statistics

    @computed_field
    @property
    def get_variables(self) -> dict[str, VariableFitResult]:
        """Per-parameter variable results.

        Returns:
            dict[str, VariableFitResult]: Variables of the fit.

        """
        return self.result.fit_insights.variables

    @computed_field
    @property
    def get_errorbars(self) -> dict[str, str]:
        """Error-bar status per parameter.

        Returns:
            dict[str, str]: Error-bar comments as dictionary.

        """
        return self.result.fit_insights.errorbars

    @computed_field
    @property
    def get_component_correlation(self) -> dict[str, dict[str, float]]:
        """Component-level linear correlations.

        Returns:
            dict[str, dict[str, float]]: Linear correlation of the components.

        """
        return self.result.fit_insights.correlations

    @computed_field
    @property
    def get_covariance_matrix(self) -> dict[str, dict[str, float]]:
        """Covariance matrix of fit parameters.

        Returns:
            dict[str, dict[str, float]]: Covariance matrix.

        """
        return self.result.fit_insights.covariance_matrix

    @computed_field
    @property
    def get_computational(
        self,
    ) -> dict[str, object]:  # intentional: serialized for report
        """Computational timing and metadata.

        Returns:
            Serialized computational information dict.

        """
        return self.result.fit_insights.computational.model_dump()

    # ------------------------------------------------------------------
    # Data summary
    # ------------------------------------------------------------------

    @computed_field
    @property
    def get_regression_metrics(self) -> DataSplitDict:
        """Regression metrics (index + data lists).

        Returns:
            DataSplitDict: Regression metrics in pandas split-dict format.

        """
        return self.result.data_summary.regression_metrics

    @computed_field
    @property
    def get_descriptive_statistic(self) -> DataSplitDict:
        """Descriptive statistics.

        Returns:
            DataSplitDict: Descriptive statistic of the spectra, fit, and
                components.

        """
        return self.result.data_summary.descriptive_statistic

    @computed_field
    @property
    def get_linear_correlation(self) -> DataSplitDict:
        """Linear correlation coefficients.

        Returns:
            DataSplitDict: Linear correlation of spectra, fit, and components.

        """
        return self.result.data_summary.linear_correlation

    # ------------------------------------------------------------------
    # Confidence interval
    # ------------------------------------------------------------------

    @computed_field
    @property
    def get_confidence_interval(self) -> dict[str, list[tuple[float, float]]]:
        """Confidence interval results; empty dict if CI was not computed.

        Returns:
            dict[str, list[tuple[float, float]]]: Confidence interval results.

        """
        if self.result.confidence.settings is False:
            return {}
        return self.result.confidence.results

    # ------------------------------------------------------------------
    # Derived / display
    # ------------------------------------------------------------------

    @computed_field
    @property
    def get_current_metric(self) -> pd.DataFrame:
        """Merge goodness-of-fit and averaged regression metrics into one row.

        !!! note "About the regression metrics"

            For using the regression metrics, the ``regression_metrics`` must be
            averaged to merge the results of the different configurations together
            with the ``goodness_of_fit`` and ``variables`` results.

        Returns:
            pd.DataFrame: One-row dataframe combining GoF and regression metrics.

        """
        gof: dict[str, list[float]] = {
            key: [value] for key, value in self.get_gof.items()
        }
        reg_metrics: DataSplitDict = self.get_regression_metrics
        reg: dict[str, list[float]] = {}
        if "index" in reg_metrics and "data" in reg_metrics:
            reg = {
                key: [np.average(val)]
                for key, val in zip(
                    reg_metrics["index"],
                    reg_metrics["data"],
                    strict=False,
                )
            }
        return pd.DataFrame(gof | reg)

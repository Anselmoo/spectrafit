"""Solver results utilities for Jupyter notebooks.

This module contains the SolverResults class for storing and accessing
solver results as a typed Pydantic model wrapping ``FitResult``.

The class replaces the legacy ``SolverResults(args_out: FittingArgs)`` pattern
where raw dict key access was used for all result fields.  All properties now
delegate to typed ``FitResult`` fields.
"""

from __future__ import annotations

import warnings

import pandas as pd

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field

from spectrafit.jupyter.result_projection import NotebookMetricProjection
from spectrafit.jupyter.result_projection import NotebookPeaksProjection
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ComputationalMeta
from spectrafit.models.results.fit_result import FitConfigurations
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.split_frame import SplitFrame
from spectrafit.reporting.service import CanonicalReportSchema
from spectrafit.reporting.service import SolverReportProjection
from spectrafit.reporting.service import project_canonical_report


def _warn_legacy_solver_shim(*, legacy_name: str, canonical_name: str) -> None:
    """Emit a deprecation warning for legacy notebook solver getters."""
    warnings.warn(
        (
            f"SolverResults.{legacy_name} is a legacy compatibility shim in v2.x; "
            f"use SolverResults.{canonical_name} instead. "
            "The shim will be removed in v3.0.0."
        ),
        FutureWarning,
        stacklevel=3,
    )


class SolverResults(BaseModel):
    """Jupyter-facing result view — owns canonical projections over ``FitResult``.

    Usage::

        solver = SolverResults(result=fit_result)
        solver.goodness_of_fit     # dict[str, float]
        solver.current_metric      # pd.DataFrame

    """

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    result: FitResult

    # ------------------------------------------------------------------
    # Settings / configuration
    # ------------------------------------------------------------------

    @property
    def fitting_mode(self) -> FittingMode:
        """Canonical fitting mode for notebook/runtime consumers."""
        return self.result.global_fitting

    @property
    def is_global(self) -> bool:
        """Whether the solver result represents a global fit."""
        return self.fitting_mode != FittingMode.STANDARD

    @property
    def fit_configurations_model(self) -> FitConfigurations:
        """Typed fit configuration snapshot for report/model bridges."""
        return self.canonical_report.configurations

    @property
    def canonical_report(self) -> CanonicalReportSchema:
        """Canonical report ownership for notebook/report/export consumers."""
        return project_canonical_report(self.result)

    @property
    def report_projection(self) -> SolverReportProjection:
        """Canonical solver projection shared by notebook/export/report adapters."""
        return self.canonical_report.solver

    @property
    def confidence_interval_settings(self) -> bool | dict[str, object]:
        """Plain confidence settings payload for report/export boundaries."""
        return self.canonical_report.confidence_settings

    @property
    def goodness_of_fit(self) -> dict[str, float]:
        """Canonical goodness-of-fit projection."""
        return self.report_projection.goodness_of_fit

    @property
    def variables(self) -> dict[str, VariableFitResult]:
        """Canonical variable projection."""
        return self.report_projection.variables

    @property
    def errorbars(self) -> dict[str, str]:
        """Canonical error-bar projection."""
        return self.report_projection.errorbars

    @property
    def component_correlation(self) -> dict[str, dict[str, float]]:
        """Canonical component-correlation projection."""
        return self.report_projection.component_correlation

    @property
    def covariance_matrix(self) -> dict[str, dict[str, float]]:
        """Canonical covariance-matrix projection."""
        return self.report_projection.covariance_matrix

    @property
    def computational(self) -> ComputationalMeta:
        """Canonical computational metadata projection."""
        return self.report_projection.computational

    @property
    def regression_metrics(self) -> SplitFrame:
        """Canonical regression-metrics projection."""
        return self.report_projection.regression_metrics

    @property
    def descriptive_statistic(self) -> SplitFrame:
        """Canonical descriptive-statistic projection."""
        return self.report_projection.descriptive_statistic

    @property
    def linear_correlation(self) -> SplitFrame:
        """Canonical linear-correlation projection."""
        return self.report_projection.linear_correlation

    @property
    def confidence_interval(self) -> dict[str, list[tuple[float, float]]]:
        """Canonical confidence-interval projection."""
        return self.report_projection.confidence_interval

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
        _warn_legacy_solver_shim(
            legacy_name="get_gof",
            canonical_name="goodness_of_fit",
        )
        return self.goodness_of_fit

    @computed_field
    @property
    def get_variables(self) -> dict[str, VariableFitResult]:
        """Per-parameter variable results.

        Returns:
            dict[str, VariableFitResult]: Variables of the fit.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_variables",
            canonical_name="variables",
        )
        return self.variables

    @computed_field
    @property
    def get_errorbars(self) -> dict[str, str]:
        """Error-bar status per parameter.

        Returns:
            dict[str, str]: Error-bar comments as dictionary.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_errorbars",
            canonical_name="errorbars",
        )
        return self.errorbars

    @computed_field
    @property
    def get_component_correlation(self) -> dict[str, dict[str, float]]:
        """Component-level linear correlations.

        Returns:
            dict[str, dict[str, float]]: Linear correlation of the components.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_component_correlation",
            canonical_name="component_correlation",
        )
        return self.component_correlation

    @computed_field
    @property
    def get_covariance_matrix(self) -> dict[str, dict[str, float]]:
        """Covariance matrix of fit parameters.

        Returns:
            dict[str, dict[str, float]]: Covariance matrix.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_covariance_matrix",
            canonical_name="covariance_matrix",
        )
        return self.covariance_matrix

    @computed_field
    @property
    def get_computational(
        self,
    ) -> dict[str, object]:  # intentional: serialized for report
        """Computational timing and metadata.

        Returns:
            Serialized computational information dict.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_computational",
            canonical_name="computational",
        )
        return self.computational.model_dump()

    @property
    def computational_metadata(self) -> ComputationalMeta:
        """Typed computational metadata for report/model bridges."""
        return self.computational

    # ------------------------------------------------------------------
    # Data summary
    # ------------------------------------------------------------------

    @computed_field
    @property
    def get_regression_metrics(self) -> SplitFrame:
        """Regression metrics (index + data lists).

        Returns:
            SplitFrame: Regression metrics as a validated split-frame model.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_regression_metrics",
            canonical_name="regression_metrics",
        )
        return self.regression_metrics

    @computed_field
    @property
    def get_descriptive_statistic(self) -> SplitFrame:
        """Descriptive statistics.

        Returns:
            SplitFrame: Descriptive statistic of the spectra, fit, and
                components.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_descriptive_statistic",
            canonical_name="descriptive_statistic",
        )
        return self.descriptive_statistic

    @computed_field
    @property
    def get_linear_correlation(self) -> SplitFrame:
        """Linear correlation coefficients.

        Returns:
            SplitFrame: Linear correlation of spectra, fit, and components.

        """
        _warn_legacy_solver_shim(
            legacy_name="get_linear_correlation",
            canonical_name="linear_correlation",
        )
        return self.linear_correlation

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
        _warn_legacy_solver_shim(
            legacy_name="get_confidence_interval",
            canonical_name="confidence_interval",
        )
        return self.confidence_interval

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
        _warn_legacy_solver_shim(
            legacy_name="get_current_metric",
            canonical_name="current_metric",
        )
        return self.current_metric

    @property
    def current_metric(self) -> pd.DataFrame:
        """Canonical one-row metrics dataframe for notebook presentation."""
        return self.metric_projection.to_dataframe()

    @property
    def metric_projection(self) -> NotebookMetricProjection:
        """Typed notebook metric projection for presentation adapters."""
        return NotebookMetricProjection.from_solver_report(self.report_projection)

    @property
    def peaks_projection(self) -> NotebookPeaksProjection:
        """Typed notebook peaks projection for presentation adapters."""
        return NotebookPeaksProjection.from_solver_report(self.report_projection)

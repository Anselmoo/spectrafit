"""Solver results utilities for Jupyter notebooks.

This module contains the SolverResults class for storing and accessing
solver results.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


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
                strict=False,
            )
        }
        metric = {**gof, **reg}
        return pd.DataFrame(metric)

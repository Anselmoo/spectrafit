"""Post-processing utilities for SpectraFit.

This module contains the PostProcessing class and its typed result container
:class:`PostProcessingResult`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from lmfit.confidence import ConfidenceInterval
from lmfit.minimizer import MinimizerException
from lmfit.minimizer import MinimizerResult
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.column_names import ColumnNames
from spectrafit.models.functions.builtin import calculated_model
from spectrafit.models.types import DataSplitDict
from spectrafit.report import RegressionMetrics
from spectrafit.report import fit_report_as_dict
from spectrafit.report.formatter import FitReportBuffer


if TYPE_CHECKING:
    from lmfit import Minimizer


# Module-level singleton — avoids creating a new ColumnNames on every call.
_COLS = ColumnNames()


class PostProcessingResult(BaseModel):
    """Typed container for all post-processing outputs.

    Replaces the legacy ``dict[str, object]`` return from ``PostProcessing``.
    Every consumer of post-processing data should read from this model
    instead of indexing into a raw dictionary.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame = Field(
        description="Enriched DataFrame with residuals, fits, contributions"
    )
    fit_insights: FitReportBuffer = Field(
        default_factory=dict,
        description="Fit report: statistics, variables, errorbars, correlations",
    )
    confidence_interval: dict[str, object] | tuple[object, ...] = Field(
        default_factory=dict,
        description="Confidence interval results (dict or tuple with trace)",
    )
    linear_correlation: DataSplitDict = Field(
        default_factory=dict,
        description="Linear correlation matrix in split-orient dict format",
    )
    fit_result_data: DataSplitDict = Field(
        default_factory=dict,
        description="Full fit result DataFrame in split-orient dict format",
    )
    regression_metrics: DataSplitDict = Field(
        default_factory=dict,
        description="Regression metrics in split-orient dict format",
    )
    descriptive_statistic: DataSplitDict = Field(
        default_factory=dict,
        description="Descriptive statistics in split-orient dict format",
    )


class PostProcessing:
    """Post-processing of the dataframe.

    Produces a :class:`PostProcessingResult` containing the enriched DataFrame
    and all derived statistics.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        minimizer: Minimizer,
        result: MinimizerResult,
        *,
        is_global: bool = False,
        conf_interval: dict[str, object] | bool = False,
        bundle: CompositeModelBundle | None = None,
    ) -> None:
        """Initialize PostProcessing class.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            minimizer: The minimizer class.
            result: The result of the minimization of the best fit.
            is_global: Whether global fitting mode is enabled.
            conf_interval: Confidence interval settings (dict to enable, False to skip).
            bundle: Optional CompositeModelBundle for local-fit decomposition.

        """
        self._is_global = is_global
        self._conf_interval = conf_interval
        self._bundle = bundle
        self.df = self._rename_columns(df=df)
        self.minimizer = minimizer
        self.result = result
        self._data_size = self._check_global_fitting()

    def __call__(self) -> PostProcessingResult:
        """Run post-processing and return typed result."""
        fit_insights = self._make_insight_report()
        confidence_interval = self._compute_confidence_interval()
        self._make_residual_fit()
        self._make_fit_contributions()

        return PostProcessingResult(
            df=self.df,
            fit_insights=fit_insights,
            confidence_interval=confidence_interval,
            linear_correlation=self.df.corr().to_dict(orient="split"),  # type: ignore[assignment]
            fit_result_data=self.df.to_dict(orient="split"),  # type: ignore[assignment]
            regression_metrics=RegressionMetrics(self.df)(),  # type: ignore[assignment]
            descriptive_statistic=self.df.describe(
                percentiles=np.arange(0.1, 1, 0.1).tolist(),
            ).to_dict(orient="split"),  # type: ignore[assignment]
        )

    def _check_global_fitting(self) -> int | None:
        """Check if the global fitting is performed.

        Returns:
            int | None: The number of spectra of the global fitting.

        """
        if self._is_global:
            return max(
                int(self.result.params[i].name.split("_")[-1])
                for i in self.result.params
            )
        return None

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename the columns of the dataframe.

        Args:
            df: DataFrame containing the original input data.

        Returns:
            pd.DataFrame: DataFrame with renamed columns.

        """
        if self._is_global:
            return df.rename(
                columns={
                    col: (_COLS.energy if i == 0 else f"{_COLS.intensity}_{i}")
                    for i, col in enumerate(df.columns)
                },
            )
        return df.rename(
            columns={
                df.columns[0]: _COLS.energy,
                df.columns[1]: _COLS.intensity,
            },
        )

    def _make_insight_report(self) -> FitReportBuffer:
        """Build the fit insight report.

        Returns:
            FitReportBuffer: Dictionary with statistics, variables, errorbars, etc.

        """
        return fit_report_as_dict(
            inpars=self.result,
            settings=self.minimizer,
            modelpars=self.result.params,
        )

    def _compute_confidence_interval(
        self,
    ) -> dict[str, object] | tuple[object, ...]:
        """Compute confidence intervals if configured.

        Returns:
            Confidence interval results, or empty dict on failure/skip.

        """
        if not self._conf_interval or not isinstance(self._conf_interval, dict):
            return {}
        try:
            ci_args = dict(self._conf_interval)
            min_rel_change = ci_args.pop("min_rel_change", None)
            ci = ConfidenceInterval(
                self.minimizer,
                self.result,
                **ci_args,
            )
            if min_rel_change is not None:
                ci.min_rel_change = min_rel_change

            trace = ci_args.get("trace")
            if trace is True:
                return (ci.calc_all_ci(), ci.trace_dict)
            return ci.calc_all_ci()

        except (MinimizerException, ValueError, KeyError):
            return {}

    def _make_residual_fit(self) -> None:
        r"""Make the residuals of the model and the fit.

        The residual is calculated by the difference of the best fit model and
        the reference data. In case of a global fitting, the residuals are
        calculated for each spectra separately plus an averaged global residual.
        """
        df_copy: pd.DataFrame = self.df.copy()
        if self._is_global:
            residual = self.result.residual.reshape((-1, self._data_size)).T
            for i, _residual in enumerate(residual, start=1):
                df_copy[f"{_COLS.residual}_{i}"] = _residual
                df_copy[f"{_COLS.fit}_{i}"] = (
                    self.df[f"{_COLS.intensity}_{i}"].to_numpy() + _residual
                )
            df_copy[f"{_COLS.residual}_avg"] = np.mean(residual, axis=0)
        else:
            residual = self.result.residual
            df_copy[_COLS.residual] = residual
            df_copy[_COLS.fit] = self.df[_COLS.intensity].to_numpy() + residual
        self.df = df_copy

    def _make_fit_contributions(self) -> None:
        """Make the fit contributions of the best fit model."""
        self.df = calculated_model(
            params=self.result.params,
            x=self.df.iloc[:, 0].to_numpy(),
            df=self.df,
            global_fit=self._is_global,
            bundle=self._bundle,
        )

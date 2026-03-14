"""Post-processing utilities for SpectraFit.

This module contains the PostProcessing class and its typed result container
:class:`PostProcessingResult`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from lmfit.confidence import ConfidenceInterval
from lmfit.minimizer import MinimizerException
from lmfit.minimizer import MinimizerResult
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.core.regression_metrics import RegressionMetrics
from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.column_names import ColumnNames
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import normalize_confidence_results_payload
from spectrafit.models.solver import calculated_model
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.split_frame import SplitFrame


if TYPE_CHECKING:
    from lmfit import Minimizer


# Module-level singleton — avoids creating a new ColumnNames on every call.
_COLS = ColumnNames()


@dataclass(frozen=True, slots=True)
class ResidualFitPayload:
    """Declarative residual/fit column payload for bulk DataFrame construction."""

    columns: dict[str, np.ndarray]

    def to_frame(self, index: pd.Index) -> pd.DataFrame:
        """Materialize the payload as a DataFrame aligned to *index*."""
        return pd.DataFrame(self.columns, index=index)


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
    fit_insights: FitInsights = Field(
        default_factory=FitInsights,
        description="Structured fit insights for statistics, variables, and correlations",
    )
    confidence_interval: ConfidenceResults = Field(
        default_factory=ConfidenceResults,
        description="Typed confidence interval settings and results",
    )
    linear_correlation: SplitFrame = Field(
        default_factory=SplitFrame.empty,
        description="Linear correlation matrix as a validated split-frame model",
    )
    fit_result_data: SplitFrame = Field(
        default_factory=SplitFrame.empty,
        description="Full fit result DataFrame as a validated split-frame model",
    )
    regression_metrics: SplitFrame = Field(
        default_factory=SplitFrame.empty,
        description="Regression metrics as a validated split-frame model",
    )
    descriptive_statistic: SplitFrame = Field(
        default_factory=SplitFrame.empty,
        description="Descriptive statistics as a validated split-frame model",
    )

    @property
    def data_summary(self) -> DataSummary:
        """Return the canonical grouped data summary projection."""
        return DataSummary(
            regression_metrics=self.regression_metrics,
            descriptive_statistic=self.descriptive_statistic,
            linear_correlation=self.linear_correlation,
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
        conf_interval: ConfIntervalConfig | bool = False,
        bundle: CompositeModelBundle | None = None,
        source_x_column: str,
        source_y_columns: list[str],
        component_models: dict[str, str] | None = None,
    ) -> None:
        """Initialize PostProcessing class.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            minimizer: The minimizer class.
            result: The result of the minimization of the best fit.
            is_global: Whether global fitting mode is enabled.
            conf_interval: Canonical confidence interval settings, or ``False`` to skip.
            bundle: Optional CompositeModelBundle for local-fit decomposition.
            source_x_column: Source x-column name before canonical postprocess renaming.
            source_y_columns: Source y-column names before canonical postprocess renaming.
            component_models: Optional mapping from canonical component ids to
                registry model names for global-fit contribution reconstruction.

        """
        self._is_global = is_global
        self._conf_interval = conf_interval
        self._bundle = bundle
        self._component_models = component_models
        self._source_x_column = source_x_column
        self._source_y_columns = source_y_columns
        self.df = self._rename_columns(df=df)
        self.minimizer = minimizer
        self.result = result
        self._data_size = self._check_global_fitting()

    def __call__(self) -> PostProcessingResult:
        """Run post-processing and return typed result."""
        fit_insights = self._make_insight_report()
        confidence_interval = self._compute_confidence_interval()
        df = self._make_residual_fit(self.df)
        df = self._make_fit_contributions(df)

        return PostProcessingResult(
            df=df,
            fit_insights=fit_insights,
            confidence_interval=confidence_interval,
            linear_correlation=SplitFrame.from_dataframe(df.corr()),
            fit_result_data=SplitFrame.from_dataframe(df),
            regression_metrics=RegressionMetrics(df)(),
            descriptive_statistic=SplitFrame.from_dataframe(
                df.describe(percentiles=np.arange(0.1, 1, 0.1).tolist())
            ),
        )

    def _check_global_fitting(self) -> int | None:
        """Check if the global fitting is performed.

        Returns:
            int | None: The number of spectra of the global fitting.

        """
        if self._is_global:
            return sum(
                1
                for column in self.df.columns
                if column.startswith(f"{_COLS.intensity}_")
            )
        return None

    def _rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename the columns of the dataframe.

        Args:
            df: DataFrame containing the original input data.

        Returns:
            pd.DataFrame: DataFrame with renamed columns.

        """
        rename_map = {self._source_x_column: _COLS.energy}
        if self._is_global:
            rename_map.update(
                {
                    column: f"{_COLS.intensity}_{index}"
                    for index, column in enumerate(self._source_y_columns, start=1)
                }
            )
            return df.rename(columns=rename_map)

        if not self._source_y_columns:
            msg = "PostProcessing requires at least one y-column for standard fits."
            raise ValueError(msg)

        rename_map[self._source_y_columns[0]] = _COLS.intensity
        return df.rename(columns=rename_map)

    def _make_insight_report(self) -> FitInsights:
        """Build the fit insight report.

        Returns:
            FitInsights: Typed fit statistics, variables, errorbars, and correlations.

        """
        return FitInsights.from_minimizer_result(
            self.result,
            max_nfev=int(getattr(self.minimizer, "max_nfev", 0) or 0),
            nan_policy=str(
                getattr(
                    self.minimizer,
                    "nan_policy",
                    "raise",
                )
            ),
            scale_covar=(
                bool(self.minimizer.scale_covar)
                if hasattr(self.minimizer, "scale_covar")
                else None
            ),
            calc_covar=(
                bool(self.minimizer.calc_covar)
                if hasattr(self.minimizer, "calc_covar")
                else None
            ),
        )

    @staticmethod
    def _normalize_confidence_bounds(
        ci_payload: dict[str, object],
    ) -> dict[str, list[tuple[float, float]]]:
        """Normalize lmfit confidence output into canonical typed bounds."""
        normalized = normalize_confidence_results_payload(ci_payload)
        if isinstance(normalized, dict):
            return normalized
        return {}

    def _compute_confidence_interval(
        self,
    ) -> ConfidenceResults:
        """Compute confidence intervals if configured.

        Returns:
            ConfidenceResults: Typed confidence interval settings and results.

        """
        if not isinstance(self._conf_interval, ConfIntervalConfig):
            return ConfidenceResults(settings=False)

        try:
            ci_args = self._conf_interval.model_dump(exclude_none=True)
            min_rel_change = ci_args.pop("min_rel_change", None)
            ci = ConfidenceInterval(
                self.minimizer,
                self.result,
                **ci_args,
            )
            if min_rel_change is not None:
                ci.min_rel_change = min_rel_change

            return ConfidenceResults(
                settings=self._conf_interval,
                results=self._normalize_confidence_bounds(ci.calc_all_ci()),
            )

        except (MinimizerException, ValueError, KeyError):
            return ConfidenceResults(settings=self._conf_interval)

    def _global_intensity_columns(self) -> list[str]:
        """Return canonical intensity columns for a global fit."""
        if self._data_size is None:
            msg = "Global post-processing requires a detected global data size."
            raise ValueError(msg)
        return [
            _COLS.intensity_for_dataset(index)
            for index in range(1, self._data_size + 1)
        ]

    def _global_residual_matrix(self) -> np.ndarray:
        """Return the residual vector reshaped by spectrum for global fits."""
        if self._data_size is None:
            msg = "Global post-processing requires a detected global data size."
            raise ValueError(msg)
        return self.result.residual.reshape((-1, self._data_size)).T

    def _build_standard_residual_fit_payload(
        self,
        df: pd.DataFrame,
    ) -> ResidualFitPayload:
        """Build residual and fit columns for a standard fit."""
        residual = np.asarray(self.result.residual)
        return ResidualFitPayload(
            columns={
                _COLS.residual_for_dataset(None): residual,
                _COLS.fit_for_dataset(None): (
                    df[_COLS.intensity].to_numpy() + residual
                ),
            }
        )

    def _build_global_residual_fit_payload(
        self,
        df: pd.DataFrame,
    ) -> ResidualFitPayload:
        """Build residual and fit columns for a global fit."""
        residual_matrix = self._global_residual_matrix()
        fit_matrix = df[self._global_intensity_columns()].to_numpy().T + residual_matrix
        indexed_columns = {
            column_name: values
            for index, (residual_values, fit_values) in enumerate(
                zip(residual_matrix, fit_matrix, strict=True),
                start=1,
            )
            for column_name, values in (
                (_COLS.residual_for_dataset(index), residual_values),
                (_COLS.fit_for_dataset(index), fit_values),
            )
        }
        indexed_columns[_COLS.residual_for_dataset("avg")] = np.mean(
            residual_matrix,
            axis=0,
        )
        return ResidualFitPayload(columns=indexed_columns)

    def _build_residual_fit_payload(self, df: pd.DataFrame) -> ResidualFitPayload:
        """Build the residual/fit payload for the current fitting mode."""
        if self._is_global:
            return self._build_global_residual_fit_payload(df)
        return self._build_standard_residual_fit_payload(df)

    def _make_residual_fit(self, df: pd.DataFrame) -> pd.DataFrame:
        r"""Make the residuals of the model and the fit.

        The residual is calculated by the difference of the best fit model and
        the reference data. In case of a global fitting, the residuals are
        calculated for each spectra separately plus an averaged global residual.
        """
        payload = self._build_residual_fit_payload(df)
        return pd.concat([df.copy(), payload.to_frame(df.index)], axis=1)

    def _make_fit_contributions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Make the fit contributions of the best fit model."""
        return calculated_model(
            params=self.result.params,
            x=df[_COLS.energy].to_numpy(),
            df=df,
            global_fit=self._is_global,
            bundle=self._bundle,
            component_models=self._component_models,
        )

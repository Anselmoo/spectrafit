"""Result projection helpers for notebook metric and peak display tables."""

from __future__ import annotations

from statistics import fmean

import pandas as pd

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import VariableFitResult
from spectrafit.models.split_frame import SplitFrameAxis
from spectrafit.models.split_frame import SplitFrameCell
from spectrafit.reporting.service import SolverReportProjection
from spectrafit.reporting.service import project_solver_report


class NotebookMetricCell(BaseModel):
    """Single metric value prepared for notebook presentation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    value: float


class NotebookMetricProjection(BaseModel):
    """Typed metric projection before dataframe materialization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cells: list[NotebookMetricCell] = Field(default_factory=list)

    @classmethod
    def from_fit_result(cls, fit_result: FitResult) -> NotebookMetricProjection:
        """Build a notebook metric projection from canonical fit results."""
        return cls.from_solver_report(project_solver_report(fit_result))

    @classmethod
    def from_solver_report(
        cls,
        solver_report: SolverReportProjection,
    ) -> NotebookMetricProjection:
        """Build a notebook metric projection from the shared solver projection."""
        goodness_of_fit = [
            NotebookMetricCell(name=name, value=value)
            for name, value in solver_report.goodness_of_fit.items()
        ]
        regression_metrics = solver_report.regression_metrics
        regression_cells = [
            NotebookMetricCell(
                name=str(label), value=_mean_numeric_row(label=label, row=row)
            )
            for label, row in zip(
                regression_metrics.index,
                regression_metrics.data,
                strict=False,
            )
        ]
        return cls(cells=[*goodness_of_fit, *regression_cells])

    def to_dataframe(self) -> pd.DataFrame:
        """Materialize the projection as a one-row dataframe."""
        return pd.DataFrame({cell.name: [cell.value] for cell in self.cells})

    def append_to_dataframe(self, df_metric: pd.DataFrame) -> pd.DataFrame:
        """Append the current projection to the metrics dataframe boundary."""
        return pd.concat([df_metric, self.to_dataframe()], ignore_index=True)


class NotebookPeakCell(BaseModel):
    """Single component/parameter projection entry for notebook peak tables."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    component: str
    parameter: str
    value: float | None


class NotebookPeaksProjection(BaseModel):
    """Typed notebook peak projection before dataframe materialization."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    cells: list[NotebookPeakCell] = Field(default_factory=list)

    @classmethod
    def from_fit_result(cls, fit_result: FitResult) -> NotebookPeaksProjection:
        """Build a peak projection from canonical fit results."""
        return cls.from_solver_report(project_solver_report(fit_result))

    @classmethod
    def from_solver_report(
        cls,
        solver_report: SolverReportProjection,
    ) -> NotebookPeaksProjection:
        """Build a peak projection from the shared solver projection."""
        return cls(
            cells=[
                NotebookPeakCell(
                    component=component_key,
                    parameter=parameter_key,
                    value=getattr(variable_result, parameter_key),
                )
                for component_key, variable_result in solver_report.variables.items()
                for parameter_key in VariableFitResult.model_fields
            ]
        )

    def to_dataframe(self) -> pd.DataFrame:
        """Materialize the projection as a one-row multi-index dataframe."""
        tuples = [(cell.component, cell.parameter) for cell in self.cells]
        values = [cell.value for cell in self.cells]
        return pd.DataFrame(
            pd.Series(
                values,
                index=pd.MultiIndex.from_tuples(
                    tuples,
                    names=["component", "parameter"],
                ),
            ),
        ).T

    def append_to_dataframe(self, df_peaks: pd.DataFrame) -> pd.DataFrame:
        """Append the current projection to the peaks dataframe boundary."""
        return pd.concat([df_peaks, self.to_dataframe()], ignore_index=True)


def _mean_numeric_row(
    *,
    label: SplitFrameAxis,
    row: list[SplitFrameCell],
) -> float:
    """Return the mean for a typed regression-metric row."""
    numeric_row = [float(value) for value in row if isinstance(value, int | float)]
    if len(numeric_row) != len(row):
        msg = f"Regression metric '{label}' must contain only numeric values."
        raise TypeError(msg)
    if not numeric_row:
        msg = f"Regression metric '{label}' must contain at least one value."
        raise ValueError(msg)
    return fmean(numeric_row)


def append_peaks_dataframe(
    df_peaks: pd.DataFrame,
    fit_result: FitResult,
) -> pd.DataFrame:
    """Append one projected variable row to the peaks dataframe.

    Args:
        df_peaks: Existing notebook peaks dataframe.
        fit_result: Current fit result.

    Returns:
        pd.DataFrame: Updated peaks dataframe with appended row.
    """
    return NotebookPeaksProjection.from_fit_result(fit_result).append_to_dataframe(
        df_peaks
    )


def append_metric_dataframe(
    df_metric: pd.DataFrame,
    fit_result: FitResult,
) -> pd.DataFrame:
    """Append one current-metric row to the metric dataframe.

    Args:
        df_metric: Existing notebook metric dataframe.
        fit_result: Current fit result.

    Returns:
        pd.DataFrame: Updated metric dataframe with appended row.
    """
    return NotebookMetricProjection.from_fit_result(fit_result).append_to_dataframe(
        df_metric
    )

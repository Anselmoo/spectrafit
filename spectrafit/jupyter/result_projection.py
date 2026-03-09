"""Result projection helpers for notebook metric and peak display tables."""

from __future__ import annotations

import pandas as pd

from spectrafit.jupyter.solver import SolverResults
from spectrafit.models.results.fit_result import FitResult


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
    tuples: list[tuple[str, str]] = []
    values: list[float | None] = []
    for component_key, variable_result in fit_result.fit_insights.variables.items():
        for parameter_key, parameter_value in variable_result.model_dump().items():
            tuples.append((component_key, parameter_key))
            values.append(parameter_value)

    row = pd.DataFrame(
        pd.Series(
            values,
            index=pd.MultiIndex.from_tuples(
                tuples,
                names=["component", "parameter"],
            ),
        ),
    ).T

    return pd.concat(
        [df_peaks, row],
        ignore_index=True,
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
    return pd.concat(
        [df_metric, SolverResults(result=fit_result).get_current_metric],
        ignore_index=True,
    )

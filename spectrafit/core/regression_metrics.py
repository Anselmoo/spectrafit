"""Runtime regression metrics for fit post-processing."""

from __future__ import annotations

from typing import TYPE_CHECKING
from warnings import warn

import numpy as np
import pandas as pd

from sklearn.metrics import explained_variance_score
from sklearn.metrics import max_error
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.metrics import mean_poisson_deviance
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_log_error
from sklearn.metrics import median_absolute_error
from sklearn.metrics import r2_score

from spectrafit.models.split_frame import SplitFrame


if TYPE_CHECKING:
    from numpy.typing import NDArray


def warn_meassage(msg: str) -> str:
    """Generate a warning message."""
    top = "\n\n## WARNING " + "#" * (len(msg) - len("## WARNING ")) + "\n"
    header = "\n" + "#" * len(msg) + "\n"
    return top + msg + header


class RegressionMetrics:
    """Calculate regression metrics for runtime post-processing."""

    def __init__(
        self,
        df: pd.DataFrame,
        name_true: str = "intensity",
        name_pred: str = "fit",
    ) -> None:
        """Initialize the regression metrics calculator."""
        self.y_true, self.y_pred = self.initialize(
            df=df,
            name_true=name_true,
            name_pred=name_pred,
        )

    def initialize(
        self,
        df: pd.DataFrame,
        name_true: str = "intensity",
        name_pred: str = "fit",
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Split the input dataframe into true and predicted arrays."""
        true = df[
            [col_name for col_name in df.columns if name_true in col_name]
        ].to_numpy()

        pred = df[
            [col_name for col_name in df.columns if name_pred in col_name]
        ].to_numpy()

        if pred.shape != true.shape:
            msg = "The shape of the real and fit data-values are not equal!"
            raise ValueError(msg)

        return (
            (true, pred) if true.shape[1] > 1 else (np.array([true]), np.array([pred]))
        )

    def __call__(
        self,
    ) -> SplitFrame:
        """Calculate regression metrics as a validated split-frame model."""
        metrics_fnc = (
            explained_variance_score,
            r2_score,
            max_error,
            mean_absolute_error,
            mean_squared_error,
            mean_squared_log_error,
            median_absolute_error,
            mean_absolute_percentage_error,
            mean_poisson_deviance,
        )
        metric_dict: dict[str, list[float | None]] = {}
        for fnc in metrics_fnc:
            metric_dict[fnc.__name__] = []
            for y_true, y_pred in zip(self.y_true.T, self.y_pred.T, strict=False):
                try:
                    metric_dict[fnc.__name__].append(fnc(y_true, y_pred))
                except ValueError as err:
                    warn(
                        warn_meassage(
                            msg=f"Regression metric '{fnc.__name__}' could not  "
                            f"be calculated due to: {err}",
                        ),
                        stacklevel=2,
                    )
                    metric_dict[fnc.__name__].append(np.nan)
        return SplitFrame.from_dataframe(pd.DataFrame(metric_dict).T)

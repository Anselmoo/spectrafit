"""Regression metrics for fit analysis.

This module contains the RegressionMetrics class for calculating
regression metrics of fits for post analysis.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
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


if TYPE_CHECKING:
    from collections.abc import Hashable

    from numpy.typing import NDArray


def warn_meassage(msg: str) -> str:
    """Generate a warning message.

    Args:
        msg (str): The message to be printed.

    Returns:
        str: The warning message.

    """
    top = "\n\n## WARNING " + "#" * (len(msg) - len("## WARNING ")) + "\n"
    header = "\n" + "#" * len(msg) + "\n"
    return top + msg + header


class RegressionMetrics:
    """Calculate the regression metrics of the Fit(s) for the post analysis.

    !!! note  "Regression Metrics for post analysis of the Fit(s)"

        `SpectraFit` provides the following regression metrics for
        post analysis of the regular and global fit(s) based on the
        metric functions of `sklearn.metrics`:

            - `explained_variance_score`: Explained variance score.
            - `r2_score`: the coefficient of determination
            - `max_error`: Maximum error.
            - `mean_absolute_error`: the mean absolute error
            - `mean_squared_error`: the mean squared error
            - `mean_squared_log_error`: the mean squared log error
            - `median_absolute_error`: the median absolute error
            - `mean_absolute_percentage_error`: the mean absolute percentage error
            - `mean_poisson_deviance`: the mean Poisson deviance
            - `mean_gamma_deviance`: the mean Gamma deviance
            - `mean_tweedie_deviance`: the mean Tweedie deviance
            - `mean_pinball_loss`: the mean Pinball loss
            - `d2_tweedie_score`: the D2 Tweedie score
            - `d2_pinball_score`: the D2 Pinball score
            - `d2_absolute_error_score`: the D2 absolute error score

        The regression fit metrics can be used to evaluate the quality of the
        fit by comparing the fit to the actual intensity.

    !!! warning "D2 Tweedie and D2 Pinball scores"

         `d2_pinball_score` and `d2_absolute_error_score` are only available for
         `sklearn` versions >= 1.1.2 and will be later implemented if the
         __End of support (2023-06-27)__ is reached for the `Python3.7`.
    """

    def __init__(
        self,
        df: pd.DataFrame,
        name_true: str = "intensity",
        name_pred: str = "fit",
    ) -> None:
        """Initialize the regression metrics of the Fit(s) for the post analysis.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            name_true (str, optional): Name of the data. Defaults to "intensity".
            name_pred (str, optional): Name of the fit data. Defaults to "fit".

        """
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
        """Initialize the regression metrics of the Fit(s) for the post analysis.

        For this reason, the dataframe is split into two numpy array for true
        (`intensity`) and predicted (`fit`) intensities. In terms of global fit,
        the numpy array according to the order in the original dataframe.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence,
                 it will be extended by the single contribution of the model.
            name_true (str, optional): Name of the data. Defaults to "intensity".
            name_pred (str, optional): Name of the fit data. Defaults to "fit".

        Raises:
            ValueError: In terms of global fit contains an unequal number of intial data
                and fit data.

        Returns:
            Tuple[NDArray[np.float64], NDArray[np.float64]]: Tuple of true and predicted
                (fit) intensities.

        """
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

    def __call__(self) -> dict[Hashable, Any]:
        """Calculate the regression metrics of the Fit(s) for the post analysis.

        Returns:
            dict[Hashable, Any]: Dictionary containing the regression metrics.

        """
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
        metric_dict: dict[Hashable, Any] = {}
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
        return pd.DataFrame(metric_dict).T.to_dict(orient="split")

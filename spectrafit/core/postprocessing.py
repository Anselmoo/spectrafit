"""Post-processing utilities for SpectraFit.

This module contains the PostProcessing class for data post-processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import numpy as np
import pandas as pd

from lmfit.confidence import ConfidenceInterval
from lmfit.minimizer import MinimizerException

from spectrafit.api.tools_model import ColumnNamesAPI
from spectrafit.models.builtin import calculated_model
from spectrafit.report import RegressionMetrics
from spectrafit.report import fit_report_as_dict


if TYPE_CHECKING:
    from lmfit import Minimizer


class PostProcessing:
    """Post-processing of the dataframe."""

    def __init__(
        self,
        df: pd.DataFrame,
        args: dict[str, Any],
        minimizer: Minimizer,
        result: Any,
    ) -> None:
        """Initialize PostProcessing class.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.
            minimizer (Minimizer): The minimizer class.
            result (Any): The result of the minimization of the best fit.

        """
        self.args = args.copy()  # Work with a copy to avoid side effects
        self.df = self.rename_columns(df=df)
        self.minimizer = minimizer
        self.result = result
        self.data_size = self.check_global_fitting()

    def __call__(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Call the post-processing."""
        self.make_insight_report()
        self.make_residual_fit()
        self.make_fit_contributions()
        self.export_correlation2args()
        self.export_results2args()
        self.export_regression_metrics2args()
        self.export_desprective_statistic2args()
        return (self.df, self.args)

    def check_global_fitting(self) -> int | None:
        """Check if the global fitting is performed.

        !!! note "About Global Fitting"
            In case of the global fitting, the data is extended by the single
            contribution of the model.

        Returns:
            Optional[int]: The number of spectra of the global fitting.

        """
        if self.args["global_"]:
            return max(
                int(self.result.params[i].name.split("_")[-1])
                for i in self.result.params
            )
        return None

    def rename_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Rename the columns of the dataframe.

        Rename the columns of the dataframe to the names defined in the input file.

        Args:
            df (pd.DataFrame): DataFrame containing the original input data, which are
                 individually pre-named.

        Returns:
            pd.DataFrame: DataFrame containing renamed columns. All column-names are
                 lowered. In case of a regular fitting, the columns are named `energy`
                 and `intensity`. In case of a global fitting, `energy` stays `energy`
                 and `intensity` is extended by a `_`  and column index; like: `energy`
                 and `intensity_1`, `intensity_2`, `intensity_...` depending on
                 the dataset size.

        """
        if self.args["global_"]:
            return df.rename(
                columns={
                    col: (
                        ColumnNamesAPI().energy
                        if i == 0
                        else f"{ColumnNamesAPI().intensity}_{i}"
                    )
                    for i, col in enumerate(df.columns)
                },
            )
        return df.rename(
            columns={
                df.columns[0]: ColumnNamesAPI().energy,
                df.columns[1]: ColumnNamesAPI().intensity,
            },
        )

    def make_insight_report(self) -> None:
        """Make an insight-report of the fit statistic.

        !!! note "About Insight Report"

            The insight report based on:

                1. Configurations
                2. Statistics
                3. Variables
                4. Error-bars
                5. Correlations
                6. Covariance Matrix
                7. _Optional_: Confidence Interval

            All of the above are included in the report as dictionary in `args`.

        """
        self.args["fit_insights"] = fit_report_as_dict(
            inpars=self.result,
            settings=self.minimizer,
            modelpars=self.result.params,
        )
        if self.args["conf_interval"]:
            try:
                _min_rel_change = self.args["conf_interval"].pop("min_rel_change", None)
                ci = ConfidenceInterval(
                    self.minimizer,
                    self.result,
                    **self.args["conf_interval"],
                )
                if _min_rel_change is not None:
                    ci.min_rel_change = _min_rel_change
                    self.args["conf_interval"]["min_rel_change"] = _min_rel_change

                trace = self.args["conf_interval"].get("trace")

                if trace is True:
                    self.args["confidence_interval"] = (ci.calc_all_ci(), ci.trace_dict)
                else:
                    self.args["confidence_interval"] = ci.calc_all_ci()

            except (MinimizerException, ValueError, KeyError):
                self.args["confidence_interval"] = {}

    def make_residual_fit(self) -> None:
        r"""Make the residuals of the model and the fit.

        !!! note "About Residual and Fit"

            The residual is calculated by the difference of the best fit `model` and
            the reference `data`. In case of a global fitting, the residuals are
            calculated for each `spectra` separately plus an avaraged global residual.

            $$
            \mathrm{residual} = \mathrm{model} - \mathrm{data}
            $$
            $$
            \mathrm{residual}_{i} = \mathrm{model}_{i} - \mathrm{data}_{i}
            $$
            $$
            \mathrm{residual}_{avg} = \frac{ \sum_{i}
                \mathrm{model}_{i} - \mathrm{data}_{i}}{i}
            $$

            The fit is defined by the difference sum of fit and reference data. In case
            of a global fitting, the residuals are calculated for each `spectra`
            separately.
        """
        df_copy: pd.DataFrame = self.df.copy()
        if self.args["global_"]:
            residual = self.result.residual.reshape((-1, self.data_size)).T
            for i, _residual in enumerate(residual, start=1):
                df_copy[f"{ColumnNamesAPI().residual}_{i}"] = _residual
                df_copy[f"{ColumnNamesAPI().fit}_{i}"] = (
                    self.df[f"{ColumnNamesAPI().intensity}_{i}"].to_numpy() + _residual
                )
            df_copy[f"{ColumnNamesAPI().residual}_avg"] = np.mean(residual, axis=0)
        else:
            residual = self.result.residual
            df_copy[ColumnNamesAPI().residual] = residual
            df_copy[ColumnNamesAPI().fit] = (
                self.df[ColumnNamesAPI().intensity].to_numpy() + residual
            )
        self.df = df_copy

    def make_fit_contributions(self) -> None:
        """Make the fit contributions of the best fit model.

        !!! info "About Fit Contributions"
            The fit contributions are made independently of the local or global fitting.
        """
        self.df = calculated_model(
            params=self.result.params,
            x=self.df.iloc[:, 0].to_numpy(),
            df=self.df,
            global_fit=self.args["global_"],
        )

    def export_correlation2args(self) -> None:
        """Export the correlation matrix to the input file arguments.

        !!! note "About Correlation Matrix"

            The linear correlation matrix is calculated from and for the pandas
            dataframe and divided into two parts:

            1. Linear correlation matrix
            2. Non-linear correlation matrix (coming later ...)

        !!! note "About reading the correlation matrix"

            The correlation matrix is stored in the `args` as a dictionary with the
            following keys:

            * `index`
            * `columns`
            * `data`

            For re-reading the data, it is important to use the following code:

            >>> import pandas as pd
            >>> pd.DataFrame(**args["linear_correlation"])

            Important is to use the generator function for access the three keys and
            their values.
        """
        self.args["linear_correlation"] = self.df.corr().to_dict(orient="split")

    def export_results2args(self) -> None:
        """Export the results of the fit to the input file arguments."""
        self.args["fit_result"] = self.df.to_dict(orient="split")

    def export_regression_metrics2args(self) -> None:
        """Export the regression metrics of the fit to the input file arguments.

        !!! note "About Regression Metrics"
            The regression metrics are calculated by the `statsmodels.stats.diagnostic`
            module.
        """
        self.args["regression_metrics"] = RegressionMetrics(self.df)()

    def export_desprective_statistic2args(self) -> None:
        """Export the descriptive statistic of the spectra, fit, and contributions."""
        self.args["descriptive_statistic"] = self.df.describe(
            percentiles=np.arange(0.1, 1, 0.1).tolist(),
        ).to_dict(orient="split")

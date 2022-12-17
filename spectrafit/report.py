"""Fit-Results as Report."""
import pprint

from typing import Any
from typing import Dict
from typing import Hashable
from typing import List
from typing import Optional
from typing import Tuple

import numpy as np
import pandas as pd

from art import tprint
from lmfit import Minimizer
from lmfit import Parameters
from lmfit import conf_interval
from lmfit import report_ci
from lmfit import report_fit
from lmfit.minimizer import MinimizerException
from lmfit.minimizer import minimize
from numpy.typing import NDArray
from sklearn.metrics import explained_variance_score
from sklearn.metrics import max_error
from sklearn.metrics import mean_absolute_error
from sklearn.metrics import mean_absolute_percentage_error
from sklearn.metrics import mean_poisson_deviance
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_squared_log_error
from sklearn.metrics import median_absolute_error
from sklearn.metrics import r2_score
from spectrafit import __version__
from tabulate import tabulate


CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"
pp = pprint.PrettyPrinter(indent=4)


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
        self, df: pd.DataFrame, name_true: str = "intensity", name_pred: str = "fit"
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
            df=df, name_true=name_true, name_pred=name_pred
        )

    def initialize(
        self, df: pd.DataFrame, name_true: str = "intensity", name_pred: str = "fit"
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Initialize the regression metrics of the Fit(s) for the post analysis.

        For this reason, the dataframe is split into two numpy array for true
        (`intensity`) and predicted (`fit`) intensities. In terms of global fit,
        the numpy array according to the order in the original dataframe.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
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
            raise ValueError("The shape of the real and fit data-values are not equal!")

        return (
            (true, pred) if true.shape[1] > 1 else (np.array([true]), np.array([pred]))
        )

    def __call__(self) -> Dict[Hashable, Any]:
        """Calculate the regression metrics of the Fit(s) for the post analysis.

        Returns:
            Dict[Hashable, Any]: Dictionary containing the regression metrics.
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
        metric_dict: Dict[Hashable, Any] = {}
        for fnc in metrics_fnc:
            metric_dict[fnc.__name__] = []
            for y_true, y_pred in zip(self.y_true.T, self.y_pred.T):
                try:
                    metric_dict[fnc.__name__].append(fnc(y_true, y_pred))
                except ValueError as err:
                    print(f"## Warning: {err} for {fnc.__name__}!")
                    metric_dict[fnc.__name__].append(np.nan)
        return pd.DataFrame(metric_dict).T.to_dict(orient="split")


def fit_report_as_dict(
    inpars: minimize, modelpars: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[Any, Any]]:
    """Generate the best fit report as dictionary.

    !!! info "About `fit_report_as_dict`"

        The report contains the best-fit values for the parameters and their
        uncertainties and correlations. The report is generated as dictionary and
        consits of the following three main criteria:

            1. Fit Statistics
            2. Fit variables
            3. Fit correlations

    Args:
        inpars (minimize): Input Parameters from a fit or the  Minimizer results
             returned from a fit.
        modelpars (Dict[str,  Any], optional): Known Model Parameters.
            Defaults to None.

    Returns:
         Dict[str, Dict[Any, Any]]: The report as a dictionary.
    """
    result = inpars
    params = inpars.params

    parnames: List[str] = list(params.keys())

    buffer: Dict[str, Dict[Any, Any]] = {
        "configurations": {},
        "statistics": {},
        "variables": {},
        "errorbars": {},
        "correlations": {},
        "covariance_matrix": {},
    }

    result, buffer, params = _extracted_gof_from_results(
        result=result, buffer=buffer, params=params
    )
    for name in parnames:
        par = params[name]
        buffer["variables"][name] = {}

        if par.init_value is not None:
            buffer["variables"][name]["init_value"] = par.init_value
        elif par.expr is not None:
            buffer["variables"][name]["init_value"] = f"As expressed value: {par.expr}"
        else:
            buffer["variables"][name]["init_value"] = f"As fixed value: {par.value}"
        if modelpars is not None and name in modelpars:
            buffer["variables"][name]["model_value"] = modelpars[name].value
        try:
            buffer["variables"][name]["best_value"] = par.value
        except (TypeError, ValueError):
            buffer["variables"][name]["init_value"] = "NonNumericValue"
        if par.stderr is not None:
            buffer["variables"][name]["error_relative"] = par.stderr
            try:
                buffer["variables"][name]["error_absolute"] = (
                    abs(par.stderr / par.value) * 100
                )
            except ZeroDivisionError:
                buffer["variables"][name]["error_absolute"] = np.inf

    for i, name_1 in enumerate(parnames):
        par = params[name_1]
        buffer["correlations"][name_1] = {}
        if not par.vary:
            continue
        if hasattr(par, "correl") and par.correl is not None:
            for name_2 in parnames[i + 1 :]:
                if (
                    name_1 != name_2
                    and name_2 in par.correl
                    and abs(par.correl[name_2]) <= 1.0
                ):
                    buffer["correlations"][name_1][name_2] = par.correl[name_2]

    if result.covar is not None and result.covar.shape[0] == len(parnames):
        for i, name_1 in enumerate(parnames):
            buffer["covariance_matrix"][name_1] = {
                name_2: result.covar[i, j] for j, name_2 in enumerate(parnames)
            }
    return buffer


def _extracted_gof_from_results(
    result: minimize, buffer: Dict[str, Any], params: Parameters
) -> Tuple[minimize, Dict[str, Any], Parameters]:
    """Extract the goodness of fit from the results.

    Args:
        result (minimize): Input Parameters from a fit or the  Minimizer results
        buffer (Dict[str, Any]): The buffer to store the results.
        params (Parameters): The parameters of the fit.

    Returns:
        minimize: The results.
        Dict[str, Any]: The buffer with updated results.
        Parameters: The parameters.
    """
    if result is not None:
        buffer["configurations"]["fitting_method"] = result.method
        buffer["configurations"]["function_evals"] = result.nfev
        buffer["configurations"]["data_points"] = result.ndata
        buffer["configurations"]["variable_names"] = result.var_names
        buffer["configurations"]["variable_numbers"] = result.nvarys
        buffer["configurations"]["degree_of_freedom"] = result.nfree

        buffer["statistics"]["chi-square"] = result.chisqr
        buffer["statistics"]["reduced_chi_square"] = result.redchi
        buffer["statistics"]["akaike_information"] = result.aic
        buffer["statistics"]["bayesian_information"] = result.bic

        if not result.errorbars:
            print("##  Warning: uncertainties could not be estimated:")
            if result.method not in ("leastsq", "least_squares"):
                print(
                    f"The fitting method '{result.method}' does not natively calculate"
                    " and uncertainties cannot be estimated due to be out of region!"
                )

            parnames_varying = [par for par in result.params if result.params[par].vary]
            for name in parnames_varying:
                par = params[name]
                if par.init_value and np.allclose(par.value, par.init_value):
                    buffer["errorbars"]["at_initial_value"] = name
                if np.allclose(par.value, par.min) or np.allclose(par.value, par.max):
                    buffer["errorbars"]["at_boundary"] = name
    return result, buffer, params


class PrintingResults:
    """Print the results of the fitting process."""

    def __init__(
        self,
        args: Dict[str, Any],
        result: Any,
        minimizer: Minimizer,
    ) -> None:
        """Initialize the PrintingResults class.

        Args:
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.
            result (Any): The lmfit `results` as a kind of result based class.
            minimizer (Minimizer): The lmfit `Minimizer`-class as a general minimizer
                 for curve fitting and optimization.
        """
        self.args = args
        self.result = result
        self.minimizer = minimizer
        self.correlation = pd.DataFrame.from_dict(args["linear_correlation"])

    def __call__(self) -> None:
        """Print the results of the fitting process."""
        if self.args["verbose"] == 1:
            self.printing_verbose_mode
        elif self.args["verbose"] == 2:
            self.printing_regular_mode

    @staticmethod
    def print_tabulate(args: Dict[str, Any]) -> None:
        """Print the results of the fitting process.

        Args:
            args (Dict[str, Any]): The args to be printed as a dictionary.
        """
        print(
            tabulate(
                pd.DataFrame(**args).T,
                headers="keys",
                tablefmt="fancy_grid",
                floatfmt=".3f",
            )
        )

    @property
    def printing_regular_mode(self) -> None:
        """Print the fitting results in the regular mode."""
        self.print_statistic()
        self.print_fit_results()
        self.print_confidence_interval()
        self.print_linear_correlation()
        self.print_regression_metrics()

    def print_statistic(self) -> None:
        """Print the statistic."""
        print("\nStatistic:\n")
        self.print_tabulate(args=self.args["data_statistic"])

    def print_fit_results(self) -> None:
        """Print the fit results."""
        print("\nFit Results and Insights:\n")
        print(
            report_fit(self.result, modelpars=self.result.params, **self.args["report"])
        )

    def print_confidence_interval(self) -> None:
        """Print the confidence interval."""
        print("\nConfidence Interval:\n")
        if self.args["conf_interval"]:
            try:
                report_ci(
                    conf_interval(
                        self.minimizer, self.result, **self.args["conf_interval"]
                    )
                )
            except (MinimizerException, ValueError, KeyError) as exc:
                print(f"Error: {exc} -> No confidence interval could be calculated!")
                self.args["confidence_interval"] = {}

    def print_linear_correlation(self) -> None:
        """Print the linear correlation."""
        print("\nOverall Linear-Correlation:\n")
        self.print_tabulate(args=self.args["linear_correlation"])

    def print_regression_metrics(self) -> None:
        """Print the regression metrics."""
        print("\nRegression Metrics:\n")
        self.print_tabulate(args=self.args["regression_metrics"])

    @property
    def printing_verbose_mode(self) -> None:
        """Print all results in verbose mode."""
        self.print_statistic_verbose()
        self.print_input_parameters_verbose()
        self.print_fit_results_verbose()
        self.print_confidence_interval_verbose()
        self.print_linear_correlation_verbose()
        self.print_regression_metrics_verbose()

    def print_statistic_verbose(self) -> None:
        """Print the data statistic in verbose mode."""
        print("\nStatistic:\n")
        pp.pprint(self.args["data_statistic"])

    def print_input_parameters_verbose(self) -> None:
        """Print input parameters in verbose mode."""
        print("Input Parameter:\n")
        pp.pprint(self.args)

    def print_fit_results_verbose(self) -> None:
        """Print fit results in verbose mode."""
        print("\nFit Results and Insights:\n")
        pp.pprint(self.args["fit_insights"])

    def print_confidence_interval_verbose(self) -> None:
        """Print confidence interval in verbose mode."""
        if self.args["conf_interval"]:
            print("\nConfidence Interval:\n")
            pp.pprint(self.args["confidence_interval"])

    def print_linear_correlation_verbose(self) -> None:
        """Print overall linear-correlation in verbose mode."""
        print("\nOverall Linear-Correlation:\n")
        pp.pprint(self.args["linear_correlation"])

    def print_regression_metrics_verbose(self) -> None:
        """Print regression metrics in verbose mode."""
        print("\nRegression Metrics:\n")
        pp.pprint(self.args["regression_metrics"])


class PrintingStatus:
    """Print the status of the fitting process."""

    @property
    def welcome(self) -> None:
        """Print the welcome message."""
        tprint("SpectraFit", font="3-d")

    @property
    def version(self) -> None:
        """Print current version of the SpectraFit."""
        print(f"Currently used version is: {__version__}")

    @property
    def start(self) -> None:
        """Print the start of the fitting process."""
        print("\nStart of the fitting process:\n")

    @property
    def end(self) -> None:
        """Print the end of the fitting process."""
        print("\nEnd of the fitting process:\n")

    @property
    def thanks(self) -> None:
        """Print the end of the fitting process."""
        print("\nThanks for using SpectraFit!")

    @property
    def yes_no(self) -> None:
        """Print the end of the fitting process."""
        print("\nDo you want to continue? (y/n)")

    @property
    def credits(self) -> None:
        """Print the credits of the fitting process."""
        tprint("\nCredits:\n", font="3-d")
        print(
            "The fitting process is based on the following software:"
            "\n\t- lmfit (https://lmfit.github.io/lmfit-py/index.html)"
            "\n\t- statsmodel (https://www.statsmodels.org/stable/)"
            "\n\t- scipy (https://docs.scipy.org/doc/scipy/reference/index.html)"
            "\n\t- scikit-learn (https://scikit-learn.org/stable/)"
            "\n\t- numpy (https://docs.scipy.org/doc/numpy/reference/index.html)"
            "\n\t- pandas (https://pandas.pydata.org/pandas-docs/stable/index.html)"
            "\n\t- matplotlib (https://matplotlib.org/index.html)"
            "\n\t- seaborn (https://seaborn.pydata.org/index.html)"
            "\n\t- tabulate (https://github.com/astanin/python-tabulate))"
            "\n\t- argparse (https://docs.python.org/3/library/argparse.html)"
            "\n\t- anymany more "
            "(https://github.com/Anselmoo/spectrafit/network/dependencies)"
        )

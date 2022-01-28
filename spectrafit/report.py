"""Fit-Results as Report."""
import pprint

from typing import Any
from typing import Dict

import numpy as np
import pandas as pd

from lmfit import Minimizer
from lmfit import conf_interval
from lmfit import report_ci
from lmfit import report_fit
from lmfit.minimizer import MinimizerException
from lmfit.minimizer import minimize
from spectrafit import __version__
from tabulate import tabulate


CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"
pp = pprint.PrettyPrinter(indent=4)


def fit_report_as_dict(inpars: minimize, modelpars: dict = None) -> dict:
    """Generate the best fit report as dictionary.

    The report contains the best-fit values for the parameters and their
    uncertainties and correlations.

    Args:
        inpars (minimize): Input Parameters from a fit or the  Minimizer results
             returned from a fit.
        modelpars (dict, optional): Known Model Parameters. Defaults to None.

    Returns:
        dict: [description]
    """
    result = inpars
    params = inpars.params

    parnames = list(params.keys())

    buffer: dict = {
        "configurations": {},
        "statistics": {},
        "variables": {},
        "errorbars": {},
        "correlations": {},
        "covariance_matrix": {},
    }
    # Fit Statistics
    # Fit variables
    # Fit correlations
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
                    name != name_2
                    and name_2 in par.correl
                    and abs(par.correl[name_2]) <= 1.0
                ):
                    buffer["correlations"][name_1][name_2] = par.correl[name_2]
    try:
        for i, name_1 in enumerate(parnames):
            buffer["covariance_matrix"][name_1] = {
                name_2: result.covar[i, j] for j, name_2 in enumerate(parnames)
            }

    except (AttributeError, IndexError) as exc:
        print(f"{exc}: Covariance Matrix could not be calculated.\n")
    return buffer


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

    @property
    def printing_regular_mode(self) -> None:
        """Print the fitting results in the regular mode."""
        print("\nStatistic:\n")
        print(
            tabulate(
                pd.DataFrame.from_dict(self.args["data_statistic"]),
                headers="keys",
                tablefmt="fancy_grid",
                floatfmt=".2f",
            )
        )
        print("\nFit Results and Insights:\n")
        print(
            report_fit(self.result, modelpars=self.result.params, **self.args["report"])
        )
        if self.args["conf_interval"]:
            print("\nConfidence Interval:\n")
            try:
                report_ci(
                    conf_interval(
                        self.minimizer, self.result, **self.args["conf_interval"]
                    )
                )
            except MinimizerException as exc:
                print(f"Error: {exc} -> No confidence interval could be calculated!")
                self.args["confidence_interval"] = None
        print("\nOverall Linear-Correlation:\n")
        print(
            tabulate(
                pd.DataFrame.from_dict(self.args["linear_correlation"]),
                headers="keys",
                tablefmt="fancy_grid",
                floatfmt=".2f",
            )
        )

    @property
    def printing_verbose_mode(self) -> None:
        """Print all results in verbose mode."""
        print("\nStatistic:\n")
        pp.pprint(self.args["data_statistic"])
        print("Input Parameter:\n")
        pp.pprint(self.args)
        print("\nFit Results and Insights:\n")
        pp.pprint(self.args["fit_insights"])
        if self.args["conf_interval"]:
            print("\nConfidence Interval:\n")
            pp.pprint(self.args["confidence_interval"])
        print("\nOverall Linear-Correlation:\n")
        pp.pprint(self.args["linear_correlation"])


class PrintingStatus:
    """Print the status of the fitting process."""

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
        print("\nCredits:\n")
        print(
            "The fitting process is based on the following software:"
            "\n\t- lmfit (https://lmfit.github.io/lmfit-py/index.html)"
            "\n\t- statsmodel (https://www.statsmodels.org/stable/)"
            "\n\t- scipy (https://docs.scipy.org/doc/scipy/reference/index.html)"
            "\n\t- numpy (https://docs.scipy.org/doc/numpy/reference/index.html)"
            "\n\t- pandas (https://pandas.pydata.org/pandas-docs/stable/index.html)"
            "\n\t- matplotlib (https://matplotlib.org/index.html)"
            "\n\t- seaborn (https://seaborn.pydata.org/index.html)"
            "\n\t- tabulate (https://github.com/astanin/python-tabulate))"
            "\n\t- argparse (https://docs.python.org/3/library/argparse.html)"
            "\n\t- anymany more "
            "(https://github.com/Anselmoo/spectrafit/network/dependencies)"
        )

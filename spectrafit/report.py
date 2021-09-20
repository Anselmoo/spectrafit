"""Fit-Results as Report."""
import pprint

from typing import Any

import numpy as np
import pandas as pd

from lmfit import Minimizer
from lmfit import conf_interval
from lmfit import report_ci
from lmfit import report_fit
from lmfit.minimizer import minimize
from lmfit.parameter import Parameters
from lmfit.printfuncs import alphanumeric_sort
from tabulate import tabulate


CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"
pp = pprint.PrettyPrinter(indent=4)


def fit_report_as_dict(
    inpars: minimize, modelpars: dict = None, sort_pars: bool = False
) -> dict:
    """Generate the best fit report as dictionary.

    The report contains the best-fit values for the parameters and their
    uncertainties and correlations.

    Args:
        inpars (minimize): Input Parameters from a fit or the  Minimizer results
             returned from a fit.
        modelpars (dict, optional): Known Model Parameters. Defaults to None.
        sort_pars (bool, optional): Whether to show parameter names sorted in
             alphanumerical order. If False (default), then the parameters will be
             listed in the order they were buffered to the Parameters dictionary. If
             callable, then this (one argument) function is used to extract a
             comparison key from each list element. Defaults to False.

    Raises:
        SystemExit: In case of `numdifftools` is not installed, it can raise SystemExit.

    Returns:
        dict: [description]
    """
    if isinstance(inpars, Parameters):
        result, params = None, inpars
    if hasattr(inpars, "params"):
        result = inpars
        params = inpars.params

    if sort_pars:
        key = sort_pars if callable(sort_pars) else alphanumeric_sort
        parnames = sorted(params, key=key)
    else:
        # dict.keys() returns a KeysView in py3, and they're indexed
        # further down
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
                raise SystemExit(
                    "    this fitting method does not natively calculate uncertainties"
                    "    and numdifftools is not installed for lmfit to do this. Use"
                    "    `pip install numdifftools` for lmfit to estimate uncertainties"
                    "    with this fitting method."
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
            buffer["covariance_matrix"][name_1] = {}
            for j, name_2 in enumerate(parnames):
                buffer["covariance_matrix"][name_1][name_2] = result.covar[i, j]
    except AttributeError as exc:
        print(f"{exc}: Covariance Matrix could not be calculated.\n")
    return buffer


def printing_regular_mode(
    args: dict, result: Any, minimizer: Minimizer, correlation: pd.DataFrame
) -> None:
    """Printing the fitting results in the regular mode.

    Args:
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.
        result (Any): The lmfit `results` as a kind of result based class.
        minimizer (Minimizer): The lmfit `Minimizer`-class as a general minimizer for
             curve fitting and optimization.
        correlation (pd.DataFrame): The correlation results of the global fit as pandas
             DataFrame.
    """
    print("\nStatistic:\n")
    print(
        tabulate(
            pd.DataFrame.from_dict(args["data_statistic"]),
            headers="keys",
            tablefmt="fancy_grid",
            floatfmt=".2f",
        )
    )
    print("\nFit Results and Insights:\n")
    print(report_fit(result, modelpars=result.params, **args["report"]))
    if args["conf_interval"]:
        print("\nConfidence Interval:\n")
        report_ci(conf_interval(minimizer, result, **args["conf_interval"]))
    print("\nOverall Linear-Correlation:\n")
    print(tabulate(correlation, headers="keys", tablefmt="fancy_grid", floatfmt=".2f"))


def printing_verbose_mode(args: dict) -> None:
    """Printing all results in verbose mode.

    Args:
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.
    """
    print("\nStatistic:\n")
    pp.pprint(args["data_statistic"])
    print("Input Parameter:\n")
    pp.pprint(args)
    print("\nFit Results and Insights:\n")
    pp.pprint(args["fit_insights"])
    if args["conf_interval"]:
        print("\nConfidence Interval:\n")
        pp.pprint(args["confidence_interval"])
    print("\nOverall Linear-Correlation:\n")
    pp.pprint(args["linear_correlation"])

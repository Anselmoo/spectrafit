"""Fit-Results as Report."""
import numpy as np

from lmfit.parameter import Parameters
from lmfit.printfuncs import alphanumeric_sort


try:
    import numdifftools  # noqa: F401

    HAS_NUMDIFFTOOLS = True
except ImportError:
    HAS_NUMDIFFTOOLS = False
CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"


def fit_report_as_dict(
    inpars: dict, modelpars: dict = None, sort_pars: bool = False
) -> dict:
    """Generate the best fit report as dictionary.

    The report contains the best-fit values for the parameters and their
    uncertainties and correlations.

    Args:
        inpars (dict): Input Parameters from fit or MinimizerResult returned from a fit.
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

    buffer = {
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
            if (
                result.method not in ("leastsq", "least_squares")
                and not HAS_NUMDIFFTOOLS
            ):
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

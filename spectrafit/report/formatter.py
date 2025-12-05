"""Fit report formatting functions.

This module contains functions for generating fit reports as dictionaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any
from warnings import warn

import numpy as np

from spectrafit.report.metrics import warn_meassage


if TYPE_CHECKING:
    from lmfit import Minimizer
    from lmfit import Parameter
    from lmfit import Parameters
    from lmfit.minimizer import minimize


def fit_report_as_dict(  # noqa: C901
    inpars: minimize,
    settings: Minimizer,
    modelpars: dict[str, Any] | None = None,
) -> dict[str, dict[Any, Any]]:
    """Generate the best fit report as dictionary.

    !!! info "About `fit_report_as_dict`"

        The report contains the best-fit values for the parameters and their
        uncertainties and correlations. The report is generated as dictionary and
        consists of the following three main criteria:

            1. Fit Statistics
            2. Fit variables
            3. Fit correlations

    !!! tip "About `Pydantic` for the report"

        In a next release, the report will be generated as a `Pydantic` model.

    Args:
        inpars (minimize): Input Parameters from a fit or the  Minimizer results
             returned from a fit.
        settings (Minimizer): The lmfit `Minimizer`-class as a general minimizer
                for curve fitting and optimization. It is required to extract the
                initial settings of the fit.
        modelpars (dict[str,  Any], optional): Known Model Parameters.
            Defaults to None.

    Returns:
         dict[str, Dict[Any, Any]]: The report as a dictionary.

    """
    result = inpars
    params = inpars.params

    parnames: list[str] = list(params.keys())

    buffer: dict[str, dict[Any, Any]] = {
        "configurations": {},
        "statistics": {},
        "variables": {},
        "errorbars": {},
        "correlations": {},
        "covariance_matrix": {},
        "computational": {},
    }

    result, buffer, params = _extracted_gof_from_results(
        result=result,
        buffer=buffer,
        params=params,
    )
    buffer = _extracted_computational_from_results(
        result=result,
        settings=settings,
        buffer=buffer,
    )
    for name in parnames:
        par = params[name]
        buffer["variables"][name] = {"init_value": get_init_value(param=par)}

        if modelpars is not None and name in modelpars:
            buffer["variables"][name]["model_value"] = modelpars[name].value
        try:
            buffer["variables"][name]["best_value"] = par.value
        except (TypeError, ValueError):  # pragma: no cover
            buffer["variables"][name]["init_value"] = "NonNumericValue"
        if par.stderr is not None:
            buffer["variables"][name]["error_relative"] = par.stderr
            try:
                buffer["variables"][name]["error_absolute"] = (
                    abs(par.stderr / par.value) * 100
                )
            except ZeroDivisionError:  # pragma: no cover
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


def get_init_value(
    param: Parameter,
    modelpars: Parameter | None = None,
) -> float | str:
    """Get the initial value of a parameter.

    Args:
        param (Parameter): The Parameter to extract the initial value from.
        modelpars (Parameter, optional): Known Model Parameters. Defaults to None.

    Returns:
        Union[float, str]: The initial value.

    """
    if param.init_value is not None:
        return param.init_value
    if param.expr is not None:
        return f"As expressed value: {param.expr}"
    if modelpars is not None and param.name in modelpars:
        return modelpars[param.name].value
    return f"As fixed value: {param.value}"


def _extracted_computational_from_results(
    result: minimize,
    settings: Minimizer,
    buffer: dict[str, Any],
) -> dict[str, Any]:
    """Extract the computational from the results.

    Args:
        result (minimize): Input Parameters from a fit or the  Minimizer results
            returned from a fit.
        settings (Minimizer): The lmfit `Minimizer`-class as a general minimizer
                for curve fitting and optimization. It is required to extract the
                initial settings of the fit.
        buffer (dict[str, Any]): The buffer to store the results.

    Returns:
        dict[str, Any]: The buffer with updated results.

    """
    buffer["computational"]["success"] = result.success
    if hasattr(result, "message"):
        buffer["computational"]["message"] = result.message
    buffer["computational"]["errorbars"] = result.errorbars
    buffer["computational"]["nfev"] = result.nfev

    buffer["computational"]["max_nfev"] = settings.max_nfev
    buffer["computational"]["scale_covar"] = settings.scale_covar
    buffer["computational"]["calc_covar"] = settings.calc_covar

    return buffer


def _extracted_gof_from_results(
    result: minimize,
    buffer: dict[str, Any],
    params: Parameters,
) -> tuple[minimize, dict[str, Any], Parameters]:
    """Extract the goodness of fit from the results.

    Args:
        result (minimize): Input Parameters from a fit or the  Minimizer results
        buffer (dict[str, Any]): The buffer to store the results.
        params (Parameters): The parameters of the fit.

    Returns:
        minimize: The results.
        dict[str, Any]: The buffer with updated results.
        Parameters: The parameters.

    """
    if result is not None:
        buffer["configurations"]["fitting_method"] = result.method
        buffer["configurations"]["function_evals"] = result.nfev
        buffer["configurations"]["data_points"] = result.ndata
        buffer["configurations"]["variable_names"] = result.var_names
        buffer["configurations"]["variable_numbers"] = result.nvarys
        buffer["configurations"]["degree_of_freedom"] = result.nfree

        buffer["statistics"]["chi_square"] = result.chisqr
        buffer["statistics"]["reduced_chi_square"] = result.redchi
        buffer["statistics"]["akaike_information"] = result.aic
        buffer["statistics"]["bayesian_information"] = result.bic

        if not result.errorbars:
            warn(warn_meassage("Uncertainties could not be estimated"), stacklevel=2)

            if result.method not in ("leastsq", "least_squares"):
                warn(
                    warn_meassage(
                        msg=f"The fitting method '{result.method}' does not "
                        "natively calculate and uncertainties cannot be "
                        "estimated due to be out of region!",
                    ),
                    stacklevel=2,
                )

            parnames_varying = [par for par in result.params if result.params[par].vary]
            for name in parnames_varying:
                par = params[name]
                if par.init_value and np.allclose(par.value, par.init_value):
                    buffer["errorbars"]["at_initial_value"] = name
                    warn(
                        warn_meassage(
                            msg=f"The parameter '{name}' is at its initial "
                            "value and uncertainties cannot be estimated!",
                        ),
                        stacklevel=2,
                    )
                if np.allclose(par.value, par.min) or np.allclose(par.value, par.max):
                    buffer["errorbars"]["at_boundary"] = name
                    warn(
                        warn_meassage(
                            msg=f"The parameter '{name}' is at its boundary "
                            "and uncertainties cannot be estimated!",
                        ),
                        stacklevel=2,
                    )

    return result, buffer, params

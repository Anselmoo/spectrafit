import numpy as np

from lmfit.parameter import Parameters
from lmfit.printfuncs import alphanumeric_sort
from lmfit.printfuncs import getfloat_attr
from lmfit.printfuncs import gformat


try:
    import numdifftools  # noqa: F401

    HAS_NUMDIFFTOOLS = True
except ImportError:
    HAS_NUMDIFFTOOLS = False
CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"


def fit_report_as_dict(
    inpars, modelpars=None, show_correl=True, min_correl=0.1, sort_pars=False
):
    """Generate a report of the fitting results.

    The report contains the best-fit values for the parameters and their
    uncertainties and correlations.

    Parameters
    ----------
    inpars : Parameters
        Input Parameters from fit or MinimizerResult returned from a fit.
    modelpars : Parameters, optional
        Known Model Parameters.
    show_correl : bool, optional
        Whether to show list of sorted correlations (default is True).
    min_correl : float, optional
        Smallest correlation in absolute value to show (default is 0.1).
    sort_pars : bool or callable, optional
        Whether to show parameter names sorted in alphanumerical order. If
        False (default), then the parameters will be listed in the order
        they were added to the Parameters dictionary. If callable, then
        this (one argument) function is used to extract a comparison key
        from each list element.

    Returns
    -------
    str
        Multi-line text of fit report.

    """

    if isinstance(inpars, Parameters):
        result, params = None, inpars
    if hasattr(inpars, "params"):
        result = inpars
        params = inpars.params

    if sort_pars:
        if callable(sort_pars):
            key = sort_pars
        else:
            key = alphanumeric_sort
        parnames = sorted(params, key=key)
    else:
        # dict.keys() returns a KeysView in py3, and they're indexed
        # further down
        parnames = list(params.keys())

    # buff = {}
    add = {
        "configurations": {},
        "statistics": {},
        "variables": {},
        "errorbars": {},
        "correlations": {},
    }
    # Fit Statistics
    # Fit variables
    # Fit correlations
    namelen = max([len(n) for n in parnames])
    if result is not None:

        add["configurations"]["fitting_method"] = result.method
        add["configurations"]["function_evals"] = result.nfev
        add["configurations"]["data_points"] = result.ndata
        add["configurations"]["variables"] = result.nvarys
        add["configurations"]["degree_of_freedom"] = result.nfree

        add["statistics"]["chi-square"] = result.chisqr
        add["statistics"]["reduced_chi_square"] = result.redchi
        add["statistics"]["akaike_information"] = result.aic
        add["statistics"]["bayesian_information"] = result.bic
        if not result.errorbars:
            print("##  Warning: uncertainties could not be estimated:")
            if result.method in ("leastsq", "least_squares") or HAS_NUMDIFFTOOLS:
                parnames_varying = [
                    par for par in result.params if result.params[par].vary
                ]
                for name in parnames_varying:
                    par = params[name]
                    space = " " * (namelen - len(name))
                    if par.init_value and np.allclose(par.value, par.init_value):
                        add["errorbars"]["at_initial_value"] = name
                    if np.allclose(par.value, par.min) or np.allclose(
                        par.value, par.max
                    ):
                        add["errorbars"]["at_boundary"] = name
            else:
                raise SystemExit(
                    "    this fitting method does not natively calculate uncertainties"
                    "    and numdifftools is not installed for lmfit to do this. Use"
                    "    `pip install numdifftools` for lmfit to estimate uncertainties"
                    "    with this fitting method."
                )

    add("[[Variables]]")
    for name in parnames:
        par = params[name]
        add["variables"][name] = {}
        space = " " * (namelen - len(name))
        nout = "%s:%s" % (name, space)
        inval = "(init = ?)"

        if par.init_value is not None:
            add["variables"][name]["init_value"] = par.init_value
        if modelpars is not None and name in modelpars:
            add["variables"][name]["model_value"] = modelpars[name].value
        try:
            add["variables"][name]["best_value"] = par.value
        except (TypeError, ValueError):
            sval = " Non Numeric Value?"
        if par.stderr is not None:
            add["variables"][name]["error_relative"] = par.stderr
            try:
                add["variables"][name]["error_absolute"] = abs(par.stderr / par.value)
            except ZeroDivisionError:
                add["variables"][name]["error_absolute"] = np.inf

        if par.vary:
            add("    %s %s %s" % (nout, sval, inval))
        elif par.expr is not None:
            add("    %s %s == '%s'" % (nout, sval, par.expr))
        else:
            add("    %s % .7g (fixed)" % (nout, par.value))

    if show_correl:
        correls = {}
        for i, name in enumerate(parnames):
            par = params[name]
            if not par.vary:
                continue
            if hasattr(par, "correl") and par.correl is not None:
                for name2 in parnames[i + 1 :]:
                    if (
                        name != name2
                        and name2 in par.correl
                        and abs(par.correl[name2]) > min_correl
                    ):
                        correls["%s, %s" % (name, name2)] = par.correl[name2]

        sort_correl = sorted(correls.items(), key=lambda it: abs(it[1]))
        sort_correl.reverse()
        if len(sort_correl) > 0:
            add(CORREL_HEAD % min_correl)
            maxlen = max([len(k) for k in list(correls.keys())])
        for name, val in sort_correl:
            lspace = max(0, maxlen - len(name))
            add("    C(%s)%s = % .3f" % (name, (" " * 30)[:lspace], val))

    return add

"""Fit-Results as Report."""

import pprint
import sys

from typing import Any
from typing import Callable
from typing import Dict
from typing import Hashable
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union
from warnings import warn

import numpy as np
import pandas as pd

from art import tprint
from lmfit import Minimizer
from lmfit import Parameter
from lmfit import Parameters
from lmfit.minimizer import MinimizerException
from lmfit.minimizer import minimize
from lmfit.printfuncs import alphanumeric_sort
from lmfit.printfuncs import getfloat_attr
from lmfit.printfuncs import gformat
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
                    warn(
                        warn_meassage(
                            msg=f"Regression metric '{fnc.__name__}' could not  "
                            f"be calculated due to: {err}"
                        ),
                        stacklevel=2,
                    )
                    metric_dict[fnc.__name__].append(np.nan)
        return pd.DataFrame(metric_dict).T.to_dict(orient="split")


def fit_report_as_dict(
    inpars: minimize, settings: Minimizer, modelpars: Optional[Dict[str, Any]] = None
) -> Dict[str, Dict[Any, Any]]:
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
        "computational": {},
    }

    result, buffer, params = _extracted_gof_from_results(
        result=result, buffer=buffer, params=params
    )
    buffer = _extracted_computational_from_results(
        result=result, settings=settings, buffer=buffer
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
    param: Parameter, modelpars: Optional[Parameter] = None
) -> Union[float, str]:
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
    result: minimize, settings: Minimizer, buffer: Dict[str, Any]
) -> Dict[str, Any]:
    """Extract the computational from the results.

    Args:
        result (minimize): Input Parameters from a fit or the  Minimizer results
            returned from a fit.
        settings (Minimizer): The lmfit `Minimizer`-class as a general minimizer
                for curve fitting and optimization. It is required to extract the
                initial settings of the fit.
        buffer (Dict[str, Any]): The buffer to store the results.

    Returns:
        Dict[str, Any]: The buffer with updated results.
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
                        "estimated due to be out of region!"
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
                            "value and uncertainties cannot be estimated!"
                        ),
                        stacklevel=2,
                    )
                if np.allclose(par.value, par.min) or np.allclose(par.value, par.max):
                    buffer["errorbars"]["at_boundary"] = name
                    warn(
                        warn_meassage(
                            msg=f"The parameter '{name}' is at its boundary "
                            "and uncertainties cannot be estimated!"
                        ),
                        stacklevel=2,
                    )

    return result, buffer, params


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


class CIReport:
    """Generate a report of confidence intervals.

    !!! info "About the Confidence Interval Report"

        This class is responsible for generating a report that displays confidence
        intervals for a given set of parameters. The report can be generated as a
        table.

        Please also check the original implementation of the `lmfit` package:
        https://lmfit.github.io/lmfit-py/confidence.html#lmfit.ci_report

    Args:
        ci (Parameters): The confidence intervals for the parameters.
        with_offset (bool, optional): Whether to include the offset in the report.
            Defaults to True.
        ndigits (int, optional): The number of digits to display in the report.
            Defaults to 5.
    """

    def __init__(
        self,
        ci: Dict[str, List[Tuple[float, float]]],
        with_offset: bool = True,
        ndigits: int = 5,
        best_tol: float = 1.0e-2,
    ):
        """Initialize the Report object.

        Args:
            ci (Dict[str, List[Tuple[float, float]]]): The confidence intervals for
                the parameters.
            with_offset (bool): Whether to include an offset in the report.
                Defaults to True.
            ndigits (int): The number of digits to round the report values to.
                Defaults to 5.
            best_tol (float): The tolerance for the best value.
                Defaults to 1.0e-2.
        """
        self.ci = ci
        self.with_offset = with_offset
        self.ndigits = ndigits
        self.best_tol = best_tol

        self.df = pd.DataFrame()

    def convp(self, x: Tuple[float, float], bound_type: str) -> str:
        """Convert the confidence interval to a string.

        Args:
            x (Tuple[float, float]): The confidence interval.
            bound_type (str): The type of the bound.

        Returns:
            str: The confidence interval as a string.
        """
        return (
            "BEST" if abs(x[0]) < self.best_tol else f"{x[0] * 100:.2f}% - {bound_type}"
        )

    def calculate_offset(self, row: List[Tuple[float, float]]) -> float:
        """Calculate the offset for a row.

        Args:
            row (List[Tuple[float, float]]): The row to calculate the offset for.

        Returns:
            float: The offset for the row.
        """
        offset = 0.0
        if self.with_offset:
            for cval, val in row:
                if abs(cval) < (self.best_tol or 0.0):
                    offset = val
        return offset

    def create_report_row(
        self, name: str, row: List[Tuple[float, float]], offset: float
    ) -> None:
        """Create a row for the report.

        Args:
            name (str): The name of the row.
            row (List[Tuple[float, float]]): The row to create the report for.
            offset (float): The offset for the row.
        """
        for i, (cval, val) in enumerate(row):
            sval = val if cval < self.best_tol else val - offset
            bound_type = "LOWER" if i < len(row) / 2 else "UPPER"
            self.report.setdefault(self.convp((cval, val), bound_type), {})[name] = sval

    def __call__(self) -> None:
        """Generate the Confidence report as a table."""
        self.report: Dict[str, Dict[str, float]] = {}
        for name, row in self.ci.items():
            offset = self.calculate_offset(row)
            self.create_report_row(name, row, offset)

        self.tabulate(df=pd.DataFrame(self.report))

    def tabulate(self, df: pd.DataFrame) -> None:
        """Print the Confidence report as a table."""
        PrintingResults.print_tabulate_df(df=df, floatfmt=f".{self.ndigits}f")


class FitReport:
    """Generate fit reports based on the result of the fitting process.

    Args:
        inpars (Parameters): The input parameters used for fitting.
        sort_pars (bool, optional): Whether to sort the parameters.
            Defaults to True.
        show_correl (bool, optional): Whether to show correlations of components.
            Defaults to True.
        min_correl (float, optional): The minimum correlation value to consider.
            Defaults to 0.0.
        modelpars (dict, optional): The model parameters. Defaults to None.

    Attributes:
        inpars (Parameters): The input parameters used for fitting.
        sort_pars (bool): Whether to sort the parameters.
        show_correl (bool): Whether to show correlations of components.
        min_correl (float): The minimum correlation value to consider.
        modelpars (dict): The model parameters.
        result (FitResult): The result of the fitting process.
        params (Parameters): The parameters used for fitting.
        parnames (list): The names of the parameters.

    Methods:
        generate_fit_statistics(): Generate fit statistics based on the result
            of the fitting process.
        generate_variables(): Generate a DataFrame containing information
            about the variables.
        generate_correlations(): Generate a correlation matrix for the
            varying parameters.
        generate_report(): Generate a report containing fit statistics,
            correlations, and variables.
        __call__(): Generate and print a report based on the data.
    """

    def __init__(
        self,
        inpars: Union[Parameters, Callable[..., Any]],
        sort_pars: Union[bool, Callable[[str], Any]] = True,
        show_correl: bool = True,
        min_correl: float = 0.0,
        modelpars: Optional[Callable[..., Any]] = None,
    ) -> None:
        """Initialize the Report object.

        Args:
            inpars (Parameters or object): The input parameters or
                object.
            sort_pars (Union[bool, Callable[[str], Any]], optional): Whether to sort the parameters.
                Defaults to True.
            show_correl (bool, optional): Whether to show correlations.
                Defaults to True.
            min_correl (float, optional): The minimum correlation value.
                Defaults to 0.0.
            modelpars (object, optional): The model parameters.
                Defaults to None.
        """
        self.inpars = inpars
        self.sort_pars = sort_pars
        self.show_correl = show_correl
        self.min_correl = min_correl
        self.modelpars = modelpars

        if isinstance(self.inpars, Parameters):
            self.result, self.params = None, self.inpars
        elif hasattr(self.inpars, "params"):
            self.result = self.inpars
            self.params = self.inpars.params

        self.parnames = self._get_parnames()

    def _get_parnames(self) -> List[str]:
        """Get parameter names, sorted if required.

        Returns:
            List[str]: List of parameter names.
        """
        if not self.sort_pars:
            return list(self.params.keys())
        key = self.sort_pars if callable(self.sort_pars) else alphanumeric_sort
        return sorted(self.params, key=key)

    def generate_fit_statistics(self) -> Optional[pd.DataFrame]:
        """Generate fit statistics based on the result of the fitting process.

        Returns:
            Optional[pd.DataFrame]: A pandas DataFrame containing the
            fit statistics, including:
                - fitting method
                - function evals
                - data points
                - variables
                - chi-square
                - reduced chi-square
                - Akaike info crit
                - Bayesian info crit
                - R-squared (if available)
        """
        if self.result is not None:
            return pd.DataFrame(
                {
                    "fitting method": [self.result.method],  # type: ignore
                    "function evals": [getfloat_attr(self.result, "nfev")],
                    "data points": [getfloat_attr(self.result, "ndata")],
                    "variables": [getfloat_attr(self.result, "nvarys")],
                    "chi-square": [getfloat_attr(self.result, "chisqr")],
                    "reduced chi-square": [getfloat_attr(self.result, "redchi")],
                    "Akaike info crit": [getfloat_attr(self.result, "aic")],
                    "Bayesian info crit": [getfloat_attr(self.result, "bic")],
                    "R-squared": [
                        (
                            getfloat_attr(self.result, "rsquared")
                            if hasattr(self.result, "rsquared")
                            else None
                        )
                    ],
                }
            )
        return None

    def generate_variables(self) -> pd.DataFrame:
        """Generate a pandas DataFrame containing information about the variables.

        Returns:
            pd.DataFrame: A DataFrame with the following columns:
                - name: The name of the variable
                - value: The current value of the variable
                - stderr absolute: The absolute standard error of the variable
                - stderr percent: The percentage standard error of the variable
                - expr: The expression defining the variable (if any)
                - init: The initial value of the variable
                - model_value: The value of the variable in the model (if applicable)
                - fixed: A boolean indicating whether the variable is fixed or not
        """
        variables = []
        namelen = max(len(n) for n in self.parnames)
        for name in self.parnames:
            par = self.params[name]
            space = " " * (namelen - len(name))
            nout = f"{name}:{space}"
            inval = None
            if par.init_value is not None:
                inval = par.init_value
            model_val = None
            if self.modelpars is not None and name in self.modelpars:  # type: ignore
                model_val = self.modelpars[name].value  # type: ignore
            try:
                sval = gformat(par.value)
            except (TypeError, ValueError):  # pragma: no cover
                sval = None
            serr = None
            spercent = None
            if par.stderr is not None:
                serr = gformat(par.stderr)
                try:
                    spercent = abs(par.stderr / par.value) * 100
                except ZeroDivisionError:  # pragma: no cover
                    spercent = None

            variable = {
                "name": nout,
                "value": sval,
                "stderr absolute": serr,
                "stderr percent": spercent,
                "expr": par.expr,
                "init": inval,
                "model_value": model_val,
                "fixed": par.vary,
            }

            variables.append(variable)
        return pd.DataFrame(variables)

    def generate_correlations(self) -> pd.DataFrame:
        """Generate a correlation matrix for the varying parameters.

        Returns:
            pd.DataFrame: The correlation matrix with the
                varying parameters as rows and columns.
        """
        correl_matrix = pd.DataFrame(index=self.parnames, columns=self.parnames)
        for i, name in enumerate(self.parnames):
            par = self.params[name]
            if not par.vary:
                continue
            if hasattr(par, "correl") and par.correl is not None:
                for name2 in self.parnames[i + 1 :]:
                    if (
                        name != name2
                        and name2 in par.correl
                        and abs(par.correl[name2]) > self.min_correl
                    ):
                        correl_matrix.loc[name, name2] = par.correl[name2]
                        correl_matrix.loc[name2, name] = par.correl[
                            name2
                        ]  # mirror the value
        correl_matrix.fillna(1, inplace=True)  # fill diagonal with 1s
        return correl_matrix

    def generate_report(self) -> Dict[str, pd.DataFrame]:
        """Generate a report.

        !!! info "About the Report"

            This report contains fit statistics, correlations of
            components (if enabled), and variables and values.

        Returns:
            report (Dict[str, pd.DataFrame]): A dictionary containing
                the generated report.
        """
        report = {
            "Fit Statistics": self.generate_fit_statistics(),
            "Variables and Values": self.generate_variables(),
        }
        if self.show_correl:
            report["Correlations of Components"] = self.generate_correlations()
        return report

    def __call__(self) -> None:
        """Generate and print a report based on the data.

        This method generates a report using the `generate_report` method and
            prints it to the console.
        The report is organized into sections, where each section is
            represented by a DataFrame.
        The report is printed using the `tabulate` function from the
            `tabulate` library.
        The table format is chosen based on the platform, using "fancy_grid"
            for non-Windows platforms and "grid" for Windows.
        The floating point numbers in the table are formatted with three
            decimal places.
        """
        report = self.generate_report()
        for section, df in report.items():
            print(f"\n{section}\n")
            PrintingResults.print_tabulate_df(df=df)


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
            minimizer (Minimizer): The lmfit `Minimizer`-class as a general
                minimizer for curve fitting and optimization.
        """
        self.args = args
        self.result = result
        self.minimizer = minimizer
        self.correlation = pd.DataFrame.from_dict(args["linear_correlation"])

    def __call__(self) -> None:
        """Print the results of the fitting process."""
        if self.args["verbose"] == 1:
            self.printing_regular_mode()
        elif self.args["verbose"] == 2:
            self.printing_verbose_mode()

    @staticmethod
    def print_tabulate(args: Dict[str, Any]) -> None:
        """Print the results of the fitting process.

        Args:
            args (Dict[str, Any]): The args to be printed as a dictionary.
        """
        PrintingResults.print_tabulate_df(
            df=pd.DataFrame(**args).T,
        )

    @staticmethod
    def print_tabulate_df(df: pd.DataFrame, floatfmt: str = ".3f") -> None:
        """Print the results of the fitting process.

        Args:
            df (pd.DataFrame): The DataFrame to be printed.
            floatfmt (str, optional): The format of the floating point numbers.
                Defaults to ".3f".
        """
        print(
            tabulate(
                df,
                headers="keys",
                tablefmt="fancy_grid" if sys.platform != "win32" else "grid",
                floatfmt=floatfmt,
            )
        )

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
        FitReport(self.result, modelpars=self.result.params, **self.args["report"])()

    def print_confidence_interval(self) -> None:
        """Print the confidence interval."""
        print("\nConfidence Interval:\n")
        if self.args["conf_interval"]:
            try:
                CIReport(self.args["confidence_interval"][0])()
            except (MinimizerException, ValueError, KeyError, TypeError) as exc:
                warn(
                    f"Error: {exc} -> No confidence interval could be calculated!",
                    stacklevel=2,
                )
                self.args["confidence_interval"] = {}

    def print_linear_correlation(self) -> None:
        """Print the linear correlation."""
        print("\nOverall Linear-Correlation:\n")
        self.print_tabulate(args=self.args["linear_correlation"])

    def print_regression_metrics(self) -> None:
        """Print the regression metrics."""
        print("\nRegression Metrics:\n")
        self.print_tabulate(args=self.args["regression_metrics"])

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

    def welcome(self) -> None:
        """Print the welcome message."""
        tprint("SpectraFit", font="3-d")

    def version(self) -> str:
        """Print current version of the SpectraFit."""
        return f"Currently used version is: {__version__}"

    def start(self) -> None:
        """Print the start of the fitting process."""
        print("\nStart of the fitting process:\n")

    def end(self) -> None:
        """Print the end of the fitting process."""
        print("\nEnd of the fitting process:\n")

    def thanks(self) -> None:
        """Print the end of the fitting process."""
        print("\nThanks for using SpectraFit!")

    def yes_no(self) -> None:
        """Print the end of the fitting process."""
        print("\nDo you want to continue? (y/n)")

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

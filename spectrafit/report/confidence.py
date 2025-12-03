"""Confidence interval and fit report classes.

This module contains the CIReport and FitReport classes for generating
confidence interval and fit reports.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import pandas as pd

from lmfit import Parameters
from lmfit.printfuncs import alphanumeric_sort
from lmfit.printfuncs import getfloat_attr
from lmfit.printfuncs import gformat

from spectrafit.report.printer import PrintingResults


if TYPE_CHECKING:
    from collections.abc import Callable


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
        ci: dict[str, list[tuple[float, float]]],
        with_offset: bool = True,
        ndigits: int = 5,
        best_tol: float = 1.0e-2,
    ) -> None:
        """Initialize the Report object.

        Args:
            ci (dict[str, List[Tuple[float, float]]]): The confidence intervals for
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

    def convp(self, x: tuple[float, float], bound_type: str) -> str:
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

    def calculate_offset(self, row: list[tuple[float, float]]) -> float:
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
        self,
        name: str,
        row: list[tuple[float, float]],
        offset: float,
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
        self.report: dict[str, dict[str, float]] = {}
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
        inpars: Parameters | Callable[..., Any],
        sort_pars: bool | Callable[[str], Any] = True,
        show_correl: bool = True,
        min_correl: float = 0.0,
        modelpars: Callable[..., Any] | None = None,
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

    def _get_parnames(self) -> list[str]:
        """Get parameter names, sorted if required.

        Returns:
            List[str]: List of parameter names.

        """
        if not self.sort_pars:
            return list(self.params.keys())
        key = self.sort_pars if callable(self.sort_pars) else alphanumeric_sort
        return sorted(self.params, key=key)

    def generate_fit_statistics(self) -> pd.DataFrame | None:
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
                    "fitting method": [self.result.method],
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
                        ),
                    ],
                },
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
        return correl_matrix.fillna(1)  # fill diagonal with 1s

    def generate_report(self) -> dict[str, pd.DataFrame]:
        """Generate a report.

        !!! info "About the Report"

            This report contains fit statistics, correlations of
            components (if enabled), and variables and values.

        Returns:
            report (dict[str, pd.DataFrame]): A dictionary containing
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
        for df in report.values():
            PrintingResults.print_tabulate_df(df=df)

"""Frozen confidence-report helpers for legacy report imports.

Canonical runtime report ownership now lives in
:mod:`spectrafit.reporting.service`. This module only preserves the historical
table-oriented compatibility classes used by legacy import paths.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from lmfit import Parameters
from lmfit.printfuncs import alphanumeric_sort
from lmfit.printfuncs import getfloat_attr
from lmfit.printfuncs import gformat
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.report._table import print_tabulate_df


if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping

    from spectrafit.models.results.fit_result import ConfidenceResults


class ConfidenceBound(BaseModel):
    """Typed confidence bound pair used by the legacy table adapter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    sigma: float
    value: float


class ConfidenceParameterBounds(BaseModel):
    """Typed confidence bound series for one parameter."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    bounds: list[ConfidenceBound]


class ConfidenceTableColumn(BaseModel):
    """One rendered column in the legacy confidence table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    label: str
    entries: dict[str, float] = Field(default_factory=dict)


class ConfidenceTableDocument(BaseModel):
    """Typed compatibility projection for the legacy confidence table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    columns: list[ConfidenceTableColumn] = Field(default_factory=list)

    def to_dataframe(self) -> pd.DataFrame:
        """Project the typed table document to the legacy DataFrame surface."""
        return pd.DataFrame({column.label: column.entries for column in self.columns})


class FitStatisticsRow(BaseModel):
    """Single-row fit-statistics projection for the legacy fit report."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    fitting_method: str
    function_evals: str
    data_points: str
    variables: str
    chi_square: str
    reduced_chi_square: str
    akaike_info_crit: str
    bayesian_info_crit: str
    r_squared: str | None = None

    def to_dataframe(self) -> pd.DataFrame:
        """Project the typed statistics row to the legacy DataFrame surface."""
        return pd.DataFrame(
            [
                {
                    "fitting method": self.fitting_method,
                    "function evals": self.function_evals,
                    "data points": self.data_points,
                    "variables": self.variables,
                    "chi-square": self.chi_square,
                    "reduced chi-square": self.reduced_chi_square,
                    "Akaike info crit": self.akaike_info_crit,
                    "Bayesian info crit": self.bayesian_info_crit,
                    "R-squared": self.r_squared,
                }
            ]
        )


class VariableDisplayRow(BaseModel):
    """Typed variable row used by the legacy fit report table."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    value: str | None = None
    stderr_absolute: str | None = None
    stderr_percent: float | None = None
    expr: str | None = None
    init: float | str | None = None
    model_value: float | None = None
    fixed: bool

    def to_legacy_mapping(self) -> dict[str, str | float | bool | None]:
        """Project the typed row to the legacy DataFrame dict shape."""
        return {
            "name": self.name,
            "value": self.value,
            "stderr absolute": self.stderr_absolute,
            "stderr percent": self.stderr_percent,
            "expr": self.expr,
            "init": self.init,
            "model_value": self.model_value,
            "fixed": self.fixed,
        }


class FitReportSection(BaseModel):
    """Typed titled section for the legacy fit report document."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    title: str
    frame: pd.DataFrame | None


class FitReportDocument(BaseModel):
    """Typed compatibility document for the legacy fit report output."""

    model_config = ConfigDict(extra="forbid", frozen=True, arbitrary_types_allowed=True)

    sections: list[FitReportSection] = Field(default_factory=list)

    def to_mapping(self) -> dict[str, pd.DataFrame]:
        """Project the typed fit report to the legacy mapping contract."""
        return {
            section.title: section.frame
            for section in self.sections
            if section.frame is not None
        }


class CIReport:
    """Render confidence intervals for the frozen report compatibility layer.

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
        ci: ConfidenceResults | Mapping[str, list[tuple[float, float]]],
        with_offset: bool = True,
        ndigits: int = 5,
        best_tol: float = 1.0e-2,
    ) -> None:
        """Initialize the Report object.

        Args:
            ci (dict[str, list[tuple[float, float]]]): The confidence intervals for
                the parameters.
            with_offset (bool): Whether to include an offset in the report.
                Defaults to True.
            ndigits (int): The number of digits to round the report values to.
                Defaults to 5.
            best_tol (float): The tolerance for the best value.
                Defaults to 1.0e-2.

        """
        self.ci = self._normalize_ci(ci)
        self.with_offset = with_offset
        self.ndigits = ndigits
        self.best_tol = best_tol

        self.df = pd.DataFrame()

    @staticmethod
    def _normalize_ci(
        ci: ConfidenceResults | Mapping[str, list[tuple[float, float]]],
    ) -> list[ConfidenceParameterBounds]:
        """Normalize confidence payloads to typed parameter-bound series."""
        if hasattr(ci, "report_results"):
            ci = ci.report_results()
        return [
            ConfidenceParameterBounds(
                name=name,
                bounds=[
                    ConfidenceBound(sigma=float(sigma), value=float(value))
                    for sigma, value in row
                ],
            )
            for name, row in ci.items()
        ]

    def convp(self, x: tuple[float, float], bound_type: str) -> str:
        """Convert the confidence interval to a string.

        Args:
            x (tuple[float, float]): The confidence interval.
            bound_type (str): The type of the bound.

        Returns:
            str: The confidence interval as a string.

        """
        return (
            "BEST" if abs(x[0]) < self.best_tol else f"{x[0] * 100:.2f}% - {bound_type}"
        )

    def calculate_offset(self, row: list[ConfidenceBound]) -> float:
        """Calculate the offset for a row.

        Args:
            row (list[tuple[float, float]]): The row to calculate the offset for.

        Returns:
            float: The offset for the row.

        """
        offset = 0.0
        if self.with_offset:
            for bound in row:
                if abs(bound.sigma) < (self.best_tol or 0.0):
                    offset = bound.value
        return offset

    def create_report_row(
        self,
        name: str,
        row: list[ConfidenceBound],
        offset: float,
    ) -> list[ConfidenceTableColumn]:
        """Create a row for the report.

        Args:
            name (str): The name of the row.
            row (list[tuple[float, float]]): The row to create the report for.
            offset (float): The offset for the row.

        """
        columns: list[ConfidenceTableColumn] = []
        for i, bound in enumerate(row):
            sval = bound.value if bound.sigma < self.best_tol else bound.value - offset
            bound_type = "LOWER" if i < len(row) / 2 else "UPPER"
            columns.append(
                ConfidenceTableColumn(
                    label=self.convp((bound.sigma, bound.value), bound_type),
                    entries={name: sval},
                )
            )
        return columns

    def __call__(self) -> None:
        """Generate the Confidence report as a table."""
        merged_columns: dict[str, dict[str, float]] = {}
        for parameter_bounds in self.ci:
            offset = self.calculate_offset(parameter_bounds.bounds)
            for column in self.create_report_row(
                parameter_bounds.name,
                parameter_bounds.bounds,
                offset,
            ):
                merged_columns.setdefault(column.label, {}).update(column.entries)

        document = ConfidenceTableDocument(
            columns=[
                ConfidenceTableColumn(label=label, entries=values)
                for label, values in merged_columns.items()
            ]
        )
        self.tabulate(df=document.to_dataframe())

    def tabulate(self, df: pd.DataFrame) -> None:
        """Print the Confidence report as a table."""
        print_tabulate_df(df=df, floatfmt=f".{self.ndigits}f")


class FitReport:
    """Render fit tables for the frozen report compatibility layer.

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
        inpars: Parameters | Callable[..., object],
        sort_pars: bool | Callable[[str], str | int] = True,
        show_correl: bool = True,
        min_correl: float = 0.0,
        modelpars: Parameters | None = None,
    ) -> None:
        """Initialize the Report object.

        Args:
            inpars (Parameters or object): The input parameters or
                object.
            sort_pars (bool | Callable[[str], str | int], optional): Whether to sort the parameters.
                Defaults to True.
            show_correl (bool, optional): Whether to show correlations.
                Defaults to True.
            min_correl (float, optional): The minimum correlation value.
                Defaults to 0.0.
            modelpars (Parameters, optional): The model parameters.
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
            list[str]: List of parameter names.

        """
        if not self.sort_pars:
            return list(self.params.keys())
        key = self.sort_pars if callable(self.sort_pars) else alphanumeric_sort
        return sorted(self.params, key=key)

    def generate_fit_statistics(self) -> pd.DataFrame | None:
        """Generate fit statistics based on the result of the fitting process.

        Returns:
            pd.DataFrame | None: A pandas DataFrame containing the
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
            return FitStatisticsRow(
                fitting_method=self.result.method,
                function_evals=getfloat_attr(self.result, "nfev"),
                data_points=getfloat_attr(self.result, "ndata"),
                variables=getfloat_attr(self.result, "nvarys"),
                chi_square=getfloat_attr(self.result, "chisqr"),
                reduced_chi_square=getfloat_attr(self.result, "redchi"),
                akaike_info_crit=getfloat_attr(self.result, "aic"),
                bayesian_info_crit=getfloat_attr(self.result, "bic"),
                r_squared=(
                    getfloat_attr(self.result, "rsquared")
                    if hasattr(self.result, "rsquared")
                    else None
                ),
            ).to_dataframe()
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
        variables: list[VariableDisplayRow] = []
        namelen = max(len(n) for n in self.parnames)
        for name in self.parnames:
            par = self.params[name]
            space = " " * (namelen - len(name))
            nout = f"{name}:{space}"
            inval = None
            if par.init_value is not None:
                inval = par.init_value
            model_val = None
            if self.modelpars is not None and name in self.modelpars:
                model_val = self.modelpars[name].value
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

            variables.append(
                VariableDisplayRow(
                    name=nout,
                    value=sval,
                    stderr_absolute=serr,
                    stderr_percent=spercent,
                    expr=par.expr,
                    init=inval,
                    model_value=model_val,
                    fixed=par.vary,
                )
            )
        return pd.DataFrame([variable.to_legacy_mapping() for variable in variables])

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
        sections = [
            FitReportSection(
                title="Fit Statistics",
                frame=self.generate_fit_statistics(),
            ),
            FitReportSection(
                title="Variables and Values",
                frame=self.generate_variables(),
            ),
        ]
        if self.show_correl:
            sections.append(
                FitReportSection(
                    title="Correlations of Components",
                    frame=self.generate_correlations(),
                )
            )
        return FitReportDocument(sections=sections).to_mapping()

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
            print_tabulate_df(df=df)


__all__ = ["CIReport", "FitReport"]

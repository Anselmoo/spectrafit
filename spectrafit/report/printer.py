"""Printing utilities for fit results.

This module contains the PrintingResults and PrintingStatus classes for
printing fit results and status messages.
"""

from __future__ import annotations

import pprint

from typing import TYPE_CHECKING
from typing import Any
from warnings import warn

import pandas as pd

from art import tprint
from lmfit.minimizer import MinimizerException

from spectrafit import __version__


if TYPE_CHECKING:
    from lmfit import Minimizer


# Constants for verbosity levels
VERBOSE_REGULAR = 1  # Regular output mode
VERBOSE_DETAILED = 2  # Detailed/verbose output mode

CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"
pp = pprint.PrettyPrinter(indent=4)


class PrintingResults:
    """Print the results of the fitting process."""

    def __init__(
        self,
        args: dict[str, Any],
        result: Any,
        minimizer: Minimizer,
    ) -> None:
        """Initialize the PrintingResults class.

        Args:
            args (dict[str,Any]): The input file arguments as a dictionary with
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
        if self.args["verbose"] == VERBOSE_REGULAR:
            self.printing_regular_mode()
        elif self.args["verbose"] == VERBOSE_DETAILED:
            self.printing_verbose_mode()

    @staticmethod
    def print_tabulate(args: dict[str, Any]) -> None:
        """Print the results of the fitting process.

        Args:
            args (dict[str, Any]): The args to be printed as a dictionary.

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

        Note:
            This method is intentionally a no-op placeholder. The actual printing
            functionality was not implemented in the original codebase.
        """
        # Intentionally empty - matches original implementation

    def printing_regular_mode(self) -> None:
        """Print the fitting results in the regular mode."""
        self.print_statistic()
        self.print_fit_results()
        self.print_confidence_interval()
        self.print_linear_correlation()
        self.print_regression_metrics()

    def print_statistic(self) -> None:
        """Print the statistic."""
        self.print_tabulate(args=self.args["data_statistic"])

    def print_fit_results(self) -> None:
        """Print the fit results."""
        # Import here to avoid circular import
        from spectrafit.report.confidence import FitReport  # noqa: PLC0415

        FitReport(self.result, modelpars=self.result.params, **self.args["report"])()

    def print_confidence_interval(self) -> None:
        """Print the confidence interval."""
        if self.args["conf_interval"]:
            try:
                # Import here to avoid circular import
                from spectrafit.report.confidence import CIReport  # noqa: PLC0415

                CIReport(self.args["confidence_interval"][0])()
            except (MinimizerException, ValueError, KeyError, TypeError) as exc:
                warn(
                    f"Error: {exc} -> No confidence interval could be calculated!",
                    stacklevel=2,
                )
                self.args["confidence_interval"] = {}

    def print_linear_correlation(self) -> None:
        """Print the linear correlation."""
        self.print_tabulate(args=self.args["linear_correlation"])

    def print_regression_metrics(self) -> None:
        """Print the regression metrics."""
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
        pp.pprint(self.args["data_statistic"])

    def print_input_parameters_verbose(self) -> None:
        """Print input parameters in verbose mode."""
        pp.pprint(self.args)

    def print_fit_results_verbose(self) -> None:
        """Print fit results in verbose mode."""
        pp.pprint(self.args["fit_insights"])

    def print_confidence_interval_verbose(self) -> None:
        """Print confidence interval in verbose mode."""
        if self.args["conf_interval"]:
            pp.pprint(self.args["confidence_interval"])

    def print_linear_correlation_verbose(self) -> None:
        """Print overall linear-correlation in verbose mode."""
        pp.pprint(self.args["linear_correlation"])

    def print_regression_metrics_verbose(self) -> None:
        """Print regression metrics in verbose mode."""
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

    def end(self) -> None:
        """Print the end of the fitting process."""

    def thanks(self) -> None:
        """Print the end of the fitting process."""

    def yes_no(self) -> None:
        """Print the end of the fitting process."""

    def credits(self) -> None:
        """Print the credits of the fitting process."""
        tprint("\nCredits:\n", font="3-d")

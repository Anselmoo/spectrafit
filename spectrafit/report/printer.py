"""Printing utilities for fit results.

This module contains the PrintingResults and PrintingStatus classes for
printing fit results and status messages.
"""

from __future__ import annotations

import pprint

from typing import TYPE_CHECKING
from typing import cast
from warnings import warn

import pandas as pd

from art import tprint
from lmfit.minimizer import MinimizerException

from spectrafit import __version__


if TYPE_CHECKING:
    from lmfit import Minimizer
    from lmfit.minimizer import MinimizerResult

    from spectrafit.core.postprocessing import PostProcessingResult


# Constants for verbosity levels
VERBOSE_REGULAR = 1  # Regular output mode
VERBOSE_DETAILED = 2  # Detailed/verbose output mode

CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"
pp = pprint.PrettyPrinter(indent=4)


class PrintingResults:
    """Print the results of the fitting process."""

    def __init__(
        self,
        post: PostProcessingResult,
        result: MinimizerResult,
        minimizer: Minimizer,
        *,
        data_statistic: dict[str, object] | None = None,  # intentional: frozen
        conf_interval: dict[str, object] | bool = False,  # intentional: frozen
        verbose: int = 0,
    ) -> None:
        """Initialize the PrintingResults class.

        Args:
            post: Typed post-processing output.
            result: The lmfit minimizer result.
            minimizer: The lmfit ``Minimizer``-class.
            data_statistic: Optional preprocessing statistics.
            conf_interval: Confidence interval settings.
            verbose: Verbosity level (0=silent, 1=regular, 2=detailed).

        """
        self.post = post
        self.result = result
        self.minimizer = minimizer
        self.data_statistic = data_statistic or {}
        self.conf_interval = conf_interval
        self.verbose = verbose
        self.correlation = pd.DataFrame.from_dict(self.post.linear_correlation)

    def __call__(self) -> None:
        """Print the results of the fitting process."""
        if self.verbose == VERBOSE_REGULAR:
            self.printing_regular_mode()
        elif self.verbose == VERBOSE_DETAILED:
            self.printing_verbose_mode()

    @staticmethod
    def print_tabulate(args: dict[str, object]) -> None:  # intentional: frozen
        """Print the results of the fitting process.

        Args:
            args: The args to be printed as a split-orient dict.

        """
        PrintingResults.print_tabulate_df(
            df=pd.DataFrame(**args).T,  # intentional: frozen Layer 4
        )

    @staticmethod
    def print_tabulate_df(df: pd.DataFrame, floatfmt: str = ".3f") -> None:
        """Print the results of the fitting process.

        Args:
            df: The DataFrame to be printed.
            floatfmt: The format of the floating point numbers.

        Note:
            This method is intentionally a no-op placeholder.
        """

    def printing_regular_mode(self) -> None:
        """Print the fitting results in the regular mode."""
        self.print_statistic()
        self.print_fit_results()
        self.print_confidence_interval()
        self.print_linear_correlation()
        self.print_regression_metrics()

    def print_statistic(self) -> None:
        """Print the statistic."""
        self.print_tabulate(args=self.data_statistic)  # type: ignore[arg-type]

    def print_fit_results(self) -> None:
        """Print the fit results."""
        from spectrafit.report.confidence import FitReport  # noqa: PLC0415

        FitReport(self.result, modelpars=self.result.params)()

    def print_confidence_interval(self) -> None:
        """Print the confidence interval."""
        if self.conf_interval:
            try:
                from spectrafit.report.confidence import CIReport  # noqa: PLC0415

                ci_data = cast(
                    "tuple[dict[str, list[tuple[float, float]]], dict[str, object]]",  # intentional
                    self.post.confidence_interval,
                )
                CIReport(ci_data[0])()
            except (MinimizerException, ValueError, KeyError, TypeError) as exc:
                warn(
                    f"Error: {exc} -> No confidence interval could be calculated!",
                    stacklevel=2,
                )

    def print_linear_correlation(self) -> None:
        """Print the linear correlation."""
        self.print_tabulate(args=self.post.linear_correlation)  # type: ignore[arg-type]

    def print_regression_metrics(self) -> None:
        """Print the regression metrics."""
        self.print_tabulate(args=self.post.regression_metrics)  # type: ignore[arg-type]

    def printing_verbose_mode(self) -> None:
        """Print all results in verbose mode."""
        self.print_statistic_verbose()
        self.print_fit_results_verbose()
        self.print_confidence_interval_verbose()
        self.print_linear_correlation_verbose()
        self.print_regression_metrics_verbose()

    def print_statistic_verbose(self) -> None:
        """Print the data statistic in verbose mode."""
        pp.pprint(self.data_statistic)

    def print_fit_results_verbose(self) -> None:
        """Print fit results in verbose mode."""
        pp.pprint(self.post.fit_insights)

    def print_confidence_interval_verbose(self) -> None:
        """Print confidence interval in verbose mode."""
        if self.conf_interval:
            pp.pprint(self.post.confidence_interval)

    def print_linear_correlation_verbose(self) -> None:
        """Print overall linear-correlation in verbose mode."""
        pp.pprint(self.post.linear_correlation)

    def print_regression_metrics_verbose(self) -> None:
        """Print regression metrics in verbose mode."""
        pp.pprint(self.post.regression_metrics)


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

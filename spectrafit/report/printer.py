"""Frozen console printers retained for historical report imports.

Canonical runtime reporting belongs to :mod:`spectrafit.reporting.service`.
This module keeps the old printer entry points importable as compatibility
adapters that bridge legacy inputs into the canonical typed report service.
"""

from __future__ import annotations

import json
import sys

from collections.abc import Mapping
from functools import cached_property
from typing import TYPE_CHECKING

import pandas as pd

from art import tprint
from pydantic import BaseModel

from spectrafit import __version__
from spectrafit.core.result_bridge import build_fit_result_from_runtime
from spectrafit.models.column_names import ColumnNames
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.split_frame import SplitFrame
from spectrafit.report._table import print_tabulate_df
from spectrafit.reporting.service import VERBOSE_DETAILED
from spectrafit.reporting.service import _render_confidence_section
from spectrafit.reporting.service import _render_split_frame_section
from spectrafit.reporting.service import emit_runtime_report
from spectrafit.reporting.service import render_text_report


if TYPE_CHECKING:
    from lmfit import Minimizer
    from lmfit.minimizer import MinimizerResult

    from spectrafit.core.postprocessing import PostProcessingResult
    from spectrafit.models.results.fit_result import FitResult


# Constants for verbosity levels
VERBOSE_REGULAR = 1  # Regular output mode retained for legacy callers

CORREL_HEAD = "[[Correlations]] (unreported correlations are < %.3f)"
_COLS = ColumnNames()


class PrintingResults:
    """Print fit output for the frozen report compatibility layer."""

    def __init__(
        self,
        post: PostProcessingResult,
        result: MinimizerResult,
        minimizer: Minimizer,
        *,
        data_statistic: Mapping[str, object] | SplitFrame | None = None,
        conf_interval: Mapping[str, object] | bool = False,  # intentional: frozen
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
        self.data_statistic = data_statistic
        self.conf_interval = conf_interval
        self.verbose = verbose

    def __call__(self) -> None:
        """Print the results of the fitting process."""
        if self.verbose >= VERBOSE_DETAILED:
            self.printing_verbose_mode()
        elif self.verbose >= VERBOSE_REGULAR:
            self.printing_regular_mode()

    @staticmethod
    def print_tabulate(args: Mapping[str, object] | SplitFrame) -> None:
        """Print the results of the fitting process.

        Args:
            args: The args to be printed as a split-orient dict.

        """
        print_tabulate_df(
            df=(
                args.to_dataframe().T
                if isinstance(args, SplitFrame)
                else SplitFrame.model_validate(args).to_dataframe().T
            ),
        )

    @staticmethod
    def print_tabulate_df(df: pd.DataFrame, floatfmt: str = ".3f") -> None:
        """Delegate table rendering through the shared compatibility hook.

        Args:
            df: The DataFrame to be printed.
            floatfmt: The format of the floating point numbers.

        """
        print_tabulate_df(df=df, floatfmt=floatfmt)

    @cached_property
    def fit_result(self) -> FitResult:
        """Build the canonical fit result projection for legacy print calls."""
        return build_fit_result_from_runtime(
            global_mode=self._infer_global_mode(),
            minimizer_result=self.result,
            post_result=self.post,
        )

    @cached_property
    def data_statistic_frame(self) -> SplitFrame:
        """Normalize legacy preprocessing statistics to the canonical frame model."""
        if isinstance(self.data_statistic, SplitFrame):
            return self.data_statistic
        if self.data_statistic is None:
            return SplitFrame.empty()
        if isinstance(self.data_statistic, Mapping):
            return SplitFrame.model_validate(self.data_statistic)
        msg = "PrintingResults.data_statistic must be a split-frame dict or SplitFrame."
        raise TypeError(msg)

    def _infer_global_mode(self) -> FittingMode:
        """Infer the fitting mode from post-processing output columns."""
        fit_columns = list(self.post.fit_result_data.columns)
        if any(str(column).startswith(f"{_COLS.intensity}_") for column in fit_columns):
            return FittingMode.GLOBAL
        return FittingMode.STANDARD

    @staticmethod
    def _write_block(text: str) -> None:
        """Write a non-empty report block to stdout."""
        if text:
            sys.stdout.write(f"{text}\n")

    @staticmethod
    def _write_json_block(payload: BaseModel | Mapping[str, object]) -> None:
        """Write a structured compatibility payload to stdout."""
        if isinstance(payload, BaseModel):
            sys.stdout.write(f"{payload.model_dump_json(indent=2)}\n")
            return
        sys.stdout.write(f"{json.dumps(dict(payload), indent=2)}\n")

    def printing_regular_mode(self) -> None:
        """Print the canonical runtime report in regular mode."""
        emit_runtime_report(
            fit_result=self.fit_result,
            data_statistic=self.data_statistic_frame,
            verbose=VERBOSE_REGULAR,
        )

    def print_statistic(self) -> None:
        """Print the preprocessing statistics block."""
        self._write_block(
            _render_split_frame_section(
                "Preprocessing statistics",
                self.data_statistic_frame,
            )
        )

    def print_fit_results(self) -> None:
        """Print the canonical fit summary/variables/statistics block."""
        self._write_block(
            render_text_report(
                self.fit_result,
                ["summary", "variables", "statistics", "correlation"],
            )
        )

    def print_confidence_interval(self) -> None:
        """Print the canonical confidence-interval section."""
        if self.conf_interval:
            self._write_block(_render_confidence_section(self.fit_result))

    def print_linear_correlation(self) -> None:
        """Print the linear-correlation section."""
        self._write_block(
            _render_split_frame_section(
                "Linear correlation",
                self.fit_result.data_summary.linear_correlation,
            )
        )

    def print_regression_metrics(self) -> None:
        """Print the regression-metrics section."""
        self._write_block(
            _render_split_frame_section(
                "Regression metrics",
                self.fit_result.data_summary.regression_metrics,
            )
        )

    def printing_verbose_mode(self) -> None:
        """Print the canonical runtime report in detailed mode."""
        emit_runtime_report(
            fit_result=self.fit_result,
            data_statistic=self.data_statistic_frame,
            verbose=VERBOSE_DETAILED,
        )

    def print_statistic_verbose(self) -> None:
        """Print preprocessing statistics as structured JSON."""
        self._write_json_block(
            {"preprocessing": self.data_statistic_frame.model_dump(mode="json")}
        )

    def print_fit_results_verbose(self) -> None:
        """Print fit insights as structured JSON."""
        self._write_json_block(
            {"fit_insights": self.fit_result.fit_insights.model_dump(mode="json")}
        )

    def print_confidence_interval_verbose(self) -> None:
        """Print confidence intervals as structured JSON."""
        if self.conf_interval:
            self._write_json_block(
                {"confidence": self.fit_result.confidence.model_dump(mode="json")}
            )

    def print_linear_correlation_verbose(self) -> None:
        """Print linear correlation as structured JSON."""
        self._write_json_block(
            {
                "linear_correlation": self.fit_result.data_summary.linear_correlation.model_dump(
                    mode="json"
                )
            }
        )

    def print_regression_metrics_verbose(self) -> None:
        """Print regression metrics as structured JSON."""
        self._write_json_block(
            {
                "regression_metrics": self.fit_result.data_summary.regression_metrics.model_dump(
                    mode="json"
                )
            }
        )


class PrintingStatus:
    """Print historical CLI status banners for legacy import paths."""

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


__all__ = [
    "CORREL_HEAD",
    "VERBOSE_DETAILED",
    "VERBOSE_REGULAR",
    "PrintingResults",
    "PrintingStatus",
]

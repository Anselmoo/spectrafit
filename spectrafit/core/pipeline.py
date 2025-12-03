"""Fitting pipeline for SpectraFit.

This module implements the pipeline pattern for the fitting workflow,
separating concerns and making the code more maintainable.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import pandas as pd

from spectrafit.core.data_loader import load_data
from spectrafit.core.postprocessing import PostProcessing
from spectrafit.core.preprocessing import PreProcessing
from spectrafit.models.builtin import SolverModels
from spectrafit.report import PrintingResults


if TYPE_CHECKING:
    from lmfit import Minimizer
    from lmfit.minimizer import MinimizerResult


class FittingResult:
    """Container for fitting results.

    Attributes:
        df (pd.DataFrame): DataFrame containing the results.
        args (dict[str, Any]): Arguments dictionary with fit information.
        minimizer (Minimizer): The minimizer used for fitting.
        result (MinimizerResult): The minimization result.

    """

    def __init__(
        self,
        df: pd.DataFrame,
        args: dict[str, Any],
        minimizer: Minimizer,
        result: MinimizerResult,
    ) -> None:
        """Initialize FittingResult.

        Args:
            df (pd.DataFrame): DataFrame containing the results.
            args (dict[str, Any]): Arguments dictionary with fit information.
            minimizer (Minimizer): The minimizer used for fitting.
            result (MinimizerResult): The minimization result.

        """
        self.df = df
        self.args = args
        self.minimizer = minimizer
        self.result = result


class FittingPipeline:
    """Pipeline for fitting workflow.

    This class orchestrates the fitting workflow by coordinating
    data loading, preprocessing, solving, and postprocessing steps.

    Attributes:
        config (dict[str, Any]): Configuration dictionary for the pipeline.

    """

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize FittingPipeline.

        Args:
            config (dict[str, Any]): Configuration dictionary containing
                 all necessary parameters for the fitting workflow.

        """
        self.config = config

    def run(self) -> FittingResult:
        """Run the complete fitting pipeline.

        This method executes the following steps:
        1. Load data
        2. Preprocess data
        3. Solve/fit the model
        4. Postprocess results

        Returns:
            FittingResult: Container with DataFrame, args, minimizer, and result.

        """
        # Step 1: Load data
        df = self._load_data()

        # Step 2: Preprocess
        df, args = self._preprocess(df)

        # Step 3: Solve
        minimizer, result = self._solve(df, args)

        # Step 4: Postprocess
        df, args = self._postprocess(df, args, minimizer, result)

        return FittingResult(df, args, minimizer, result)

    def _load_data(self) -> pd.DataFrame:
        """Load data from input file.

        Returns:
            pd.DataFrame: Loaded data.

        """
        return load_data(self.config)

    def _preprocess(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Preprocess the data.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            tuple[pd.DataFrame, dict[str, Any]]: Preprocessed DataFrame and
                 updated configuration.

        """
        preprocessor = PreProcessing(df=df, args=self.config)
        return preprocessor()

    def _solve(
        self,
        df: pd.DataFrame,
        args: dict[str, Any],
    ) -> tuple[Minimizer, MinimizerResult]:
        """Solve the fitting problem.

        Args:
            df (pd.DataFrame): Preprocessed DataFrame.
            args (dict[str, Any]): Configuration with preprocessing results.

        Returns:
            tuple[Minimizer, MinimizerResult]: Minimizer and fitting result.

        """
        solver = SolverModels(df=df, args=args)
        return solver()

    def _postprocess(
        self,
        df: pd.DataFrame,
        args: dict[str, Any],
        minimizer: Minimizer,
        result: MinimizerResult,
    ) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Postprocess the fitting results.

        Args:
            df (pd.DataFrame): DataFrame with fit data.
            args (dict[str, Any]): Configuration dictionary.
            minimizer (Minimizer): The minimizer used.
            result (MinimizerResult): The fitting result.

        Returns:
            tuple[pd.DataFrame, dict[str, Any]]: Postprocessed DataFrame and
                 updated configuration.

        """
        postprocessor = PostProcessing(
            df=df,
            args=args,
            minimizer=minimizer,
            result=result,
        )
        return postprocessor()


def fitting_routine_pipeline(
    args: dict[str, Any],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the fitting algorithm using the pipeline pattern.

    This is a convenience function that creates and runs a FittingPipeline.

    Args:
        args (dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.

    Returns:
        tuple[pd.DataFrame, dict[str, Any]]: Returns a DataFrame and a dictionary,
             which is containing the input data (`x` and `data`), as well as the best
             fit, single contributions of each peak and the corresponding residuum. The
             dictionary contains the raw input data, the best fit, the single
             contributions and the corresponding residuum. Furthermore, the dictionary
             is extended by advanced statistical information of the fit.

    """
    pipeline = FittingPipeline(config=args)
    result = pipeline.run()

    # Print results
    PrintingResults(
        args=result.args,
        minimizer=result.minimizer,
        result=result.result,
    )()

    return result.df, result.args

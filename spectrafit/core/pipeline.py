"""Fitting pipeline for SpectraFit.

This module implements the pipeline pattern for the fitting workflow,
separating concerns and making the code more maintainable.
"""

from __future__ import annotations

import pandas as pd

from lmfit import Minimizer
from lmfit.minimizer import MinimizerResult
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.core.data_loader import load_data
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.postprocessing import PostProcessing
from spectrafit.core.preprocessing import PreProcessing
from spectrafit.models.builtin import SolverModels
from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.data_config import DataConfig
from spectrafit.models.output_config import OutputConfig
from spectrafit.report import PrintingResults


class FitStatistics(BaseModel):
    """Serializable fit statistics from a minimization result.

    Attributes:
        chi_squared: Chi-squared statistic of the fit.
        reduced_chi_squared: Reduced chi-squared statistic.
        num_variables: Number of free variables in the fit.
        success: Whether the fit converged successfully.
        message: Status message from the minimizer.
        nfev: Number of function evaluations.
        ndata: Number of data points.
        nfree: Degrees of freedom (ndata - nvarys).

    """

    chi_squared: float = Field(description="Chi-squared statistic")
    reduced_chi_squared: float = Field(description="Reduced chi-squared statistic")
    num_variables: int = Field(description="Number of free variables")
    success: bool = Field(description="Whether fit converged")
    message: str = Field(description="Minimizer status message")
    nfev: int = Field(description="Number of function evaluations")
    ndata: int = Field(description="Number of data points")
    nfree: int = Field(description="Degrees of freedom")


class FittingResult(BaseModel):
    """Container for fitting results.

    Attributes:
        df: DataFrame containing the results.
        args: Arguments dictionary with fit information.
        minimizer: The minimizer used for fitting.
        result: The minimization result.

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame
    args: dict[str, object]
    minimizer: Minimizer
    result: MinimizerResult

    @property
    def chi_squared(self) -> float:
        """Return the chi-squared statistic from the fit result."""
        return float(self.result.chisqr)

    @property
    def reduced_chi_squared(self) -> float:
        """Return the reduced chi-squared statistic from the fit result."""
        return float(self.result.redchi)

    @property
    def num_variables(self) -> int:
        """Return the number of variables in the fit."""
        return int(self.result.nvarys)

    @property
    def success(self) -> bool:
        """Return whether the fit was successful."""
        return bool(self.result.success)

    def to_json(self) -> FitStatistics:
        """Export serializable fit metadata.

        Returns:
            FitStatistics: Pydantic model containing serializable fit
                statistics and metadata. Call ``.model_dump()`` to get a
                plain dictionary representation.

        """
        return FitStatistics(
            chi_squared=self.chi_squared,
            reduced_chi_squared=self.reduced_chi_squared,
            num_variables=self.num_variables,
            success=self.success,
            message=self.result.message,
            nfev=self.result.nfev,
            ndata=self.result.ndata,
            nfree=self.result.nfree,
        )


class FittingPipeline:
    """Pipeline for fitting workflow.

    This class orchestrates the fitting workflow by coordinating
    data loading, preprocessing, solving, and postprocessing steps.

    Attributes:
        config (UnifiedFittingConfig): Validated configuration for the pipeline.
        output (OutputConfig): Runtime output configuration (outfile, noplot, verbose).

    """

    def __init__(
        self,
        config: UnifiedFittingConfig,
        output: OutputConfig | None = None,
    ) -> None:
        """Initialize FittingPipeline.

        Args:
            config: Validated :class:`UnifiedFittingConfig` for the fitting run.
            output: Optional :class:`OutputConfig` controlling result export and
                display.  Defaults to ``OutputConfig()`` (standard output,
                plots enabled, table verbosity).

        """
        self.config: UnifiedFittingConfig = config
        self.output: OutputConfig = output or OutputConfig()

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
        minimizer, result, bundle = self._solve(df)

        # Step 4: Postprocess
        df, args = self._postprocess(df, args, minimizer, result, bundle)

        return FittingResult(df=df, args=args, minimizer=minimizer, result=result)

    def _load_data(self) -> pd.DataFrame:
        """Load data from input file.

        Returns:
            pd.DataFrame: Loaded data.

        """
        return load_data(DataConfig.from_unified(self.config))

    def _preprocess(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
        """Preprocess the data.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            tuple[pd.DataFrame, dict[str, object]]: Preprocessed DataFrame and
                 ``data_statistic`` result dict.

        """
        preprocessor = PreProcessing(df=df, config=self.config)
        return preprocessor()

    def _solve(
        self,
        df: pd.DataFrame,
    ) -> tuple[Minimizer, MinimizerResult, CompositeModelBundle | None]:
        """Solve the fitting problem.

        Args:
            df (pd.DataFrame): Preprocessed DataFrame.

        Returns:
            tuple[Minimizer, MinimizerResult, CompositeModelBundle | None]:
                Minimizer, fitting result, and the composite bundle (None for global fits).

        """
        solver = SolverModels(df=df, config=self.config)
        minimizer, result = solver()
        bundle: CompositeModelBundle | None = solver.bundle
        return minimizer, result, bundle

    def _postprocess(
        self,
        df: pd.DataFrame,
        args: dict[str, object],
        minimizer: Minimizer,
        result: MinimizerResult,
        bundle: CompositeModelBundle | None = None,
    ) -> tuple[pd.DataFrame, dict[str, object]]:
        """Postprocess the fitting results.

        Args:
            df (pd.DataFrame): DataFrame with fit data.
            args (dict[str, object]): Configuration dictionary from preprocessing.
            minimizer (Minimizer): The minimizer used.
            result (MinimizerResult): The fitting result.
            bundle: Optional CompositeModelBundle for local-fit decomposition.

        Returns:
            tuple[pd.DataFrame, dict[str, object]]: Postprocessed DataFrame and
                 updated configuration.

        """
        # Merge config fields into args so PostProcessing (frozen Layer 4) gets
        # both preprocessing results and the typed config values.
        # OutputConfig provides outfile/noplot/verbose for the export chain.
        extra_fields: dict[str, object] = self.config.model_extra or {}
        post_args: dict[str, object] = {
            **args,
            **extra_fields,
            **self.output.model_dump(),
            "global_": int(self.config.global_),
            "conf_interval": self.config.conf_interval,
            "peaks": self.config.peaks,
            "column": [self.config.column.x, self.config.column.y],
            "_bundle": bundle,
            # FitReport kwargs (sort_pars, show_correl, min_correl) — empty = use defaults.
            # printer.py (frozen) expects this key.
            "report": {},
        }
        postprocessor = PostProcessing(
            df=df,
            args=post_args,
            minimizer=minimizer,
            result=result,
        )
        return postprocessor()


def fitting_routine_pipeline(
    args: UnifiedFittingConfig,
    output: OutputConfig | None = None,
) -> tuple[pd.DataFrame, dict[str, object]]:
    """Run the fitting algorithm using the pipeline pattern.

    This is a convenience function that creates and runs a FittingPipeline.

    Args:
        args: Validated :class:`UnifiedFittingConfig` for the fitting run.
        output: Optional :class:`OutputConfig` controlling result export and
            display.  Defaults to ``OutputConfig()`` (standard output).

    Returns:
        tuple[pd.DataFrame, dict[str, object]]: Returns a DataFrame and a dictionary,
             which is containing the input data (`x` and `data`), as well as the best
             fit, single contributions of each peak and the corresponding residuum. The
             dictionary contains the raw input data, the best fit, the single
             contributions and the corresponding residuum. Furthermore, the dictionary
             is extended by advanced statistical information of the fit.

    """
    pipeline = FittingPipeline(config=args, output=output)
    result = pipeline.run()

    # Print results
    PrintingResults(
        args=result.args,
        minimizer=result.minimizer,
        result=result.result,
    )()

    return result.df, result.args

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
from spectrafit.core.postprocessing import PostProcessingResult
from spectrafit.core.preprocessing import preprocess
from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.data_config import DataConfig
from spectrafit.models.functions.builtin import SolverModels
from spectrafit.models.output_config import OutputConfig
from spectrafit.models.preprocess_result import PreprocessResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.types import DataSplitDict
from spectrafit.report import PrintingResults


type _CIResult = bool | dict[str, object]  # intentional: serialization boundary


def _resolve_conf_interval(ci: bool | ConfIntervalConfig) -> _CIResult:
    """Convert ``ConfIntervalConfig`` to the ``dict`` form expected by frozen modules.

    Args:
        ci: Confidence-interval configuration from `UnifiedFittingConfig`.

    Returns:
        ``False`` to disable CI, or a kwargs dict for ``lmfit.conf_interval``.
    """
    if isinstance(ci, ConfIntervalConfig):
        return ci.model_dump(exclude_none=True)
    return ci


def _coerce_data_statistic(raw: object) -> DataSplitDict:
    """Normalize preprocessing statistics to ``DataSplitDict``.

    Args:
        raw: Raw ``data_statistic`` payload from frozen preprocessing code.

    Returns:
        DataSplitDict: Normalized split-orient payload.
    """
    empty = DataSplitDict(data=[], index=[], columns=[])
    if not isinstance(raw, dict):
        return empty
    if {"data", "index", "columns"} - set(raw):
        return empty
    return DataSplitDict(
        data=list(raw.get("data", [])),
        index=list(raw.get("index", [])),
        columns=list(raw.get("columns", [])),
    )


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

    All pipeline consumers read typed fields — no ``args: dict`` access.

    Attributes:
        df: Enriched DataFrame (residuals, fits, contributions).
        post: Typed post-processing result.
        config: The validated configuration that produced this result.
        output: Runtime output configuration (outfile, noplot, verbose).
        data_statistic: Preprocessing statistics (from ``PreProcessing``).
        minimizer: The lmfit minimizer used for fitting.
        result: The lmfit minimization result.

    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    df: pd.DataFrame
    post: PostProcessingResult
    config: UnifiedFittingConfig
    output: OutputConfig = Field(default_factory=OutputConfig)
    data_statistic: DataSplitDict = Field(
        default_factory=lambda: DataSplitDict(data=[], index=[], columns=[])
    )
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
            FittingResult: Typed container with DataFrame, config,
                post-processing result, minimizer, and result.

        """
        # Step 1: Load data
        df = self._load_data()

        # Step 2: Preprocess
        pre_result = self._preprocess(df)
        df = pre_result.df
        data_statistic = pre_result.data_statistic

        # Step 3: Solve
        minimizer, result, bundle = self._solve(df)

        # Step 4: Postprocess (typed)
        post_result = self._postprocess(df, minimizer, result, bundle)

        return FittingResult(
            df=post_result.df,
            post=post_result,
            config=self.config,
            output=self.output,
            data_statistic=data_statistic,
            minimizer=minimizer,
            result=result,
        )

    def _load_data(self) -> pd.DataFrame:
        """Load data from input file.

        Returns:
            pd.DataFrame: Loaded data.

        """
        return load_data(DataConfig.from_unified(self.config))

    def _preprocess(self, df: pd.DataFrame) -> PreprocessResult:
        """Preprocess the data.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            PreprocessResult: Typed result with the preprocessed DataFrame and
                descriptive statistics of the raw input frame.

        """
        return preprocess(df=df, config=self.config)

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
        minimizer: Minimizer,
        result: MinimizerResult,
        bundle: CompositeModelBundle | None = None,
    ) -> PostProcessingResult:
        """Postprocess the fitting results.

        Args:
            df: DataFrame with fit data.
            minimizer: The minimizer used.
            result: The fitting result.
            bundle: Optional CompositeModelBundle for local-fit decomposition.

        Returns:
            PostProcessingResult: Typed post-processing output.

        """
        postprocessor = PostProcessing(
            df=df,
            minimizer=minimizer,
            result=result,
            is_global=self.config.context.is_global,
            conf_interval=_resolve_conf_interval(self.config.conf_interval),
            bundle=bundle,
        )
        return postprocessor()


def fitting_routine_pipeline(
    args: UnifiedFittingConfig,
    output: OutputConfig | None = None,
) -> FittingResult:
    """Run the fitting algorithm using the pipeline pattern.

    This is a convenience function that creates and runs a FittingPipeline,
    prints results, and returns the typed ``FittingResult``.

    Args:
        args: Validated :class:`UnifiedFittingConfig` for the fitting run.
        output: Optional :class:`OutputConfig` controlling result export and
            display.  Defaults to ``OutputConfig()`` (standard output).

    Returns:
        FittingResult: Typed container with all pipeline outputs.

    """
    pipeline = FittingPipeline(config=args, output=output)
    result = pipeline.run()

    # Print results
    PrintingResults(
        post=result.post,
        data_statistic=result.data_statistic,
        conf_interval=_resolve_conf_interval(result.config.conf_interval),
        verbose=result.output.verbose,
        minimizer=result.minimizer,
        result=result.result,
    )()

    return result

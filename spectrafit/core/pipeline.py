"""Fitting pipeline for SpectraFit.

This module implements the pipeline pattern for the fitting workflow,
separating concerns and making the code more maintainable.
"""

from __future__ import annotations

from collections.abc import Callable
from functools import cached_property
from typing import TYPE_CHECKING
from typing import Protocol

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
from spectrafit.core.solver_runtime import LmfitSolverRuntime
from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.naming import sanitize_component_id
from spectrafit.models.output_config import OutputConfig
from spectrafit.models.preprocess_result import PreprocessResult
from spectrafit.models.split_frame import SplitFrame
from spectrafit.reporting.service import emit_runtime_report


if TYPE_CHECKING:
    from collections.abc import Callable

    from spectrafit.models.results.fit_result import FitResult


class SolverRuntime(Protocol):
    """Protocol for solver collaborators used by the pipeline."""

    @property
    def bundle(self) -> CompositeModelBundle | None:
        """Return the prepared bundle, when available."""

    def solve(self) -> tuple[Minimizer, MinimizerResult]:
        """Execute solving and return minimizer plus result."""


def build_data_config(config: UnifiedFittingConfig) -> DataConfig:
    """Build the typed data-loader config from the unified fitting config."""
    return DataConfig.from_unified(config)


def build_solver_models(
    df: pd.DataFrame, config: UnifiedFittingConfig
) -> SolverRuntime:
    """Build the solver runtime for one fitting pipeline run."""
    return LmfitSolverRuntime(df=df, config=config)


def run_postprocessing(
    df: pd.DataFrame,
    minimizer: Minimizer,
    result: MinimizerResult,
    config: UnifiedFittingConfig,
    bundle: CompositeModelBundle | None = None,
) -> PostProcessingResult:
    """Run canonical post-processing for one fitting pipeline run."""
    return PostProcessing(
        df=df,
        minimizer=minimizer,
        result=result,
        is_global=config.context.is_global,
        conf_interval=config.conf_interval,
        bundle=bundle,
        source_x_column=config.x_column,
        source_y_columns=[
            str(column) for column in df.columns if str(column) != config.x_column
        ],
        component_models={
            sanitize_component_id(component.id): component.model
            for component in config.components
        },
    )()


class ReportEmitter(Protocol):
    """Protocol for emitting runtime fit reports from pipeline results."""

    def __call__(
        self,
        *,
        fit_result: FitResult,
        data_statistic: SplitFrame,
        verbose: int,
    ) -> None:
        """Emit a runtime report from canonical fit-result data."""


class PipelineDependencies(BaseModel):
    """Injected collaborators for fitting pipeline orchestration."""

    model_config = ConfigDict(frozen=True, extra="forbid", arbitrary_types_allowed=True)

    data_config_factory: Callable[[UnifiedFittingConfig], DataConfig] = Field(
        default=build_data_config,
    )
    data_loader: Callable[[DataConfig], pd.DataFrame] = Field(default=load_data)
    preprocessor: Callable[[pd.DataFrame, UnifiedFittingConfig], PreprocessResult] = (
        Field(default=preprocess)
    )
    solver_factory: Callable[[pd.DataFrame, UnifiedFittingConfig], SolverRuntime] = (
        Field(default=build_solver_models)
    )
    postprocess_runner: Callable[
        [
            pd.DataFrame,
            Minimizer,
            MinimizerResult,
            UnifiedFittingConfig,
            CompositeModelBundle | None,
        ],
        PostProcessingResult,
    ] = Field(default=run_postprocessing)
    report_emitter: Callable[..., None] = Field(default=emit_runtime_report)


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
    data_statistic: SplitFrame = Field(default_factory=SplitFrame.empty)
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

    @cached_property
    def fit_result(self) -> FitResult:
        """Return the canonical typed fit-result projection for this pipeline run."""
        from spectrafit.core.result_bridge import (  # noqa: PLC0415
            build_fit_result_from_pipeline,
        )

        return build_fit_result_from_pipeline(self)

    def to_fit_result(self) -> FitResult:
        """Build a canonical :class:`~spectrafit.models.results.fit_result.FitResult`.

        Delegates to :func:`~spectrafit.core.result_bridge.build_fit_result_from_pipeline`
        so that all bridge logic lives in one module.

        Returns:
            FitResult: Canonical typed result ready for serialisation or
                further processing.
        """
        return self.fit_result

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
        request (FittingRequest): Typed request carrying config and output settings.

    """

    def __init__(
        self,
        request: FittingRequest,
        deps: PipelineDependencies | None = None,
    ) -> None:
        """Initialize FittingPipeline.

        Args:
            request: Typed request containing the validated
                :class:`UnifiedFittingConfig` plus runtime output settings.
            deps: Optional injected collaborators for data loading,
                preprocessing, solver construction, post-processing, and
                runtime reporting.

        """
        self.request: FittingRequest = request
        self.config: UnifiedFittingConfig = request.config
        self.output = request.output
        self.deps: PipelineDependencies = deps or PipelineDependencies()

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
        return self.deps.data_loader(self.deps.data_config_factory(self.config))

    def _preprocess(self, df: pd.DataFrame) -> PreprocessResult:
        """Preprocess the data.

        Args:
            df (pd.DataFrame): Input DataFrame.

        Returns:
            PreprocessResult: Typed result with the preprocessed DataFrame and
                descriptive statistics of the raw input frame.

        """
        return self.deps.preprocessor(df, self.config)

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
        solver = self.deps.solver_factory(df, self.config)
        minimizer, result = solver.solve()
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
        return self.deps.postprocess_runner(
            df,
            minimizer,
            result,
            self.config,
            bundle,
        )


def fitting_routine_pipeline(
    request: FittingRequest,
    deps: PipelineDependencies | None = None,
) -> FittingResult:
    """Run the fitting algorithm using the pipeline pattern.

    This is a convenience function that creates and runs a FittingPipeline,
    prints results, and returns the typed ``FittingResult``.

    Args:
        request: Typed request containing the validated fitting config and
            runtime output settings for this execution.
        deps: Optional injected collaborators for pipeline orchestration and
            runtime reporting.

    Returns:
        FittingResult: Typed container with all pipeline outputs.

    """
    pipeline = FittingPipeline(request=request, deps=deps)
    result = pipeline.run()
    pipeline.deps.report_emitter(
        fit_result=result.fit_result,
        data_statistic=result.data_statistic,
        verbose=request.output.verbose,
    )

    return result

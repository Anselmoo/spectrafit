"""Solver orchestration helpers for Jupyter notebook fitting."""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Protocol
from typing import TypedDict

import pandas as pd

from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.types import DataSplitDict
from spectrafit.utilities.transformer import LegacyModelSpec
from spectrafit.utilities.transformer import list2dict


if TYPE_CHECKING:
    from lmfit.minimizer import MinimizerResult


type ConfIntervalSettingsDict = dict[
    str, object
]  # intentional: TOML/JSON scalar export boundary
type ResolvedConfInterval = ConfIntervalConfig | ConfIntervalAPI
CI_BOUND_PAIR_LENGTH = 2


class LegacySolverArgs(TypedDict):
    """Legacy SolverModels kwargs dictionary used by notebook bridge paths."""

    global_: (
        int  # intentional: frozen-adapter for legacy SolverModels; 0=STANDARD, 1=GLOBAL
    )
    column: list[str]
    peaks: dict[str, LegacyModelSpec]
    minimizer: dict[
        str, object
    ]  # intentional: frozen-adapter — passes legacy SolverModels kwargs
    optimizer: dict[
        str, object
    ]  # intentional: frozen-adapter — passes legacy SolverModels kwargs


class PostProcessingResultView(Protocol):
    """Minimal post-processing result interface needed for fit-result projection."""

    df: pd.DataFrame
    regression_metrics: DataSplitDict
    descriptive_statistic: DataSplitDict
    linear_correlation: DataSplitDict
    confidence_interval: dict[str, object] | tuple[object, ...]  # intentional: protocol


def _serialize_conf_interval_settings(
    conf_interval: ResolvedConfInterval,
) -> ConfIntervalSettingsDict:
    """Serialize confidence settings into TOML/JSON-safe scalar values."""
    serialized: ConfIntervalSettingsDict = {}
    raw_settings = conf_interval.model_dump(exclude_none=True)
    for key, value in raw_settings.items():
        if key == "prob_func" and not isinstance(value, str):
            continue
        if isinstance(value, bool | float | int | str):
            serialized[key] = value
            continue
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            serialized[key] = value
            continue
        if isinstance(value, list) and all(isinstance(item, float) for item in value):
            serialized[key] = value
    return serialized


def _serialize_ci_results(
    ci_payload: dict[str, object]  # intentional: post-processing boundary
    | tuple[object, ...],
) -> dict[str, list[tuple[float, float]]]:
    """Convert post-processing confidence payload to typed confidence results."""
    if not isinstance(ci_payload, dict):
        return {}

    ci_results: dict[str, list[tuple[float, float]]] = {}
    for key, value in ci_payload.items():
        if not isinstance(value, list):
            continue

        bounds: list[tuple[float, float]] = []
        for item in value:
            if not isinstance(item, tuple | list) or len(item) != CI_BOUND_PAIR_LENGTH:
                continue
            lower, upper = item
            if not isinstance(lower, int | float) or not isinstance(upper, int | float):
                continue
            bounds.append((float(lower), float(upper)))

        if bounds:
            ci_results[key] = bounds
    return ci_results


def _to_object_dict(value: object) -> dict[str, object]:  # intentional: lmfit bridge
    """Convert object-like dictionaries into a homogeneous string-keyed dict."""
    if not isinstance(value, dict):
        return {}
    typed: dict[
        str, object
    ] = {}  # intentional: homogeneous wrapper for lmfit kwargs bridge
    for key, item in value.items():
        typed[str(key)] = item
    return typed


def normalize_conf_interval(
    conf_interval: bool | ConfIntervalAPI | ConfIntervalConfig,
) -> ResolvedConfInterval | None:
    """Normalize confidence interval settings for the solver layer.

    Args:
        conf_interval: Raw confidence interval settings from notebook/config API.

    Returns:
        Typed model when enabled, ``None`` when disabled.
    """
    if isinstance(conf_interval, ConfIntervalAPI):
        return conf_interval
    if isinstance(conf_interval, ConfIntervalConfig):
        return conf_interval
    return ConfIntervalConfig() if conf_interval is True else None


def resolve_solver_options(
    conf_interval: bool | ConfIntervalAPI | ConfIntervalConfig,
    solver_settings: SolverModelsAPI | None,
    config: UnifiedFittingConfig | None,
) -> tuple[ResolvedConfInterval | None, SolverModelsAPI | None]:
    """Resolve solver options from explicit params and optional unified config.

    Args:
        conf_interval: Direct confidence-interval argument from notebook API.
        solver_settings: Direct solver-settings argument from notebook API.
        config: Optional unified config override source.

    Returns:
        Normalized confidence model (or ``None``) and resolved solver settings.
    """
    if config is not None:
        conf_interval = config.conf_interval
        solver_settings = SolverModelsAPI(
            minimizer=config.minimizer,
            optimizer=config.optimizer,
        )
    return normalize_conf_interval(conf_interval), solver_settings


def apply_solver_settings(
    current_settings: SolverModelsAPI,
    solver_settings: SolverModelsAPI | None,
) -> SolverModelsAPI:
    """Apply solver settings while preserving existing notebook defaults.

    Args:
        current_settings: Current notebook solver settings.
        solver_settings: New settings model, or ``None`` to keep current.

    Returns:
        SolverModelsAPI: Effective solver settings after applying overrides.
    """
    if solver_settings is None:
        return current_settings
    return solver_settings


def build_solver_args(
    df: pd.DataFrame,
    initial_model: list[LegacyModelSpec],
    global_mode: FittingMode,
    solver_settings: SolverModelsAPI,
) -> LegacySolverArgs:  # intentional: legacy SolverModels bridge, v2.1 migration target
    """Build legacy ``SolverModels`` argument dictionary.

    Args:
        df: Dataframe used for fitting.
        initial_model: Legacy model specification list.
        global_mode: Fitting mode to map into legacy ``global_`` integer flag.
        solver_settings: Effective solver settings.

    Returns:
        LegacySolverArgs: Legacy ``SolverModels`` args dictionary.
    """
    return LegacySolverArgs(
        global_=0 if global_mode == FittingMode.STANDARD else 1,
        column=list(df.columns),
        peaks=list2dict(peak_list=initial_model)["peaks"],
        minimizer=_to_object_dict(solver_settings.minimizer.model_dump()),
        optimizer=_to_object_dict(solver_settings.optimizer.model_dump()),
    )


def build_fit_result(
    global_mode: FittingMode,
    minimizer_result: MinimizerResult,
    post_result: PostProcessingResultView,
    resolved_ci: ResolvedConfInterval | None,
) -> FitResult:
    """Build a typed ``FitResult`` from solver and post-processing outputs.

    Args:
        global_mode: Current notebook fitting mode.
        minimizer_result: lmfit minimizer result from solver stage.
        post_result: Post-processing output view.
        resolved_ci: Typed confidence interval settings, or ``None`` if disabled.

    Returns:
        FitResult: Typed result model for notebook/result export consumption.
    """
    fit_insights = FitInsights.from_minimizer_result(minimizer_result)
    data_summary = DataSummary(
        regression_metrics=post_result.regression_metrics,
        descriptive_statistic=post_result.descriptive_statistic,
        linear_correlation=post_result.linear_correlation,
    )

    ci_results = _serialize_ci_results(post_result.confidence_interval)

    ci_settings: ConfIntervalSettingsDict | bool = (
        _serialize_conf_interval_settings(resolved_ci)
        if resolved_ci is not None
        else False
    )

    return FitResult(
        global_fitting=global_mode,
        fit_insights=fit_insights,
        data_summary=data_summary,
        confidence=ConfidenceResults(
            settings=ci_settings,
            results=ci_results,
        ),
    )

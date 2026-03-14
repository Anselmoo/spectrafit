"""Shared typed bridges between runtime fitting results and CLI/Jupyter outputs."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Protocol

import pandas as pd

from pydantic import ValidationError

from spectrafit.adapters.fit_result_json import save_fit_result
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.column_names import ColumnNames
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.results.fit_result import ComponentResult
from spectrafit.models.results.fit_result import ConfidenceResults
from spectrafit.models.results.fit_result import DataSummary
from spectrafit.models.results.fit_result import FitInsights
from spectrafit.models.results.fit_result import FitResult
from spectrafit.models.results.fit_result import FitStatistics
from spectrafit.models.results.fit_result import InputSnapshot
from spectrafit.models.results.fit_result import JsonValue
from spectrafit.models.results.fit_result import ParameterResult
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import normalize_conf_interval_value
from spectrafit.models.split_frame import SplitFrame


if TYPE_CHECKING:
    from lmfit.minimizer import MinimizerResult

    from spectrafit.core.pipeline import FittingResult


_COLS = ColumnNames()


def _output_artifact_path(outfile: str, suffix: str) -> Path:
    """Build a CLI output path without reintroducing stringly path scatter."""
    return Path(outfile + "_" + suffix)


class PostProcessingResultView(Protocol):
    """Minimal post-processing interface needed for typed result projection."""

    df: pd.DataFrame
    fit_insights: FitInsights
    regression_metrics: SplitFrame
    descriptive_statistic: SplitFrame
    linear_correlation: SplitFrame
    confidence_interval: ConfidenceResults


def normalize_resolved_conf_interval(
    conf_interval: bool | ConfIntervalConfig | Mapping[str, object] | None,
) -> ConfIntervalConfig | None:
    """Normalize confidence interval settings into the resolved typed shape."""
    return normalize_conf_interval_value(conf_interval)


def resolve_fit_result_input_config(
    fit_result: FitResult,
) -> UnifiedFittingConfig | None:
    """Resolve the canonical typed config snapshot embedded in ``FitResult``."""
    if isinstance(fit_result.input_snapshot, Mapping):
        raw_snapshot = dict(fit_result.input_snapshot)
    else:
        raw_snapshot = fit_result.input_snapshot.model_dump(
            mode="python",
            exclude_none=True,
        )
    if not raw_snapshot:
        return None
    try:
        return UnifiedFittingConfig.model_validate(raw_snapshot)
    except ValidationError:
        return None


def _build_fit_statistics(minimizer_result: MinimizerResult) -> FitStatistics:
    """Build canonical fit statistics from an lmfit minimizer result."""
    return FitStatistics.from_minimizer_result(minimizer_result)


def _build_parameter_results(
    minimizer_result: MinimizerResult,
) -> list[ParameterResult]:
    """Build canonical parameter results from lmfit parameters."""
    parameter_results: list[ParameterResult] = []
    for name, parameter in minimizer_result.params.items():
        init_value = parameter.init_value
        if init_value is None:
            init_value = parameter.value
        parameter_results.append(
            ParameterResult(
                name=name,
                init_value=float(init_value),
                best_value=float(parameter.value),
                stderr=float(parameter.stderr)
                if parameter.stderr is not None
                else None,
                vary=bool(parameter.vary),
                expr=str(parameter.expr) if parameter.expr is not None else None,
            )
        )
    return parameter_results


def _extract_series(
    fit_df: pd.DataFrame,
) -> tuple[list[float], list[float], list[float]]:
    """Extract canonical x/data/fit series when standard columns are available."""
    required_columns = {_COLS.energy, _COLS.intensity, _COLS.fit}
    if not required_columns.issubset(fit_df.columns):
        return [], [], []
    return (
        fit_df[_COLS.energy].astype(float).tolist(),
        fit_df[_COLS.intensity].astype(float).tolist(),
        fit_df[_COLS.fit].astype(float).tolist(),
    )


def _extract_series_from_split_frame(
    fit_frame: SplitFrame,
) -> tuple[list[float], list[float], list[float]]:
    """Extract canonical series directly from the typed fit-result frame."""
    if not fit_frame.columns:
        return [], [], []
    return _extract_series(fit_frame.to_dataframe())


def _fit_frame_from_post_result(post_result: PostProcessingResultView) -> pd.DataFrame:
    """Resolve the most canonical fit-result frame available from post-processing."""
    fit_frame = getattr(post_result, "fit_result_data", None)
    if isinstance(fit_frame, SplitFrame) and fit_frame.columns:
        return fit_frame.to_dataframe()
    return post_result.df


def _extract_component_model_mapping(
    input_snapshot: Mapping[str, JsonValue] | None,
) -> dict[str, str]:
    """Extract canonical component-id to model-name mapping from the input snapshot."""
    if input_snapshot is None:
        return {}

    raw_components = input_snapshot.get("components")
    if not isinstance(raw_components, list):
        return {}

    component_models: dict[str, str] = {}
    for component in raw_components:
        if not isinstance(component, Mapping):
            continue
        component_id = component.get("id")
        model_name = component.get("model")
        if isinstance(component_id, str) and isinstance(model_name, str):
            component_models[component_id] = model_name
    return component_models


def _is_reserved_global_column(column_name: str, base_name: str) -> bool:
    """Return whether a column is a dataset-scoped canonical fit column."""
    prefix = f"{base_name}_"
    if not column_name.startswith(prefix):
        return False
    suffix = column_name.removeprefix(prefix)
    return suffix.isdigit() or suffix == "avg"


def _component_column_names(fit_df: pd.DataFrame) -> list[str]:
    """Return canonical component columns from an enriched fit dataframe."""
    reserved_columns = {
        _COLS.energy,
        _COLS.intensity,
        _COLS.fit,
        _COLS.residual,
        _COLS.residual_for_dataset("avg"),
    }
    component_columns: list[str] = []
    for raw_column in fit_df.columns:
        column_name = str(raw_column)
        if column_name in reserved_columns:
            continue
        if any(
            _is_reserved_global_column(column_name, base_name)
            for base_name in (_COLS.intensity, _COLS.fit, _COLS.residual)
        ):
            continue
        component_columns.append(column_name)
    return component_columns


def _lookup_component_model(
    component_id: str,
    component_models: Mapping[str, str],
) -> str:
    """Resolve the component model name for a component curve column."""
    if component_id in component_models:
        return component_models[component_id]

    base_component_id, separator, suffix = component_id.rpartition("_")
    if separator and suffix.isdigit() and base_component_id in component_models:
        return component_models[base_component_id]

    return base_component_id if separator and suffix.isdigit() else component_id


def _extract_component_results(
    post_result: PostProcessingResultView,
    input_snapshot: Mapping[str, JsonValue] | None,
) -> list[ComponentResult]:
    """Extract canonical component curves from the post-processing fit frame."""
    fit_df = _fit_frame_from_post_result(post_result)
    if fit_df.empty:
        return []

    component_models = _extract_component_model_mapping(input_snapshot)
    return [
        ComponentResult(
            id=component_column,
            model=_lookup_component_model(component_column, component_models),
            curve=fit_df[component_column].astype(float).tolist(),
        )
        for component_column in _component_column_names(fit_df)
    ]


def _build_data_summary(post_result: PostProcessingResultView) -> DataSummary:
    """Build canonical data-summary payloads from post-processing output."""
    grouped_summary = getattr(post_result, "data_summary", None)
    if isinstance(grouped_summary, DataSummary):
        return grouped_summary

    return DataSummary(
        regression_metrics=post_result.regression_metrics,
        descriptive_statistic=post_result.descriptive_statistic,
        linear_correlation=post_result.linear_correlation,
    )


def _extract_runtime_series(
    post_result: PostProcessingResultView,
) -> tuple[list[float], list[float], list[float]]:
    """Prefer typed fit-frame data when building canonical result series."""
    fit_frame = getattr(post_result, "fit_result_data", None)
    if isinstance(fit_frame, SplitFrame):
        typed_series = _extract_series_from_split_frame(fit_frame)
        if any(typed_series):
            return typed_series
    return _extract_series(post_result.df)


def build_fit_result_from_runtime(
    *,
    global_mode: FittingMode,
    minimizer_result: MinimizerResult,
    post_result: PostProcessingResultView,
    input_snapshot: Mapping[str, JsonValue] | None = None,
) -> FitResult:
    """Build a canonical FitResult from runtime solver and post-processing outputs."""
    x_values, y_data, y_fit = _extract_runtime_series(post_result)
    return FitResult(
        input_snapshot=InputSnapshot.model_validate(dict(input_snapshot or {})),
        statistics=_build_fit_statistics(minimizer_result),
        parameters=_build_parameter_results(minimizer_result),
        components=_extract_component_results(post_result, input_snapshot),
        x=x_values,
        y_data=y_data,
        y_fit=y_fit,
        global_fitting=global_mode,
        fit_insights=post_result.fit_insights,
        data_summary=_build_data_summary(post_result),
        confidence=ConfidenceResults.model_validate(post_result.confidence_interval),
    )


def build_fit_result_from_pipeline(fitting_result: FittingResult) -> FitResult:
    """Build a canonical FitResult from a pipeline FittingResult wrapper."""
    return build_fit_result_from_runtime(
        global_mode=fitting_result.config.context.mode,
        minimizer_result=fitting_result.result,
        post_result=fitting_result.post,
        input_snapshot=fitting_result.config.model_dump(mode="json", exclude_none=True),
    )


def build_correlation_frame(fit_result: FitResult) -> pd.DataFrame:
    """Build the CLI correlation artifact directly from canonical result data."""
    return fit_result.data_summary.linear_correlation.to_dataframe()


def build_component_parameter_frame(fit_result: FitResult) -> pd.DataFrame:
    """Build the CLI component-parameter artifact from canonical result data."""
    return pd.DataFrame.from_dict(
        {
            name: variable.model_dump(mode="json", exclude_none=True)
            for name, variable in fit_result.fit_insights.variables.items()
        }
    )


def write_cli_outputs(
    *,
    fit_result: FitResult,
    fit_df: pd.DataFrame,
    outfile: str,
) -> None:
    """Write CLI artifacts from canonical typed result data."""
    if not outfile:
        msg = "No output file provided!"
        raise FileNotFoundError(msg)

    save_fit_result(fit_result, _output_artifact_path(outfile, "summary.json"))

    fit_df.to_csv(_output_artifact_path(outfile, "fit.csv"), index=False)
    build_correlation_frame(fit_result).to_csv(
        _output_artifact_path(outfile, "correlation.csv"),
        index=True,
        index_label="attributes",
    )
    build_component_parameter_frame(fit_result).to_csv(
        _output_artifact_path(outfile, "components.csv"),
        index=True,
        index_label="attributes",
    )

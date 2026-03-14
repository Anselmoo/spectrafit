"""Notebook-first helpers built on the canonical SpectraFit runtime."""

from __future__ import annotations

import itertools

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from spectrafit.core.data_loader import sniff_separator
from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline
from spectrafit.core.pipeline import PipelineDependencies
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.output_config import OutputConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig
from spectrafit.notebook._result import FitSession


if TYPE_CHECKING:
    from spectrafit.models.meta_config import MetaConfig
    from spectrafit.models.preprocessing_config import PreprocessingConfig


type ParameterTuple = tuple[float, float, float] | tuple[float, float, float, bool]
type ParameterValue = FitParameter | float | int | ParameterTuple | dict[str, object]
type DataSource = pd.DataFrame | str | Path

_PEAK_COUNTER = itertools.count(1)
_BACKGROUND_COUNTER = itertools.count(1)
_NOTEBOOK_ATTRS_KEY = "spectrafit.notebook"
_TUPLE_WITH_BOUNDS_LEN = 3
_TUPLE_WITH_BOUNDS_AND_VARY_LEN = 4
_MIN_REQUIRED_COLUMNS = 2


def fixed(value: float) -> FitParameter:
    """Return a fixed fit parameter."""
    return FitParameter(value=float(value), vary=False)


def tie(expr: str) -> FitParameter:
    """Return a tied fit parameter using dot-notation expressions."""
    return FitParameter(expr=expr, vary=False)


def peak(
    model: str,
    /,
    *,
    id: str | None = None,  # noqa: A002
    **parameters: ParameterValue,
) -> Component:
    """Build one peak-like component using shorthand parameter syntax."""
    return _build_component(
        kind="peak",
        model=model,
        component_id=id,
        parameters=parameters,
    )


def background(
    model: str,
    /,
    *,
    id: str | None = None,  # noqa: A002
    **parameters: ParameterValue,
) -> Component:
    """Build one background component using the same shorthand protocol as ``peak``."""
    return _build_component(
        kind="background",
        model=model,
        component_id=id,
        parameters=parameters,
    )


def read(
    source: DataSource,
    *,
    x: str | None = None,
    y: str | None = None,
    separator: str | None = None,
    header: int | None = 0,
    decimal: str = ".",
    comment: str | None = None,
) -> pd.DataFrame:
    """Load notebook data with lightweight defaults and preserved metadata."""
    if isinstance(source, pd.DataFrame):
        dataframe = source.copy(deep=True)
        resolved_x, resolved_y = _resolve_dataframe_columns(
            dataframe,
            x=x,
            y=y,
        )
        return _attach_notebook_attrs(
            dataframe,
            path=_metadata_path(_notebook_metadata(source)),
            x=resolved_x,
            y=resolved_y,
            separator=separator or _notebook_metadata(source).get("separator"),
            header=header,
            decimal=decimal,
            comment=comment,
        )

    path = Path(source)
    resolved_separator = separator or sniff_separator(path)
    dataframe = pd.read_csv(
        path,
        sep=resolved_separator,
        header=header,
        decimal=decimal,
        comment=comment,
    )
    resolved_x, resolved_y = _resolve_dataframe_columns(dataframe, x=x, y=y)
    return _attach_notebook_attrs(
        dataframe,
        path=path.resolve(),
        x=resolved_x,
        y=resolved_y,
        separator=resolved_separator,
        header=header,
        decimal=decimal,
        comment=comment,
    )


def fit(
    data: DataSource,
    *,
    peaks: Sequence[Component] | Component,
    background: Sequence[Component] | Component | None = None,
    x: str | None = None,
    y: str | None = None,
    separator: str | None = None,
    header: int | None = 0,
    decimal: str = ".",
    comment: str | None = None,
    minimizer: MinimizerConfig | None = None,
    optimizer: OptimizerConfig | None = None,
    preprocessing: PreprocessingConfig | None = None,
    context: FittingContext | None = None,
    conf_interval: bool | ConfIntervalConfig = False,
    meta: MetaConfig | None = None,
    preview: bool = False,
    name: str = "spectrafit",
) -> FitSession:
    """Run one fit through the canonical pipeline and return a notebook session."""
    dataframe = read(
        data,
        x=x,
        y=y,
        separator=separator,
        header=header,
        decimal=decimal,
        comment=comment,
    )
    metadata = _notebook_metadata(dataframe)
    resolved_context = context or FittingContext()
    resolved_components = _normalize_components(peaks, background)
    config = UnifiedFittingConfig(
        components=resolved_components,
        minimizer=minimizer or MinimizerConfig(),
        optimizer=optimizer or OptimizerConfig(),
        column=ColumnConfig(x=str(metadata["x"]), y=str(metadata["y"])),
        context=resolved_context,
        conf_interval=conf_interval,
        meta=meta,
        data=_build_data_config(metadata=metadata, context=resolved_context),
        preprocessing=preprocessing,
    )
    request = FittingRequest.from_config(
        config,
        output=OutputConfig(outfile=name, noplot=True, verbose=0),
    )
    deps = None
    if metadata.get("path") is None:
        deps = _in_memory_deps(dataframe, metadata, resolved_context)
    pipeline = FittingPipeline(request=request, deps=deps)
    session = FitSession(
        pipeline_result=pipeline.run(),
        source_dataframe=dataframe,
        name=name,
    )
    if preview:
        session.plot()
    return session


def _build_component(
    *,
    kind: str,
    model: str,
    component_id: str | None,
    parameters: dict[str, ParameterValue],
) -> Component:
    """Build one canonical component from shorthand notebook inputs."""
    resolved_id = component_id or _auto_component_id(kind)
    return Component(
        id=resolved_id,
        model=model,
        parameters={
            name: _coerce_parameter(value) for name, value in parameters.items()
        },
    )


def _auto_component_id(kind: str) -> str:
    """Return a stable auto id within the current notebook kernel session."""
    if kind == "background":
        return f"bg{next(_BACKGROUND_COUNTER)}"
    return f"peak{next(_PEAK_COUNTER)}"


def _coerce_parameter(value: ParameterValue) -> FitParameter:
    """Normalize shorthand parameter inputs into ``FitParameter``."""
    if isinstance(value, FitParameter):
        return value
    if isinstance(value, dict):
        return FitParameter.model_validate(value)
    if isinstance(value, int | float):
        return FitParameter(value=float(value))
    if isinstance(value, tuple):
        if len(value) == _TUPLE_WITH_BOUNDS_LEN:
            resolved_value, minimum, maximum = value
            return FitParameter(
                value=float(resolved_value),
                min=float(minimum),
                max=float(maximum),
            )
        if len(value) == _TUPLE_WITH_BOUNDS_AND_VARY_LEN:
            resolved_value, minimum, maximum, vary = value
            return FitParameter(
                value=float(resolved_value),
                min=float(minimum),
                max=float(maximum),
                vary=bool(vary),
            )
    msg = (
        "Notebook parameters must be floats, FitParameter instances, "
        "dict payloads, or tuples of (value, min, max[, vary])."
    )
    raise TypeError(msg)


def _resolve_dataframe_columns(
    dataframe: pd.DataFrame,
    *,
    x: str | None,
    y: str | None,
) -> tuple[str, str]:
    """Resolve the canonical x/y column names for a notebook dataframe."""
    metadata = _notebook_metadata(dataframe)
    resolved_x = x or metadata.get("x")
    resolved_y = y or metadata.get("y")
    columns = [str(column) for column in dataframe.columns]
    if resolved_x is None:
        resolved_x = columns[0]
    if resolved_y is None:
        if len(columns) < _MIN_REQUIRED_COLUMNS:
            msg = "Notebook data requires at least two columns when y is not provided."
            raise ValueError(msg)
        resolved_y = columns[1]
    if str(resolved_x) not in columns:
        msg = f"Unknown x column '{resolved_x}'. Available columns: {columns}"
        raise ValueError(msg)
    if str(resolved_y) not in columns:
        msg = f"Unknown y column '{resolved_y}'. Available columns: {columns}"
        raise ValueError(msg)
    return str(resolved_x), str(resolved_y)


def _attach_notebook_attrs(
    dataframe: pd.DataFrame,
    *,
    path: Path | None,
    x: str,
    y: str,
    separator: str | None,
    header: int | None,
    decimal: str,
    comment: str | None,
) -> pd.DataFrame:
    """Attach canonical notebook metadata to a dataframe."""
    metadata = dict(dataframe.attrs)
    metadata[_NOTEBOOK_ATTRS_KEY] = {
        "path": str(path) if path is not None else None,
        "x": x,
        "y": y,
        "separator": separator,
        "header": header,
        "decimal": decimal,
        "comment": comment,
    }
    dataframe.attrs = metadata
    return dataframe


def _notebook_metadata(dataframe: pd.DataFrame) -> dict[str, object]:
    """Return notebook metadata previously attached by ``read``."""
    raw_metadata = dataframe.attrs.get(_NOTEBOOK_ATTRS_KEY, {})
    if not isinstance(raw_metadata, dict):
        return {}
    return raw_metadata


def _metadata_path(metadata: dict[str, object]) -> Path | None:
    """Return the optional source path stored in notebook metadata."""
    raw_path = metadata.get("path")
    if raw_path is None:
        return None
    return Path(str(raw_path))


def _normalize_components(
    peaks: Sequence[Component] | Component,
    background: Sequence[Component] | Component | None,
) -> list[Component]:
    """Normalize notebook component inputs into one ordered component list."""
    resolved_peaks = _as_component_list(peaks)
    if background is None:
        return resolved_peaks
    resolved_background = _as_component_list(background)
    return [*resolved_peaks, *resolved_background]


def _as_component_list(
    value: Sequence[Component] | Component,
) -> list[Component]:
    """Normalize a component or component sequence into a list."""
    if isinstance(value, Sequence) and not isinstance(value, Component):
        return list(value)
    return [value]


def _build_data_config(
    *,
    metadata: dict[str, object],
    context: FittingContext,
) -> DataConfig | None:
    """Build a path-backed data config when the notebook input came from disk."""
    path = _metadata_path(metadata)
    if path is None:
        return None
    return DataConfig(
        infile=path,
        x_col=str(metadata["x"]),
        y_col=str(metadata["y"]),
        separator=str(metadata.get("separator") or r"\s+"),
        header=metadata.get("header"),
        decimal=str(metadata.get("decimal") or "."),
        comment=(
            str(metadata["comment"]) if metadata.get("comment") is not None else None
        ),
        context=context,
    )


def _in_memory_deps(
    dataframe: pd.DataFrame,
    metadata: dict[str, object],
    context: FittingContext,
) -> PipelineDependencies:
    """Override the pipeline loader when the notebook input is already in memory."""
    return PipelineDependencies(
        data_config_factory=lambda _: DataConfig(
            infile=Path("in-memory.csv"),
            x_col=str(metadata["x"]),
            y_col=str(metadata["y"]),
            separator=str(metadata.get("separator") or r"\s+"),
            header=metadata.get("header"),
            decimal=str(metadata.get("decimal") or "."),
            comment=(
                str(metadata["comment"])
                if metadata.get("comment") is not None
                else None
            ),
            context=context,
        ),
        data_loader=lambda _: dataframe.copy(deep=True),
    )

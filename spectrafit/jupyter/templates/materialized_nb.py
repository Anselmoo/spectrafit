"""Shared builders for compact SpectraFit notebooks."""

from __future__ import annotations

import ast
import json
import math

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

import nbformat

from nbformat.v4 import new_code_cell
from nbformat.v4 import new_markdown_cell
from nbformat.v4 import new_notebook
from pydantic import BaseModel

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.naming import restore_dot_notation
from spectrafit.models.preprocessing_config import PreprocessingConfig


if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Mapping


_COMMON_IMPORTS_CODE = """\
from __future__ import annotations

from pathlib import Path

import spectrafit.notebook as sf
"""

_LOCAL_PATHS_CODE = """\
NOTEBOOK_ROOT = Path.cwd()
DATA_PATH = NOTEBOOK_ROOT / {data_path!r}
OUTPUT_DIR = NOTEBOOK_ROOT / "outputs" / "live" / "notebook"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"Notebook root: {{NOTEBOOK_ROOT}}")
print(f"Using local data file: {{DATA_PATH}}")
"""

_READ_DATA_CODE = """\
df = sf.read(DATA_PATH, x={x_column!r}, y={y_column!r})
location = NOTEBOOK_ROOT.name or str(NOTEBOOK_ROOT)
print(f"Loaded {{DATA_PATH.name}} with {{len(df)}} rows from {{location}}")
df.head()
"""

_EXPORT_ARTIFACTS_CODE = """\
artifacts = result.save(OUTPUT_DIR, name={artifact_name!r})

[path.name for path in artifacts]
"""

_NOTEBOOK_LANGUAGE_VERSION = "3.12.0"
_BACKGROUND_MODELS = frozenset({"constant", "linear", "polynom2"})


@dataclass(frozen=True)
class _RawCode:
    """Marker for Python source that should be embedded verbatim."""

    code: str


def _markdown_cell(source: str, cell_id: str) -> object:
    """Build a markdown cell."""
    return new_markdown_cell(source=source, id=cell_id)


def _code_cell(source: str, cell_id: str) -> object:
    """Build a code cell."""
    return new_code_cell(source=source, id=cell_id)


def _validate_python_source(source: str) -> None:
    """Validate that generated notebook code parses as Python."""
    ast.parse(source)


def build_materialized_config_model(
    config: UnifiedFittingConfig | Mapping[str, object],
    *,
    data_path: str,
) -> UnifiedFittingConfig:
    """Build a notebook-owned typed config model with a local relative data path."""
    typed_config = (
        config
        if isinstance(config, UnifiedFittingConfig)
        else UnifiedFittingConfig.from_dict(config)
    )
    return typed_config.with_data_infile(data_path)


def _render_scalar(value: object) -> str:
    """Render a scalar Python literal."""
    if isinstance(value, _RawCode):
        return value.code
    if isinstance(value, Path):
        return f"Path({str(value)!r})"
    if isinstance(value, Enum):
        return f"{type(value).__name__}.{value.name}"
    if isinstance(value, float) and math.isinf(value):
        return "float('inf')" if value > 0 else "-float('inf')"
    return repr(value)


def _render_python_value(value: object, *, indent: int = 4) -> str:
    """Render Python source for a typed notebook section."""
    if isinstance(value, (str, int, float, bool, type(None), Path, Enum, _RawCode)):
        return _render_scalar(value)

    if isinstance(value, BaseModel):
        return _render_model_instance(value, indent=indent)

    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            rendered = _render_python_value(item, indent=indent + 4).splitlines()
            lines.append(f"{' ' * indent}{rendered[0]}")
            lines.extend(rendered[1:])
            lines[-1] = f"{lines[-1]},"
        lines.append("]")
        return "\n".join(lines)

    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for key, item in value.items():
            rendered = _render_python_value(item, indent=indent + 4).splitlines()
            lines.append(f"{' ' * indent}{key!r}: {rendered[0]}")
            lines.extend(rendered[1:])
            lines[-1] = f"{lines[-1]},"
        lines.append("}")
        return "\n".join(lines)

    return _render_scalar(value)


def _model_kwargs(model: BaseModel) -> dict[str, object]:
    """Return notebook-facing constructor kwargs for a model."""
    kwargs = {
        field_name: getattr(model, field_name)
        for field_name in type(model).model_fields
        if getattr(model, field_name) is not None
    }
    if model.model_extra:
        kwargs.update(model.model_extra)
    if isinstance(model, FittingContext):
        kwargs.pop("environment", None)
    if isinstance(model, UnifiedFittingConfig) and model.data is not None:
        kwargs.pop("column", None)
    return kwargs


def _render_model_call(
    class_name: str,
    kwargs: dict[str, object],
    *,
    indent: int = 4,
    value_renderer: Callable[..., str] | None = None,
) -> str:
    """Render a multi-line class constructor."""
    if not kwargs:
        return f"{class_name}()"

    render_value = _render_python_value if value_renderer is None else value_renderer
    lines = [f"{class_name}("]
    for key, value in kwargs.items():
        rendered = render_value(value, indent=indent + 4).splitlines()
        lines.append(f"{' ' * indent}{key}={rendered[0]}")
        lines.extend(rendered[1:])
        lines[-1] = f"{lines[-1]},"
    lines.append(")")
    return "\n".join(lines)


def _render_model_instance(model: BaseModel, *, indent: int = 4) -> str:
    """Render a model instance as constructor source."""
    return _render_model_call(type(model).__name__, _model_kwargs(model), indent=indent)


def _render_assignment(name: str, value: object) -> str:
    """Render a variable assignment, preserving multi-line layout."""
    rendered = _render_python_value(value).splitlines()
    lines = [f"{name} = {rendered[0]}"]
    lines.extend(rendered[1:])
    return "\n".join(lines)


def _render_data_section(config: UnifiedFittingConfig) -> str:
    """Render the data-loading section using notebook-local paths."""
    data_config = config.data
    if data_config is None:
        data_kwargs: dict[str, object] = {"infile": _RawCode("DATA_PATH")}
    else:
        data_kwargs = data_config.model_dump(mode="python", exclude_none=True)
        data_kwargs.pop("context", None)
        data_kwargs["infile"] = _RawCode("DATA_PATH")
    return _render_assignment(
        "data", _RawCode(_render_model_call("DataConfig", data_kwargs))
    )


def _render_config_assembly(config: UnifiedFittingConfig) -> str:
    """Render the final typed ``UnifiedFittingConfig`` assembly."""
    kwargs: dict[str, object] = {
        "components": _RawCode("components"),
        "minimizer": _RawCode("minimizer"),
        "optimizer": _RawCode("optimizer"),
        "context": _RawCode("context"),
        "data": _RawCode("data"),
        "preprocessing": _RawCode("preprocessing"),
    }
    if config.meta is not None:
        kwargs["meta"] = _RawCode("meta")
    if config.conf_interval not in (False, None):
        kwargs["conf_interval"] = _RawCode("conf_interval")
    if config.global_fitting_config is not None:
        kwargs["global_fitting_config"] = _RawCode("global_fitting_config")
    if config.mcmc is not None:
        kwargs["mcmc"] = _RawCode("mcmc")
    return _render_assignment(
        "config",
        _RawCode(_render_model_call("UnifiedFittingConfig", kwargs)),
    )


def render_materialized_config_cell(
    config: UnifiedFittingConfig | Mapping[str, object],
    *,
    data_path: str,
) -> str:
    """Render the compatibility typed-config code cell source."""
    typed_config = build_materialized_config_model(config, data_path=data_path)
    sections = [
        "# Typed notebook sections — edit these models directly and re-run this cell.",
        _render_assignment("components", typed_config.components),
        "",
        _render_data_section(typed_config),
        _render_assignment(
            "preprocessing", typed_config.preprocessing or PreprocessingConfig()
        ),
        _render_assignment("context", typed_config.context),
        _render_assignment("minimizer", typed_config.minimizer),
        _render_assignment("optimizer", typed_config.optimizer),
    ]

    if typed_config.meta is not None:
        sections.extend(("", _render_assignment("meta", typed_config.meta)))
    if typed_config.conf_interval not in (False, None):
        sections.extend(
            ("", _render_assignment("conf_interval", typed_config.conf_interval))
        )
    if typed_config.global_fitting_config is not None:
        sections.extend(
            (
                "",
                _render_assignment(
                    "global_fitting_config", typed_config.global_fitting_config
                ),
            )
        )
    if typed_config.mcmc is not None:
        sections.extend(("", _render_assignment("mcmc", typed_config.mcmc)))

    sections.extend(
        (
            "",
            "# Assemble the validated SpectraFit config from the typed sections above.",
            _render_config_assembly(typed_config),
            "",
            "config",
        )
    )
    return "\n".join(sections)


def _render_sf_scalar(value: object) -> str:
    """Render a scalar literal for the simplified ``spectrafit.notebook`` surface."""
    if isinstance(value, _RawCode):
        return value.code
    if isinstance(value, Path):
        return repr(str(value))
    if isinstance(value, Enum):
        return f"sf.{type(value).__name__}.{value.name}"
    if isinstance(value, float) and math.isinf(value):
        return "float('inf')" if value > 0 else "-float('inf')"
    return repr(value)


def _render_sf_value(value: object, *, indent: int = 4) -> str:
    """Render Python source that uses ``sf.<Type>`` escape hatches when needed."""
    if isinstance(value, (str, int, float, bool, type(None), Path, Enum, _RawCode)):
        return _render_sf_scalar(value)
    if isinstance(value, BaseModel):
        kwargs = _model_kwargs(value)
        return _render_model_call(
            f"sf.{type(value).__name__}",
            kwargs,
            indent=indent,
            value_renderer=_render_sf_value,
        )
    if isinstance(value, list):
        if not value:
            return "[]"
        lines = ["["]
        for item in value:
            rendered = _render_sf_value(item, indent=indent + 4).splitlines()
            lines.append(f"{' ' * indent}{rendered[0]}")
            lines.extend(rendered[1:])
            lines[-1] = f"{lines[-1]},"
        lines.append("]")
        return "\n".join(lines)
    if isinstance(value, dict):
        if not value:
            return "{}"
        lines = ["{"]
        for key, item in value.items():
            rendered = _render_sf_value(item, indent=indent + 4).splitlines()
            lines.append(f"{' ' * indent}{key!r}: {rendered[0]}")
            lines.extend(rendered[1:])
            lines[-1] = f"{lines[-1]},"
        lines.append("}")
        return "\n".join(lines)
    return _render_sf_scalar(value)


def _render_sf_assignment(name: str, value: object) -> str:
    """Render a one-variable assignment for the simplified notebook surface."""
    rendered = _render_sf_value(value).splitlines()
    lines = [f"{name} = {rendered[0]}"]
    lines.extend(rendered[1:])
    return "\n".join(lines)


def _render_parameter_shorthand(
    parameter: BaseModel,
    *,
    known_parameters: dict[str, tuple[str, ...]],
) -> str:
    """Render one ``FitParameter`` as notebook shorthand."""
    value = parameter.value
    minimum = parameter.min
    maximum = parameter.max
    vary = parameter.vary
    expr = parameter.expr
    if expr is not None:
        restored_expr = restore_dot_notation(expr, known_parameters=known_parameters)
        return f"sf.tie({restored_expr!r})"
    if not vary:
        return f"sf.fixed({value!r})"
    if minimum == -math.inf and maximum == math.inf:
        return repr(value)
    return f"({value!r}, {_render_sf_scalar(minimum)}, {_render_sf_scalar(maximum)})"


def _render_component_call(
    component: BaseModel,
    *,
    known_parameters: dict[str, tuple[str, ...]],
) -> str:
    """Render one ``sf.peak(...)`` or ``sf.background(...)`` call."""
    model = component.model
    component_id = component.id
    parameters = component.parameters
    factory = "background" if model in _BACKGROUND_MODELS else "peak"
    lines = [f"sf.{factory}(", f"    {model!r},", f"    id={component_id!r},"]
    for name, parameter in parameters.items():
        rendered_parameter = _render_parameter_shorthand(
            parameter,
            known_parameters=known_parameters,
        )
        lines.append(f"    {name}={rendered_parameter},")
    lines.append(")")
    return "\n".join(lines)


def _render_component_list(
    name: str,
    components: list[BaseModel],
    *,
    known_parameters: dict[str, tuple[str, ...]],
) -> str:
    """Render a notebook component list."""
    if not components:
        return f"{name} = []"
    lines = [f"{name} = ["]
    for component in components:
        rendered = _render_component_call(
            component,
            known_parameters=known_parameters,
        ).splitlines()
        lines.append(f"    {rendered[0]}")
        lines.extend(f"    {line}" for line in rendered[1:])
        lines[-1] = f"{lines[-1]},"
    lines.append("]")
    return "\n".join(lines)


def _is_default_model(model: BaseModel, default_model: BaseModel) -> bool:
    """Return whether a typed config section matches its default model instance."""
    return model.model_dump(
        mode="python", exclude_none=True
    ) == default_model.model_dump(
        mode="python",
        exclude_none=True,
    )


def _append_named_section(
    sections: list[str],
    *,
    should_include: bool,
    name: str,
    value: object,
) -> None:
    """Append one named assignment block when the section is non-default."""
    if should_include:
        sections.extend(("", _render_sf_assignment(name, value)))


def _build_fit_lines(
    *,
    include_background: bool,
    include_preprocessing: bool,
    include_context: bool,
    include_minimizer: bool,
    include_optimizer: bool,
    include_meta: bool,
    include_conf_interval: bool,
    artifact_name: str,
) -> list[str]:
    """Build the compact ``sf.fit(...)`` call for generated notebooks."""
    fit_lines = [
        "result = sf.fit(",
        "    df,",
        "    peaks=peaks,",
    ]
    if include_background:
        fit_lines.append("    background=background,")
    if include_preprocessing:
        fit_lines.append("    preprocessing=preprocessing,")
    if include_context:
        fit_lines.append("    context=context,")
    if include_minimizer:
        fit_lines.append("    minimizer=minimizer,")
    if include_optimizer:
        fit_lines.append("    optimizer=optimizer,")
    if include_meta:
        fit_lines.append("    meta=meta,")
    if include_conf_interval:
        fit_lines.append("    conf_interval=conf_interval,")
    fit_lines.append(f"    name={artifact_name!r},")
    fit_lines.append(")")
    return fit_lines


def render_simple_notebook_flow(
    config: UnifiedFittingConfig | Mapping[str, object],
    *,
    artifact_name: str,
    data_path: str,
) -> str:
    """Render the simplified ``spectrafit.notebook`` fitting cell."""
    typed_config = build_materialized_config_model(config, data_path=data_path)
    peaks = [
        component
        for component in typed_config.components
        if component.model not in _BACKGROUND_MODELS
    ]
    backgrounds = [
        component
        for component in typed_config.components
        if component.model in _BACKGROUND_MODELS
    ]
    known_parameters = {
        component.id: tuple(component.parameters.keys())
        for component in typed_config.components
    }
    sections = [
        _render_component_list(
            "peaks",
            peaks,
            known_parameters=known_parameters,
        )
    ]
    if backgrounds:
        sections.extend(
            (
                "",
                _render_component_list(
                    "background",
                    backgrounds,
                    known_parameters=known_parameters,
                ),
            )
        )
    default_context = FittingContext()
    default_minimizer = type(typed_config.minimizer)()
    default_optimizer = type(typed_config.optimizer)()
    include_preprocessing = (
        typed_config.preprocessing is not None
        and not _is_default_model(
            typed_config.preprocessing,
            PreprocessingConfig(),
        )
    )
    include_context = not _is_default_model(typed_config.context, default_context)
    include_minimizer = not _is_default_model(typed_config.minimizer, default_minimizer)
    include_optimizer = not _is_default_model(typed_config.optimizer, default_optimizer)
    include_meta = typed_config.meta is not None
    include_conf_interval = typed_config.conf_interval not in (False, None)

    _append_named_section(
        sections,
        should_include=include_preprocessing,
        name="preprocessing",
        value=typed_config.preprocessing,
    )
    _append_named_section(
        sections,
        should_include=include_context,
        name="context",
        value=typed_config.context,
    )
    _append_named_section(
        sections,
        should_include=include_minimizer,
        name="minimizer",
        value=typed_config.minimizer,
    )
    _append_named_section(
        sections,
        should_include=include_optimizer,
        name="optimizer",
        value=typed_config.optimizer,
    )
    _append_named_section(
        sections,
        should_include=include_meta,
        name="meta",
        value=typed_config.meta,
    )
    _append_named_section(
        sections,
        should_include=include_conf_interval,
        name="conf_interval",
        value=typed_config.conf_interval,
    )

    fit_lines = _build_fit_lines(
        include_background=bool(backgrounds),
        include_preprocessing=include_preprocessing,
        include_context=include_context,
        include_minimizer=include_minimizer,
        include_optimizer=include_optimizer,
        include_meta=include_meta,
        include_conf_interval=include_conf_interval,
        artifact_name=artifact_name,
    )
    sections.extend(("", *fit_lines, "", "result.plot()", "result.metrics"))
    return "\n".join(sections)


def build_materialized_notebook(
    *,
    project_name: str,
    intro_title: str,
    intro_body: str,
    artifact_name: str,
    config: UnifiedFittingConfig | Mapping[str, object],
    data_path: str,
    prep_markdown: str | None = None,
    prep_code: str | None = None,
    next_steps: tuple[str, ...] | None = None,
) -> dict[str, object]:
    """Build a notebook with the simplified ``spectrafit.notebook`` API."""
    typed_config = build_materialized_config_model(config, data_path=data_path)
    resolved_next_steps = next_steps or (
        (
            "Inspect the generated CSVs, HTML fit plot, report, and lockfile in "
            "`outputs/live/notebook/`."
        ),
        (
            "Edit the compact `sf.peak(...)` / `sf.background(...)` definitions and "
            "rerun the fit cell to explore different models, bounds, and solver "
            "settings."
        ),
    )
    next_steps_markdown = "\n".join(f"- {item}" for item in resolved_next_steps)

    cells: list[object] = [
        _markdown_cell(
            f"# {intro_title}\n\n"
            f"{intro_body}\n\n"
            "## Workflow\n"
            "1. Resolve local notebook paths.\n"
            "2. Load `data.csv` through `sf.read(...)`.\n"
            "3. Edit compact `sf.peak(...)` and `sf.background(...)` definitions.\n"
            "4. Run `sf.fit(...)` and inspect the inline plot/metrics.\n"
            "5. Export bundled live notebook artifacts under `outputs/live/notebook/`.\n",
            "intro",
        ),
        _code_cell(_COMMON_IMPORTS_CODE, "imports"),
    ]

    if prep_markdown is not None and prep_code is not None:
        cells.extend(
            (
                _markdown_cell(prep_markdown, "prepare-md"),
                _code_cell(prep_code, "prepare-code"),
            )
        )

    cells.extend(
        (
            _markdown_cell(
                "## 1 — Resolve local paths\n\n"
                f"This notebook always loads `{data_path}` from the local notebook "
                "directory and writes exports under `outputs/live/notebook/`.",
                "paths-md",
            ),
            _code_cell(_LOCAL_PATHS_CODE.format(data_path=data_path), "paths"),
            _markdown_cell(
                "## 2 — Load the local dataset\n\n"
                "Use the single notebook import to load the local spectrum and keep the "
                "data columns attached to the dataframe for the fit step.",
                "read-md",
            ),
            _code_cell(
                _READ_DATA_CODE.format(
                    x_column=typed_config.x_column,
                    y_column=typed_config.y_column,
                ),
                "read-data",
            ),
            _markdown_cell(
                "## 3 — Define the fit and run it\n\n"
                "The compact notebook API still compiles into the canonical "
                "`UnifiedFittingConfig -> FittingPipeline -> FitResult` chain under the "
                "hood, but the cell below hides the internal object graph.",
                "fit-md",
            ),
            _code_cell(
                render_simple_notebook_flow(
                    typed_config,
                    artifact_name=artifact_name,
                    data_path=data_path,
                ),
                "fit-flow",
            ),
            _markdown_cell(
                "## 4 — Export notebook artifacts\n\n"
                "Use one `result.save(...)` call to write the fitted dataframe, "
                "metric table, peak table, HTML plot, report, and lockfile.",
                "export-md",
            ),
            _code_cell(
                _EXPORT_ARTIFACTS_CODE.format(artifact_name=artifact_name),
                "export-artifacts",
            ),
            _markdown_cell(
                f"## Next steps\n\n{next_steps_markdown}\n",
                "next-steps",
            ),
        )
    )

    for cell in cells:
        if cell["cell_type"] == "code":
            _validate_python_source(str(cell["source"]))

    notebook = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {
                "display_name": "Python 3 (ipykernel)",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": _NOTEBOOK_LANGUAGE_VERSION,
            },
            "spectrafit": {
                "project": project_name,
                "artifact_name": artifact_name,
            },
        },
    )
    nbformat.validate(notebook)
    return json.loads(json.dumps(notebook))


def write_materialized_notebook(
    *,
    output_path: Path,
    project_name: str,
    intro_title: str,
    intro_body: str,
    artifact_name: str,
    config: UnifiedFittingConfig | Mapping[str, object],
    data_path: str,
    prep_markdown: str | None = None,
    prep_code: str | None = None,
    next_steps: tuple[str, ...] | None = None,
) -> None:
    """Write a compact SpectraFit notebook to disk."""
    notebook = build_materialized_notebook(
        project_name=project_name,
        intro_title=intro_title,
        intro_body=intro_body,
        artifact_name=artifact_name,
        config=config,
        data_path=data_path,
        prep_markdown=prep_markdown,
        prep_code=prep_code,
        next_steps=next_steps,
    )
    output_path.write_text(json.dumps(notebook, indent=1), encoding="utf-8")

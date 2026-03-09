"""Configuration I/O helpers for the Jupyter notebook integration."""

from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import tomli_w

from spectrafit.api.models_model import ConfIntervalAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.utilities.transformer import list2components


if TYPE_CHECKING:
    from spectrafit.jupyter.core import SpectraFitNotebook


def _normalize_conf_interval_settings(
    settings: bool | dict[str, object] | ConfIntervalConfig | ConfIntervalAPI,
) -> bool | ConfIntervalConfig:
    """Normalize confidence interval settings into UnifiedFittingConfig shape."""
    if isinstance(settings, bool | ConfIntervalConfig):
        return settings

    raw_settings = (
        settings.model_dump(exclude_none=True)
        if isinstance(settings, ConfIntervalAPI)
        else dict(settings)
    )
    prob_func = raw_settings.get("prob_func")
    if prob_func is not None and not isinstance(prob_func, str):
        raw_settings.pop("prob_func", None)

    return ConfIntervalConfig.model_validate(raw_settings)


def build_notebook_from_config(
    notebook_cls: type[SpectraFitNotebook],
    df: pd.DataFrame,
    config: UnifiedFittingConfig,
    **kwargs: object,
) -> SpectraFitNotebook:
    """Create and configure a notebook instance from a unified config.

    Args:
        notebook_cls: Notebook class constructor.
        df: Input spectra dataframe.
        config: Validated unified fitting configuration.
        **kwargs: Additional keyword arguments forwarded to the notebook constructor.

    Returns:
        SpectraFitNotebook: Configured notebook instance.
    """
    notebook = notebook_cls(
        df=df,
        x_column=config.column.x,
        y_column=config.column.y,
        **kwargs,
    )
    notebook.settings_solver_models = SolverModelsAPI(
        minimizer=config.minimizer,
        optimizer=config.optimizer,
    )
    notebook.global_ = config.context.mode
    return notebook


def notebook_args_to_config(notebook: SpectraFitNotebook) -> UnifiedFittingConfig:
    """Convert a notebook state into ``UnifiedFittingConfig``.

    Args:
        notebook: Notebook instance with current fit state.

    Returns:
        UnifiedFittingConfig: Validated configuration matching notebook state.
    """
    components = list2components(peak_list=notebook.initial_model)
    y_col = (
        notebook.y_column
        if isinstance(notebook.y_column, str)
        else notebook.y_column[0]
    )

    conf_interval: bool | ConfIntervalConfig = False
    resolved_ci = getattr(notebook, "_resolved_ci", None)
    if hasattr(notebook, "fit_result"):
        conf_interval = _normalize_conf_interval_settings(
            notebook.fit_result.confidence.settings
        )
    elif isinstance(resolved_ci, ConfIntervalAPI | ConfIntervalConfig):
        conf_interval = _normalize_conf_interval_settings(resolved_ci)

    return UnifiedFittingConfig(
        components=components,
        minimizer=notebook.settings_solver_models.minimizer,
        optimizer=notebook.settings_solver_models.optimizer,
        column=ColumnConfig(x=notebook.x_column, y=y_col),
        global_=notebook.global_,
        conf_interval=conf_interval,
    )


def export_notebook_config_toml(
    config: UnifiedFittingConfig,
    path: Path | str,
    *,
    force: bool = False,
) -> None:
    """Serialize a config to v2 TOML on disk.

    Args:
        config: Configuration to export.
        path: Destination ``.toml`` path.
        force: Overwrite destination if it already exists.

    Raises:
        FileExistsError: If the destination exists and ``force=False``.
    """
    dest = Path(path)
    if dest.exists() and not force:
        msg = f"'{dest}' already exists. Pass force=True to overwrite."
        raise FileExistsError(msg)

    components = [
        component.model_dump(exclude_none=True) for component in config.components
    ]
    out: dict[str, object] = {
        "components": components,
        "minimizer": config.minimizer.model_dump(exclude_none=True)
        if config.minimizer
        else {},
        "optimizer": config.optimizer.model_dump(exclude_none=True)
        if config.optimizer
        else {},
    }
    with dest.open("wb") as fh:
        tomli_w.dump(out, fh)


def load_notebook_config(path: Path | str) -> UnifiedFittingConfig:
    """Load and validate a v2 TOML/JSON configuration file.

    Args:
        path: Path to ``.toml`` or ``.json`` file.

    Returns:
        UnifiedFittingConfig: Validated configuration model.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file extension is unsupported.
    """
    try:
        import tomllib  # noqa: PLC0415
    except ImportError:
        import tomli as tomllib  # type: ignore[no-redef]  # noqa: PLC0415

    src = Path(path)
    if not src.exists():
        msg = f"Config file not found: '{src}'"
        raise FileNotFoundError(msg)

    if src.suffix == ".toml":
        with src.open("rb") as fh:
            raw = tomllib.load(fh)
    elif src.suffix == ".json":
        with src.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
    else:
        msg = f"Unsupported config format: '{src.suffix}'. Use .toml or .json."
        raise ValueError(msg)

    return UnifiedFittingConfig.model_validate(raw)

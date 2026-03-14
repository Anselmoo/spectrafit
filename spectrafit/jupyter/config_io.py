"""Configuration I/O helpers for the Jupyter notebook integration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
import tomli_w

from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import normalize_conf_interval_value


if TYPE_CHECKING:
    from collections.abc import Mapping

    from spectrafit.jupyter.core import SpectraFitNotebook


type TomlScalar = str | int | float | bool | None
type TomlValue = TomlScalar | list["TomlValue"] | dict[str, "TomlValue"]
type TomlDocument = dict[str, TomlValue]


def _normalize_conf_interval_settings(
    settings: bool | Mapping[str, object] | ConfIntervalConfig,
) -> bool | ConfIntervalConfig:
    """Normalize confidence interval settings into UnifiedFittingConfig shape."""
    normalized = normalize_conf_interval_value(settings)
    return normalized if normalized is not None else False


def _resolve_notebook_y_column_input(
    df: pd.DataFrame,
    config: UnifiedFittingConfig,
) -> str | list[str]:
    """Resolve the canonical notebook y-column input from config and dataframe."""
    if config.context.mode == FittingMode.STANDARD:
        return config.y_column

    dataframe_y_columns = [
        str(column) for column in df.columns if str(column) != config.x_column
    ]
    if config.y_column not in dataframe_y_columns:
        msg = (
            f"Notebook config data.y_col='{config.y_column}' is not present in the "
            f"dataframe y-columns {dataframe_y_columns}."
        )
        raise ValueError(msg)

    if len(dataframe_y_columns) == 1:
        return config.y_column

    if len(dataframe_y_columns) != config.context.n_datasets:
        msg = (
            "Notebook config context.n_datasets="
            f"{config.context.n_datasets} does not match dataframe y-columns="
            f"{len(dataframe_y_columns)}."
        )
        raise ValueError(msg)

    if dataframe_y_columns[0] != config.y_column:
        msg = (
            f"Notebook config data.y_col='{config.y_column}' must match the first "
            f"dataframe y-column '{dataframe_y_columns[0]}' for notebook "
            "roundtrip reconstruction."
        )
        raise ValueError(msg)

    return dataframe_y_columns


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
        x_column=config.x_column,
        y_column=_resolve_notebook_y_column_input(df=df, config=config),
        **kwargs,
    )
    notebook.settings_solver_models = SolverModelsAPI(
        minimizer=config.minimizer,
        optimizer=config.optimizer,
    )
    notebook.n_datasets = config.context.n_datasets
    notebook.fitting_mode = config.context.mode
    notebook.preprocessing_config = (
        config.preprocessing
        if config.preprocessing is not None
        else PreprocessingConfig()
    )
    notebook.initial_components = config.components
    return notebook


def notebook_args_to_config(notebook: SpectraFitNotebook) -> UnifiedFittingConfig:
    """Convert a notebook state into ``UnifiedFittingConfig``.

    Args:
        notebook: Notebook instance with current fit state.

    Returns:
        UnifiedFittingConfig: Validated configuration matching notebook state.
    """
    components = notebook.initial_components
    y_columns = notebook.y_columns
    y_col = y_columns[0]

    conf_interval: bool | ConfIntervalConfig = False
    resolved_ci = getattr(notebook, "_resolved_ci", None)
    if hasattr(notebook, "fit_result"):
        conf_interval = _normalize_conf_interval_settings(
            notebook.fit_result.confidence.settings
        )
    elif resolved_ci is not None:
        conf_interval = _normalize_conf_interval_settings(resolved_ci)

    return UnifiedFittingConfig(
        components=components,
        minimizer=notebook.settings_solver_models.minimizer,
        optimizer=notebook.settings_solver_models.optimizer,
        column=ColumnConfig(x=notebook.x_column, y=y_col),
        context=FittingContext(
            mode=notebook.fitting_mode,
            n_datasets=notebook.n_datasets,
        ),
        conf_interval=conf_interval,
        preprocessing=notebook.preprocessing_config,
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

    out: TomlDocument = config.model_dump(  # intentional: TOML serialization boundary
        mode="json",
        exclude_none=True,
    )
    with dest.open("wb") as fh:
        tomli_w.dump(out, fh)


def load_notebook_config(path: Path | str) -> UnifiedFittingConfig:
    """Load and validate a v2 TOML/JSON/YAML configuration file.

    Args:
        path: Path to ``.toml``, ``.json``, ``.yaml``, or ``.yml`` file.

    Returns:
        UnifiedFittingConfig: Validated configuration model.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file extension is unsupported.
    """
    src = Path(path)
    if not src.exists():
        msg = f"Config file not found: '{src}'"
        raise FileNotFoundError(msg)
    return UnifiedFittingConfig.from_file(src)

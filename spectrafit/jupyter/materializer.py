"""Supported helpers for materializing SpectraFit notebooks from configs."""

from __future__ import annotations

from pathlib import Path

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.jupyter.templates.materialized_nb import write_materialized_notebook


def _default_data_path(config: UnifiedFittingConfig) -> str:
    """Infer the local notebook CSV path from a config model."""
    payload = config.model_dump(mode="json", exclude_none=True)
    data_section = payload.get("data", {})
    infile = data_section.get("infile", "data.csv")
    return Path(str(infile)).name or "data.csv"


def materialize_notebook_from_config(
    *,
    config_path: Path,
    output_path: Path,
    artifact_name: str | None = None,
    data_path: str | None = None,
    title: str | None = None,
    description: str | None = None,
) -> Path:
    """Convert a config file into an editable, materialized SpectraFit notebook."""
    config = UnifiedFittingConfig.from_file(config_path)
    notebook_data_path = data_path or _default_data_path(config)
    resolved_artifact_name = artifact_name or output_path.stem
    resolved_title = (
        title or f"{resolved_artifact_name} — Materialized SpectraFit Notebook"
    )
    resolved_description = description or (
        f"This notebook was materialized from `{config_path.name}`. Edit the embedded "
        "Python payload directly, then validate and rerun the fit without reloading the "
        "source config file at notebook runtime."
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_materialized_notebook(
        output_path=output_path,
        project_name=resolved_artifact_name,
        intro_title=resolved_title,
        intro_body=resolved_description,
        artifact_name=resolved_artifact_name,
        config=config,
        data_path=notebook_data_path,
    )
    return output_path

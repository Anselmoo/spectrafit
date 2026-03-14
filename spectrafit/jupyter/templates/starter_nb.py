"""Notebook builders for ``spectrafit init --jupyter`` and committed examples."""

from __future__ import annotations

from pathlib import Path  # noqa: TC003

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.generators.scenarios import get_synthetic_scenario
from spectrafit.jupyter.templates.materialized_nb import build_materialized_notebook
from spectrafit.jupyter.templates.materialized_nb import write_materialized_notebook


def build_example_notebook(
    *,
    example_name: str,
    description: str,
) -> dict[str, object]:
    """Build a committed, runnable example notebook rooted in ``examples/<name>``."""
    scenario = get_synthetic_scenario(example_name)
    return build_materialized_notebook(
        project_name=example_name,
        intro_title=f"{example_name} — SpectraFit Example Notebook",
        intro_body=(
            f"This user-facing notebook is the runnable companion for the "
            f"`examples/{example_name}` workflow.\n\n"
            f"{description}"
        ),
        artifact_name=example_name,
        config=scenario.to_config(),
        data_path="data.csv",
    )


def build_starter_notebook(
    project_name: str,
    config: UnifiedFittingConfig,
) -> dict[str, object]:
    """Build the starter notebook used by ``spectrafit init --jupyter``."""
    return build_materialized_notebook(
        project_name=project_name,
        intro_title=f"{project_name} — SpectraFit Getting Started",
        intro_body=(
            "This notebook gives you the new one-import SpectraFit notebook workflow. "
            "The compact `spectrafit.notebook` surface still compiles into the same "
            "canonical fit pipeline as the scaffolded CLI config, but you can start "
            "from readable `sf.read(...)`, `sf.peak(...)`, and `sf.fit(...)` cells."
        ),
        artifact_name=project_name,
        config=config,
        data_path="data.csv",
    )


def write_example_notebook(
    *,
    example_name: str,
    description: str,
    output_path: Path,
) -> None:
    """Write a committed example notebook to disk."""
    write_materialized_notebook(
        output_path=output_path,
        project_name=example_name,
        intro_title=f"{example_name} — SpectraFit Example Notebook",
        intro_body=(
            f"This user-facing notebook is the runnable companion for the "
            f"`examples/{example_name}` workflow.\n\n"
            f"{description}"
        ),
        artifact_name=example_name,
        config=get_synthetic_scenario(example_name).to_config(),
        data_path="data.csv",
    )


def write_starter_notebook(
    project_name: str,
    output_path: Path,
    config: UnifiedFittingConfig,
) -> None:
    """Serialise the starter notebook to *output_path*."""
    write_materialized_notebook(
        output_path=output_path,
        project_name=project_name,
        intro_title=f"{project_name} — SpectraFit Getting Started",
        intro_body=(
            "This notebook gives you the new one-import SpectraFit notebook workflow. "
            "The compact `spectrafit.notebook` surface still compiles into the same "
            "canonical fit pipeline as the scaffolded CLI config, but you can start "
            "from readable `sf.read(...)`, `sf.peak(...)`, and `sf.fit(...)` cells."
        ),
        artifact_name=project_name,
        config=config,
        data_path="data.csv",
    )

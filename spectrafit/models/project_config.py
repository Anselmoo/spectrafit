"""Project-level configuration model for ``spectrafit.toml``."""

from __future__ import annotations

from datetime import UTC
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


if TYPE_CHECKING:
    from pathlib import Path


class ProjectFiles(BaseModel):
    """File references for a SpectraFit project.

    Attributes:
        default_notebook: Path (relative to project root) of the Jupyter notebook.
        default_config: Path (relative to project root) of the fitting config file.
        data_dir: Sub-directory for raw data files.
        results_dir: Sub-directory for fit results.

    Examples:
        >>> pf = ProjectFiles()
        >>> pf.default_notebook
        'spectrafit_getting_started.ipynb'
    """

    model_config = ConfigDict(extra="forbid")

    default_notebook: str = "spectrafit_getting_started.ipynb"
    default_config: str = "config.toml"
    data_dir: str = "data"
    results_dir: str = "results"


class ProjectMeta(BaseModel):
    """Project metadata section of ``spectrafit.toml``.

    Attributes:
        name: Human-readable project name.
        description: Optional short description.
        spectrafit_version: SpectraFit version that created the project.
        created_at: ISO-8601 creation timestamp.
        files: Associated file paths.

    Examples:
        >>> pm = ProjectMeta(name="my_rixs")
        >>> pm.name
        'my_rixs'
    """

    model_config = ConfigDict(extra="forbid")

    name: str
    description: str = ""
    spectrafit_version: str = Field(
        default="",
        description="SpectraFit version used to create this project.",
    )
    created_at: str = Field(
        default_factory=lambda: datetime.now(tz=UTC).isoformat(timespec="seconds"),
        description="ISO-8601 creation timestamp.",
    )
    files: ProjectFiles = Field(default_factory=ProjectFiles)


class ProjectConfig(BaseModel):
    """Root model for ``spectrafit.toml`` project meta file.

    The ``spectrafit.toml`` file is created by ``spectrafit init`` and placed
    in the project root directory.  It is read by ``spectrafit jupyter`` to
    locate the default notebook.

    Attributes:
        project: Project metadata (name, version, file references).

    Examples:
        >>> pc = ProjectConfig(project=ProjectMeta(name="my_rixs"))
        >>> pc.project.name
        'my_rixs'
    """

    model_config = ConfigDict(extra="forbid")

    project: ProjectMeta

    @classmethod
    def from_toml(cls, path: Path) -> ProjectConfig:
        """Load a ProjectConfig from a TOML file.

        Args:
            path: Path to the ``spectrafit.toml`` file.

        Returns:
            Parsed :class:`ProjectConfig`.

        Raises:
            FileNotFoundError: If *path* does not exist.
            ValueError: If the TOML cannot be parsed or validated.
        """
        try:
            import tomllib  # noqa: PLC0415
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]  # noqa: PLC0415

        with path.open("rb") as fh:
            raw = tomllib.load(fh)
        return cls.model_validate(raw)

    def to_toml_dict(self) -> dict[str, object]:  # intentional: serialization boundary
        """Serialise to a plain dict suitable for ``tomli_w.dump``.

        Returns:
            Nested dict with ``project`` top-level key.
        """
        return self.model_dump()

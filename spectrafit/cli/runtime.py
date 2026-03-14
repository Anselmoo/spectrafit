"""Shared CLI runtime state and configuration loading helpers."""

from __future__ import annotations

import os

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import typer

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator

from spectrafit.cli._status import CliStatus
from spectrafit.cli._status import cli_status
from spectrafit.core.fitting_config import UnifiedFittingConfig


class StatusPrinter(Protocol):
    """Protocol for CLI status lifecycle messages."""

    def start(self) -> None:
        """Call before a fit starts."""

    def end(self) -> None:
        """Call after a fit completes."""


class CliRuntimeSettings(BaseModel):
    """Validated CLI runtime settings loaded from environment variables."""

    model_config = ConfigDict(extra="forbid")

    app_dir: Path = Field(
        default_factory=lambda: Path(typer.get_app_dir("spectrafit")),
        description="Directory for SpectraFit CLI runtime config storage.",
    )
    config_path: Path | None = Field(
        default=None,
        description="Optional fitting config path from SPECTRAFIT_CONFIG.",
    )
    default_config_name: str = Field(
        default="config.toml",
        description="Default config file name to look up under app_dir.",
    )

    @field_validator("default_config_name", mode="after")
    @classmethod
    def validate_default_config_name(cls, value: str) -> str:
        """Reject blank default config file names."""
        normalized = value.strip()
        if not normalized:
            msg = "default_config_name must not be blank"
            raise ValueError(msg)
        return normalized

    @classmethod
    def from_environment(
        cls,
        environ: dict[str, str] | os._Environ[str] | None = None,
    ) -> CliRuntimeSettings:
        """Build settings from environment variables."""
        env = os.environ if environ is None else environ
        raw: dict[str, str] = {}
        if app_dir := env.get("SPECTRAFIT_APP_DIR"):
            raw["app_dir"] = app_dir
        if config_path := env.get("SPECTRAFIT_CONFIG"):
            raw["config_path"] = config_path
        if default_config_name := env.get("SPECTRAFIT_DEFAULT_CONFIG_NAME"):
            raw["default_config_name"] = default_config_name
        return cls.model_validate(raw)

    @property
    def default_config_path(self) -> Path:
        """Return the default config file path under the CLI app dir."""
        return self.app_dir / self.default_config_name


@dataclass(slots=True)
class CliRuntime:
    """Runtime dependencies shared across CLI commands."""

    settings: CliRuntimeSettings
    status_printer: StatusPrinter

    def resolve_config_path(self, explicit_path: Path | None) -> Path:
        """Resolve config file path from explicit arg, env var, or app dir."""
        if explicit_path is not None:
            return Path(explicit_path)
        if self.settings.config_path is not None:
            return Path(self.settings.config_path)

        default_path = self.settings.default_config_path
        if default_path.exists():
            return default_path

        msg = (
            "No fitting config path provided. Pass a config file path, set "
            "SPECTRAFIT_CONFIG, or place a config file at "
            f"'{default_path}'."
        )
        raise FileNotFoundError(msg)

    def load_fitting_config(self, explicit_path: Path | None) -> UnifiedFittingConfig:
        """Load the unified fitting config from the resolved path."""
        return UnifiedFittingConfig.from_file(self.resolve_config_path(explicit_path))


def build_cli_runtime(
    *,
    status_printer: StatusPrinter | None = None,
    environ: dict[str, str] | os._Environ[str] | None = None,
) -> CliRuntime:
    """Create shared CLI runtime dependencies."""
    return CliRuntime(
        settings=CliRuntimeSettings.from_environment(environ=environ),
        status_printer=status_printer or cli_status,
    )


def get_cli_runtime(ctx: typer.Context) -> CliRuntime:
    """Return shared CLI runtime stored in Typer context state."""
    runtime = ctx.obj.get("runtime") if isinstance(ctx.obj, dict) else None
    if isinstance(runtime, CliRuntime):
        return runtime

    built_runtime = build_cli_runtime()
    ctx.obj = {"runtime": built_runtime}
    return built_runtime


__all__ = [
    "CliRuntime",
    "CliRuntimeSettings",
    "CliStatus",
    "StatusPrinter",
    "build_cli_runtime",
    "get_cli_runtime",
]

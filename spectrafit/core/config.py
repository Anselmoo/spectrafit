"""Configuration management for SpectraFit.

This module provides unified configuration loading and validation,
with support for environment variables and configuration files.
"""

from __future__ import annotations

import os

from pathlib import Path
from typing import Any

import typer

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator


class FittingConfig(BaseModel):
    """Configuration model for fitting parameters.

    Attributes:
        infile (str): Input data file path.
        outfile (str): Output results file path.
        input (str): Input parameter file path.
        oversampling (bool): Enable oversampling.
        energy_start (float | None): Starting energy for fitting range.
        energy_stop (float | None): Ending energy for fitting range.
        smooth (int): Smoothing factor.
        shift (float): Energy shift to apply.
        column (list[str]): Column names for energy and intensity.
        separator (str): CSV separator character.
        decimal (str): Decimal separator character.
        header (int | None): Header row index.
        comment (str | None): Comment character for skipping lines.
        global_ (int): Global fitting mode (0=classic, 1=auto, 2=custom).
        autopeak (bool): Enable auto-peak detection.
        noplot (bool): Disable plotting.
        verbose (int): Verbosity level (0=silent, 1=table, 2=dict).

    """

    model_config = ConfigDict(
        extra="allow",  # Allow additional fields for flexibility
        validate_assignment=True,
    )

    infile: str = Field(
        ...,
        description="Filename of the spectra data",
    )
    outfile: str = Field(
        default="spectrafit_results",
        description="Filename for the export",
    )
    input: str = Field(
        default="fitting_input.toml",
        description="Filename for the input parameter file",
    )
    oversampling: bool = Field(
        default=False,
        description="Oversample the spectra by factor of 5",
    )
    energy_start: float | None = Field(
        default=None,
        description="Starting energy in eV",
    )
    energy_stop: float | None = Field(
        default=None,
        description="Ending energy in eV",
    )
    smooth: int = Field(
        default=0,
        ge=0,
        description="Number of smooth points",
    )
    shift: float = Field(
        default=0,
        description="Constant applied energy shift",
    )
    column: list[str] = Field(
        default=["0", "1"],
        description="Selected columns for energy and intensity",
    )
    separator: str = Field(
        default="\t",
        description="Type of separator",
    )
    decimal: str = Field(
        default=".",
        description="Type of decimal separator",
    )
    header: int | None = Field(
        default=None,
        description="Selected header for the dataframe",
    )
    comment: str | None = Field(
        default=None,
        description="Comment character to skip lines",
    )
    global_: int = Field(
        default=0,
        ge=0,
        le=2,
        description="Global fitting mode",
    )
    autopeak: bool = Field(
        default=False,
        description="Auto detection of peaks",
    )
    noplot: bool = Field(
        default=False,
        description="Disable plotting",
    )
    verbose: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Verbosity level",
    )

    @field_validator("column", mode="before")
    @classmethod
    def validate_column(cls, v: Any) -> list[str]:
        """Validate and convert column parameter.

        Args:
            v: Column value to validate.

        Returns:
            list[str]: Validated column list.

        """
        if v is None:
            return ["0", "1"]
        if isinstance(v, list):
            return [str(c) for c in v]
        return [str(v)]


class ConfigLoader:
    """Configuration loader with environment variable support.

    This class provides methods to load configuration from various sources
    and merge them with proper precedence.

    Precedence (highest to lowest):
    1. Direct arguments (programmatic usage)
    2. Environment variables
    3. Configuration file
    4. Default values

    """

    def __init__(self, app_name: str = "spectrafit") -> None:
        """Initialize ConfigLoader.

        Args:
            app_name (str): Application name for configuration directory.
                 Defaults to "spectrafit".

        """
        self.app_name = app_name
        self.config_dir = self._get_config_dir()

    def _get_config_dir(self) -> Path:
        """Get application configuration directory.

        Returns:
            Path: Path to configuration directory.

        """
        app_dir = typer.get_app_dir(self.app_name)
        config_dir = Path(app_dir)
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir

    def load_from_env(self, prefix: str = "SPECTRAFIT_") -> dict[str, Any]:
        """Load configuration from environment variables.

        Args:
            prefix (str): Prefix for environment variables.
                 Defaults to "SPECTRAFIT_".

        Returns:
            dict[str, Any]: Configuration dictionary from environment.

        """
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to lowercase
                config_key = key[len(prefix) :].lower()
                # Handle boolean values
                if value.lower() in ("true", "1", "yes"):
                    config[config_key] = True
                elif value.lower() in ("false", "0", "no"):
                    config[config_key] = False
                # Handle numeric values
                elif value.isdigit():
                    config[config_key] = int(value)
                else:
                    try:
                        config[config_key] = float(value)
                    except ValueError:
                        config[config_key] = value
        return config

    def merge_configs(
        self,
        *configs: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge multiple configuration dictionaries.

        Later dictionaries take precedence over earlier ones.

        Args:
            *configs: Variable number of configuration dictionaries.

        Returns:
            dict[str, Any]: Merged configuration dictionary.

        """
        merged = {}
        for config in configs:
            if config:
                merged.update(config)
        return merged

    def get_config_file_path(self, filename: str = "config.toml") -> Path:
        """Get path to configuration file in app directory.

        Args:
            filename (str): Configuration filename. Defaults to "config.toml".

        Returns:
            Path: Full path to configuration file.

        """
        return self.config_dir / filename

    def validate_config(self, config: dict[str, Any]) -> FittingConfig:
        """Validate configuration using Pydantic model.

        Args:
            config (dict[str, Any]): Configuration dictionary to validate.

        Returns:
            FittingConfig: Validated configuration object.

        Raises:
            ValidationError: If configuration is invalid.

        """
        return FittingConfig(**config)


def load_config(
    args: dict[str, Any] | None = None,
    use_env: bool = True,
) -> dict[str, Any]:
    """Load and merge configuration from all sources.

    Args:
        args (dict[str, Any] | None): Direct configuration arguments.
             Defaults to None.
        use_env (bool): Whether to load from environment variables.
             Defaults to True.

    Returns:
        dict[str, Any]: Merged configuration dictionary.

    """
    loader = ConfigLoader()

    # Start with empty config
    configs = []

    # Load from environment if enabled
    if use_env:
        env_config = loader.load_from_env()
        if env_config:
            configs.append(env_config)

    # Add direct args (highest precedence)
    if args:
        configs.append(args)

    # Merge all configs
    return loader.merge_configs(*configs)

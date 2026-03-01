"""Unified fitting configuration model for SpectraFit.

This module provides a single Pydantic model that captures the full fitting
configuration consumed by both the CLI and notebook interfaces.  It supports
loading from JSON, YAML, and TOML files and can produce the legacy dict
format expected by the current solver pipeline.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import tomli
import yaml

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.api.tools_model import MinimizerConfig
from spectrafit.api.tools_model import OptimizerConfig
from spectrafit.models.autopeak import PeaksDict


class ColumnConfig(BaseModel):
    """Column name configuration for the energy and intensity axes.

    Attributes:
        x: Column name for the energy / x-axis.
        y: Column name for the intensity / y-axis.
    """

    x: str = Field(default="energy", description="Column name for the x-axis")
    y: str = Field(default="intensity", description="Column name for the y-axis")


class UnifiedFittingConfig(BaseModel):
    """Unified fitting configuration consumed by CLI and notebook.

    This model captures peaks, minimizer/optimizer settings, column mapping,
    global fitting mode, and confidence-interval options in a single validated
    structure.

    Attributes:
        peaks: Nested peak parameter definitions keyed by peak index, model
            name, and parameter constraints.
        minimizer: Minimizer options forwarded to *lmfit*.
        optimizer: Optimizer options forwarded to *lmfit*.
        column: Column-name mapping for the input data.
        global_: Global fitting mode (0=none, 1=standard, 2=with-pre).
        conf_interval: Confidence-interval configuration.  ``False`` disables
            CI calculation; a dict is forwarded to *lmfit* ``conf_interval``.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    peaks: PeaksDict = Field(
        ...,
        description="Peak definitions keyed by index, model name, and parameters",
    )
    minimizer: MinimizerConfig = Field(
        default_factory=MinimizerConfig,
        description="Minimizer options forwarded to lmfit",
    )
    optimizer: OptimizerConfig = Field(
        default_factory=OptimizerConfig,
        description="Optimizer options forwarded to lmfit",
    )
    column: ColumnConfig = Field(
        default_factory=ColumnConfig,
        description="Column name mapping for the input data",
    )
    global_: int = Field(
        default=0,
        ge=0,
        le=2,
        alias="global",
        description="Global fitting mode (0=none, 1=standard, 2=with-pre)",
    )
    conf_interval: bool | dict[str, Any] = Field(
        default=False,
        description="Confidence interval config; False disables CI calculation",
    )

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def from_file(cls, path: Path) -> UnifiedFittingConfig:
        """Load configuration from a JSON, YAML, or TOML file.

        The file format is auto-detected from the extension.

        Args:
            path: Path to the configuration file.

        Returns:
            UnifiedFittingConfig: Validated configuration instance.

        Raises:
            OSError: If the file extension is not supported.
        """
        path = Path(path)

        if path.suffix == ".toml":
            with path.open("rb") as fb:
                data = tomli.load(fb)
        elif path.suffix == ".json":
            with path.open(encoding="utf-8") as ft:
                data = json.load(ft)
        elif path.suffix in {".yaml", ".yml"}:
            with path.open(encoding="utf-8") as ft:
                data = yaml.load(ft, Loader=yaml.FullLoader)
        else:
            msg = (
                f"Unsupported file format '{path.suffix}'. "
                "Supported formats are: .json, .yaml, .yml, .toml"
            )
            raise OSError(msg)

        return cls.model_validate(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UnifiedFittingConfig:
        """Create a configuration from a plain dictionary.

        This provides backward-compatible construction from the legacy dict
        format used throughout SpectraFit.

        Args:
            data: Dictionary with fitting configuration keys.

        Returns:
            UnifiedFittingConfig: Validated configuration instance.
        """
        return cls.model_validate(data)

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def to_solver_args(self) -> dict[str, Any]:
        """Convert to the dict format expected by the current solver pipeline.

        Returns:
            dict[str, Any]: Solver-compatible argument dictionary containing
                ``peaks``, ``minimizer``, ``optimizer``, ``column``,
                ``global_``, and ``conf_interval`` keys.
        """
        return {
            "peaks": self.peaks,
            "minimizer": self.minimizer.model_dump(),
            "optimizer": self.optimizer.model_dump(),
            "column": [self.column.x, self.column.y],
            "global_": self.global_,
            "conf_interval": self.conf_interval,
        }

"""Unified fitting configuration model for SpectraFit.

This module provides a single Pydantic model that captures the full fitting
configuration consumed by both the CLI and notebook interfaces. Raw legacy and
structured config ingress is normalized at the adapter boundary before this
typed model composes and validates the canonical runtime surface.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from spectrafit.core.config_loader import load_config_payload
from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.bundle import build_composite_bundle
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.mcmc_config import MCMCConfig
from spectrafit.models.meta_config import MetaConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.preprocessing_config import PreprocessingConfig
from spectrafit.models.solver_config import ConfIntervalConfig
from spectrafit.models.solver_config import MinimizerConfig
from spectrafit.models.solver_config import OptimizerConfig


if TYPE_CHECKING:
    from pathlib import Path


class ColumnConfig(BaseModel):
    """Column name configuration for the energy and intensity axes.

    Attributes:
        x: Column name for the energy / x-axis.
        y: Column name for the intensity / y-axis.
    """

    x: str = Field(default="energy", description="Column name for the x-axis")
    y: str = Field(default="intensity", description="Column name for the y-axis")

    @field_validator("x", "y", mode="before")
    @classmethod
    def coerce_to_str(cls, v: object) -> str:
        """Coerce numeric column indices to strings.

        Args:
            v: Column value to coerce.

        Returns:
            str: String representation of the column value.
        """
        return str(v)


class UnifiedFittingConfig(BaseModel):
    """Unified fitting configuration consumed by CLI and notebook.

    The v2 design philosophy: **the structured config file is the user interface.**
    Fitting parameters, data loading, and pre-processing are all declared in the
    ``[data]``, ``[preprocessing]``, and ``[[components]]`` sections of a TOML/JSON
    file.  The CLI is a minimal launcher; no flat per-parameter flags exist.

    Attributes:
        components: Typed component definitions (v2 canonical format).
        minimizer: Minimizer options forwarded to *lmfit*.
        optimizer: Optimizer options forwarded to *lmfit*.
        column: Column-name mapping for the input data. This remains as a
            synchronized compatibility view, but ``data`` owns column metadata
            whenever a ``[data]`` block is present.
        context: Canonical typed fitting context carrying fitting mode ownership.
            Legacy ``global`` / ``global_`` inputs are normalized into this field.
        conf_interval: Confidence-interval configuration.  ``False`` disables
            CI calculation; enabled settings are normalized into
            :class:`~spectrafit.models.solver_config.ConfIntervalConfig`.
        meta: Optional project metadata (``[meta]`` section in TOML).
        data: Data-loading configuration (``[data]`` section in TOML).
        preprocessing: Pre-processing configuration (``[preprocessing]`` section).
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    components: list[Component] = Field(
        default_factory=list,
        description="Typed component definitions (v2 canonical input).",
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
        description=(
            "Column name mapping — synchronized compatibility view over data-owned "
            "column metadata."
        ),
    )
    context: FittingContext = Field(
        default_factory=FittingContext,
        description=(
            "Canonical typed fitting context. Legacy global/global_ inputs are "
            "normalized into this field at the adapter boundary."
        ),
    )
    conf_interval: bool | ConfIntervalConfig = Field(
        default=False,
        description="Confidence interval config; False disables CI calculation",
    )
    global_fitting_config: GlobalFittingConfig | None = Field(
        default=None,
        description="Optional global fitting config with shared parameters and weights",
    )
    mcmc: MCMCConfig | None = Field(
        default=None,
        description=(
            "MCMC sampling config; required when optimizer.method = 'emcee'. "
            "Passed to lmfit.Minimizer.emcee() as keyword arguments."
        ),
    )

    # ------------------------------------------------------------------
    # v2 structured sub-models
    # ------------------------------------------------------------------
    meta: MetaConfig | None = Field(
        default=None,
        description="Project metadata ([meta] section in TOML)",
    )
    data: DataConfig | None = Field(
        default=None,
        description="Data-loading configuration ([data] section in TOML)",
    )
    preprocessing: PreprocessingConfig | None = Field(
        default=None,
        description="Pre-processing configuration ([preprocessing] section in TOML)",
    )

    # Backward-compat @property accessors for frozen modules.
    # None of these appear in model_dump() / model_json_schema().

    @property
    def infile(self) -> Path | None:
        """Path to the input data file (delegates to ``data.infile``)."""
        return self.data.infile if self.data else None

    @property
    def separator(self) -> str:
        """CSV column separator character (delegates to ``data.separator``)."""
        return self.data.separator if self.data else r"\s+"

    @property
    def header(self) -> int | None:
        """Header row index (delegates to ``data.header``)."""
        return self.data.header if self.data else 0

    @property
    def decimal(self) -> str:
        """Decimal character (delegates to ``data.decimal``)."""
        return self.data.decimal if self.data else "."

    @property
    def comment(self) -> str | None:
        """Comment character (delegates to ``data.comment``)."""
        return self.data.comment if self.data else None

    def with_data_infile(self, infile: Path | str) -> UnifiedFittingConfig:
        """Return a copy of the config with ``data.infile`` owned canonically.

        Args:
            infile: New input-data location to embed in the returned config.

        Returns:
            UnifiedFittingConfig: Deep copy with a typed :class:`DataConfig`
                carrying the requested ``infile``.
        """
        from spectrafit.models.data_config import DataConfig  # noqa: PLC0415

        return self.model_copy(
            update={"data": DataConfig.from_unified(self, infile=infile)},
            deep=True,
        )

    @property
    def x_column(self) -> str:
        """Canonical x-column name owned by ``data`` when available."""
        return self.data.x_col if self.data is not None else self.column.x

    @property
    def y_column(self) -> str:
        """Canonical y-column name owned by ``data`` when available."""
        return self.data.y_col if self.data is not None else self.column.y

    @property
    def energy_start(self) -> float | None:
        """Lower energy bound (delegates to ``preprocessing.energy_start``)."""
        return self.preprocessing.energy_start if self.preprocessing else None

    @property
    def energy_stop(self) -> float | None:
        """Upper energy bound (delegates to ``preprocessing.energy_stop``)."""
        return self.preprocessing.energy_stop if self.preprocessing else None

    @property
    def smooth(self) -> int:
        """Smoothing window size (delegates to ``preprocessing.smooth``)."""
        return self.preprocessing.smooth if self.preprocessing else 0

    @property
    def shift(self) -> float:
        """Constant energy offset in eV (delegates to ``preprocessing.shift``)."""
        return self.preprocessing.shift if self.preprocessing else 0.0

    @property
    def oversampling(self) -> bool:
        """Oversampling flag (delegates to ``preprocessing.oversampling``)."""
        return self.preprocessing.oversampling if self.preprocessing else False

    # ------------------------------------------------------------------
    # Compatibility accessors — derived from canonical context
    # ------------------------------------------------------------------

    @property
    def global_(self) -> FittingMode:
        """Compatibility alias exposing fitting mode from ``context``.

        Returns:
            FittingMode: Canonical fitting mode derived from ``context``.
        """
        return self.context.mode

    @model_validator(mode="before")
    @classmethod
    def normalize_v2_input(cls, data: object) -> object:
        """Normalise v2 input before field validation.

        Args:
            data: Raw input data before field coercion.

        Returns:
            object: Normalized dict ready for field validation, or original value
                if input is not a dict.
        """
        if not isinstance(data, Mapping):
            return data
        from spectrafit.adapters.unified_config_input import (  # noqa: PLC0415
            normalize_strict_unified_config_input,
        )

        return normalize_strict_unified_config_input(data)

    @model_validator(mode="after")
    def validate_components_non_empty(self) -> UnifiedFittingConfig:
        """Validate that at least one component is defined.

        Returns:
            UnifiedFittingConfig: Self if validation passes.

        Raises:
            ValueError: If no components are provided for a fit-capable config.
        """
        if self.components:
            return self

        is_preprocessing_only = (
            self.preprocessing is not None
            and self.minimizer is None
            and self.optimizer is None
        )
        if is_preprocessing_only:
            return self

        if not self.components:
            msg = "At least one component must be defined using v2 'components' format."
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def sync_column_compatibility_view(self) -> UnifiedFittingConfig:
        """Keep the legacy ``column`` view synchronized with data-owned columns."""
        if self.data is None:
            return self

        synced_column = ColumnConfig(x=self.data.x_col, y=self.data.y_col)
        if self.column != synced_column:
            self.column = synced_column
        return self

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def _validate_mapping(cls, data: Mapping[str, object]) -> UnifiedFittingConfig:
        """Validate a raw config mapping through the canonical ingress path."""
        return cls.model_validate(data)

    @classmethod
    def _validate_legacy_mapping(
        cls, data: Mapping[str, object]
    ) -> UnifiedFittingConfig:
        """Validate a legacy mapping through the explicit compatibility path."""
        from spectrafit.adapters.unified_config_input import (  # noqa: PLC0415
            normalize_unified_config_input,
        )

        normalized = normalize_unified_config_input(
            data, allow_optimizer_passthrough=True
        )
        return cls.model_validate(normalized)

    @classmethod
    def from_file(cls, path: Path | str) -> UnifiedFittingConfig:
        """Load configuration from a JSON, YAML, or TOML file.

        The file format is auto-detected from the extension.

        Args:
            path: Path to the configuration file.

        Returns:
            UnifiedFittingConfig: Validated configuration instance.

        Raises:
            OSError: If the file extension is not supported.
        """
        return cls._validate_mapping(load_config_payload(path))

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> UnifiedFittingConfig:
        """Create a configuration from a plain dictionary.

        This strict entry point accepts canonical v2 configuration shapes only.
        Legacy aliases must use :meth:`from_legacy_dict`.

        Args:
            data: Mapping with fitting configuration keys.

        Returns:
            UnifiedFittingConfig: Validated configuration instance.
        """
        return cls._validate_mapping(data)

    @classmethod
    def from_legacy_file(cls, path: Path | str) -> UnifiedFittingConfig:
        """Load a legacy config file through the explicit compatibility path.

        Args:
            path: Path to the legacy configuration file.

        Returns:
            UnifiedFittingConfig: Validated configuration instance.
        """
        return cls._validate_legacy_mapping(load_config_payload(path))

    @classmethod
    def from_legacy_dict(cls, data: Mapping[str, object]) -> UnifiedFittingConfig:
        """Create a config from a legacy mapping via the compatibility adapter.

        Args:
            data: Mapping with legacy v1 or compatibility-shim keys.

        Returns:
            UnifiedFittingConfig: Validated configuration instance.
        """
        return cls._validate_legacy_mapping(data)

    # ------------------------------------------------------------------
    # Conversion helpers
    # ------------------------------------------------------------------

    def build_composite_model(self) -> CompositeModelBundle:
        """Build a :class:`CompositeModelBundle` from the component list.

        This is the v2 entry point for constructing the lmfit model graph.
        It replaces the nested ``define_parameters*`` loops in
        :class:`~spectrafit.models.parameter_builder.ParameterBuilder`.

        Returns:
            CompositeModelBundle: Ready-to-fit composite model with all
                component lmfit models composed via ``+``, parameters
                populated from :attr:`components`, and a :attr:`parts`
                mapping for per-component decomposition.

        Examples:
            >>> from spectrafit.core.fitting_config import UnifiedFittingConfig
            >>> cfg = UnifiedFittingConfig(components=[{
            ...     "id": "p1",
            ...     "model": "gaussian",
            ...     "parameters": {
            ...         "amplitude": {"value": 1.0, "min": 0, "max": 2, "vary": True},
            ...         "center": {"value": 0.0, "min": -1, "max": 1, "vary": True},
            ...         "fwhmg": {"value": 0.5, "min": 0.1, "max": 2.0, "vary": True},
            ...     },
            ... }])
            >>> bundle = cfg.build_composite_model()
            >>> "p1_amplitude" in bundle.params
            True
        """
        return build_composite_bundle(self.components)

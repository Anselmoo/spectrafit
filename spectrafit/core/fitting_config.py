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
from pydantic import computed_field
from pydantic import field_validator
from pydantic import model_validator

from spectrafit.api.tools_model import MinimizerConfig
from spectrafit.api.tools_model import OptimizerConfig
from spectrafit.models.bundle import CompositeModelBundle
from spectrafit.models.bundle import build_composite_bundle
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.global_fitting import GlobalMode
from spectrafit.models.mcmc_config import MCMCConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.types import PeaksDict


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
    def coerce_to_str(cls, v: Any) -> str:
        """Coerce numeric column indices to strings.

        Args:
            v: Column value to coerce.

        Returns:
            str: String representation of the column value.
        """
        return str(v)


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
        global_: Global fitting mode — ``GlobalMode.NONE`` (0) for standard
            single-dataset fits; ``GlobalMode.STANDARD`` (1) or
            ``GlobalMode.WITH_PRE`` (2) for multi-dataset global fitting.
        conf_interval: Confidence-interval configuration.  ``False`` disables
            CI calculation; a dict is forwarded to *lmfit* ``conf_interval``.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    peaks: PeaksDict | None = Field(
        default=None,
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
    global_: GlobalMode = Field(
        default=GlobalMode.NONE,
        alias="global",
        description="Global fitting mode (0=none, 1=standard, 2=with-pre)",
    )
    conf_interval: bool | dict[str, Any] = Field(
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
    # Data-loading fields (consumed by DataConfig / load_data)
    # ------------------------------------------------------------------
    infile: Path | None = Field(
        default=None,
        description="Path to the input data file",
    )
    separator: str = Field(
        default=r"\s+",
        description="Column separator forwarded to pandas.read_csv",
    )
    header: int | None = Field(
        default=0,
        description="Row index to use as column header; None means no header",
    )
    decimal: str = Field(
        default=".",
        description="Decimal point character",
    )
    comment: str | None = Field(
        default=None,
        description="Character marking comment lines; None disables comment parsing",
    )

    # ------------------------------------------------------------------
    # Pre-processing fields (consumed by PreProcessing)
    # ------------------------------------------------------------------
    energy_start: float | None = Field(
        default=None,
        description="Lower bound of the energy range to fit",
    )
    energy_stop: float | None = Field(
        default=None,
        description="Upper bound of the energy range to fit",
    )
    shift: float = Field(
        default=0.0,
        description="Constant energy shift applied before fitting",
    )
    oversampling: bool = Field(
        default=False,
        description="Whether to 5x oversample the data before fitting",
    )
    smooth: int = Field(
        default=0,
        description="Box-car smoothing window size (0 = disabled)",
    )

    # ------------------------------------------------------------------
    # Computed fields — derived from peaks and global_
    # ------------------------------------------------------------------

    @computed_field  # type: ignore[prop-decorator]
    @property
    def components(self) -> list[Component]:
        """Return typed :class:`Component` list.

        Prefers the v2 ``[[components]]`` input format when present
        (stored in ``model_extra["__v2_components__"]`` by
        :meth:`migrate_v1_format`); falls back to auto-migrating the legacy
        ``peaks`` dict.

        Returns:
            list[Component]: One Component per fitting component.
        """
        raw = (self.model_extra or {}).get("__v2_components__")
        if raw is not None:
            return [Component.model_validate(c) for c in raw]
        if not self.peaks:
            return []
        comps: list[Component] = []
        for peak_id, model_spec in self.peaks.items():
            for model_name, param_spec in model_spec.items():
                params = {
                    field_name: FitParameter(**constraint)  # type: ignore[arg-type]
                    for field_name, constraint in param_spec.items()
                }
                comps.append(Component(id=peak_id, model=model_name, parameters=params))
        return comps

    @computed_field  # type: ignore[prop-decorator]
    @property
    def context(self) -> FittingContext:
        """Derive :class:`FittingContext` from the ``global_`` mode flag.

        Returns:
            FittingContext: Typed fitting context with mode and n_datasets
                derived from the legacy integer flag.
        """
        return FittingContext.from_global_int(int(self.global_))

    @classmethod
    def _migrate_v2_format(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Translate v2 ``[[components]]`` input to internal representation.

        Handles the prototype schema::

            [[components]]
            id    = "p1"
            model = "gaussian"
            [components.parameters]
            amplitude = { value = 1.0, bounds = [0.0, 3.0], vary = true }

            [data]
            infile = "synth.csv"
            x_col  = "energy"
            y_col  = "intensity"

            [solver]
            method     = "leastsq"
            max_nfev   = 1000
            nan_policy = "propagate"
            calc_covar = true

        Args:
            data: Raw input dict containing a ``components`` list.

        Returns:
            dict: Normalised dict ready for field validation.
        """
        data = dict(data)
        data["__v2_components__"] = data.pop("components")

        if "data" in data:
            d = data.pop("data")
            data.setdefault("infile", d.get("infile"))
            data.setdefault(
                "column",
                {"x": d.get("x_col", "energy"), "y": d.get("y_col", "intensity")},
            )

        if "solver" in data:
            s = data.pop("solver")
            data.setdefault(
                "minimizer",
                {
                    "nan_policy": s.get("nan_policy", "propagate"),
                    "calc_covar": s.get("calc_covar", True),
                },
            )
            data.setdefault(
                "optimizer",
                {"method": s.get("method", "leastsq"), "max_nfev": s.get("max_nfev")},
            )

        for key in ("schema_version", "config_type", "meta"):
            data.pop(key, None)

        return data

    @classmethod
    def _migrate_v1_full_wrapper(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Unwrap ``{"fitting": {...}, "settings": {...}}`` (v1 Pattern 1).

        Args:
            data: Raw input dict containing a top-level ``fitting`` key.

        Returns:
            dict: Flattened dict with peaks/minimizer/optimizer at root.
        """
        fitting = data["fitting"]
        result: dict[str, Any] = {}
        if "settings" in data:
            result |= data["settings"]
        if "peaks" in fitting:
            result["peaks"] = fitting["peaks"]
        params = fitting.get("parameters", {})
        for key in ("minimizer", "optimizer"):
            if key in params:
                result[key] = params[key]
        result.update(
            {k: v for k, v in data.items() if k not in ("fitting", "settings")}
        )
        return result

    @classmethod
    def _migrate_v1_inner(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Unwrap ``{"parameters": {...}, "peaks": {...}}`` (v1 Pattern 2).

        Args:
            data: Raw input dict with a ``parameters`` wrapper around
                minimizer/optimizer keys.

        Returns:
            dict: Flattened dict with minimizer/optimizer hoisted to root.
        """
        params = data["parameters"]
        result = {k: v for k, v in data.items() if k != "parameters"}
        for key in ("minimizer", "optimizer"):
            if key in params:
                result[key] = params[key]
        return result

    @model_validator(mode="before")
    @classmethod
    def migrate_v1_format(cls, data: Any) -> Any:
        """Unwrap v1.x input file format before field validation.

        Handles two legacy patterns:

        **Pattern 1 — full file wrapper** (``from_file`` path):

        .. code-block:: json

           {"fitting": {"parameters": {"minimizer": …, "optimizer": …},
                        "peaks": {"1": {…}}},
            "settings": {"column": […], "infile": "…", …}}

        **Pattern 2 — inner ``fitting`` dict** (``from_dict`` called with
        the pre-extracted ``fitting`` section):

        .. code-block:: json

           {"parameters": {"minimizer": …, "optimizer": …},
            "peaks": {"1": {…}}, "description": {…}}

        Both patterns are flattened so that ``peaks``, ``minimizer``, and
        ``optimizer`` appear at the top level as ``UnifiedFittingConfig``
        expects.  ``settings`` keys (``infile``, ``column``, …) are merged
        at the top level so the ``_raw_args`` contract in ``FittingPipeline``
        still works.

        Args:
            data: Raw input data before field coercion.

        Returns:
            Any: Normalised dict ready for field validation, or the original
            value if not a dict (Pydantic handles the type error downstream).
        """
        if not isinstance(data, dict):
            return data

        if isinstance(data.get("components"), list):
            return cls._migrate_v2_format(data)

        if "fitting" in data:
            return cls._migrate_v1_full_wrapper(data)

        if "parameters" in data and "peaks" in data and "minimizer" not in data:
            return cls._migrate_v1_inner(data)

        return data

    @field_validator("column", mode="before")
    @classmethod
    def coerce_column(cls, v: Any) -> Any:
        """Coerce list/tuple column input to ColumnConfig-compatible dict.

        Accepts the legacy ``["x_col", "y_col"]`` list format produced by the
        CLI argument parser and converts it to ``{"x": ..., "y": ...}`` so that
        Pydantic can instantiate ``ColumnConfig`` normally.

        Args:
            v: Raw column value — either a ``list``/``tuple`` of two strings,
               a ``dict`` (passed through), or a ``ColumnConfig`` instance.

        Returns:
            Any: Dict suitable for ``ColumnConfig`` construction, or the original
            value if it is already a dict/instance.
        """
        if isinstance(v, (list, tuple)) and len(v) >= 2:  # noqa: PLR2004
            return {"x": str(v[0]), "y": str(v[1])}
        return v

    @field_validator("peaks", mode="before")
    @classmethod
    def validate_peak_keys(cls, v: Any) -> Any:
        """Reject peaks dict entries with non-positive-integer string keys.

        Valid keys are decimal digit strings whose integer value is >= 1
        (e.g. ``"1"``, ``"2"``, ``"10"``).  Keys like ``"0"``, ``"foo"``,
        or ``"-1"`` raise ``ValueError``.

        Args:
            v: Raw peaks value before field coercion.

        Returns:
            Any: The unchanged value if all keys are valid.

        Raises:
            ValueError: If any key is not a positive-integer string.
        """
        if isinstance(v, dict):
            for k in v:
                if not (isinstance(k, str) and k.isdigit() and int(k) >= 1):
                    msg = (
                        f"Peak key {k!r} is invalid. "
                        "Keys must be positive integer strings (e.g. '1', '2', '10')."
                    )
                    raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_peaks_non_empty(self) -> UnifiedFittingConfig:
        """Validate that at least one component or peak is defined.

        Accepts either:
        - v2 ``[[components]]`` format (``__v2_components__`` in model_extra)
        - v1 ``peaks`` dict (non-empty)

        Returns:
            UnifiedFittingConfig: Self if validation passes.

        Raises:
            ValueError: If neither components nor peaks are provided.
        """
        has_v2 = bool((self.model_extra or {}).get("__v2_components__"))
        if not has_v2 and not self.peaks:
            msg = (
                "At least one component must be defined — use 'peaks' (v1) "
                "or '[[components]]' (v2) format."
            )
            raise ValueError(msg)
        return self

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

    def build_composite_model(self) -> CompositeModelBundle:
        """Build a :class:`CompositeModelBundle` from the component list.

        This is the v2 entry point for constructing the lmfit model graph.
        It replaces the nested ``define_parameters*`` loops in
        :class:`~spectrafit.models.model_parameters.ModelParameters`.

        Returns:
            CompositeModelBundle: Ready-to-fit composite model with all
                component lmfit models composed via ``+``, parameters
                populated from :attr:`components`, and a :attr:`parts`
                mapping for per-component decomposition.

        Examples:
            >>> from spectrafit.core.fitting_config import UnifiedFittingConfig
            >>> peaks = {"1": {"gaussian": {
            ...     "amplitude": {"value": 1.0, "min": 0, "max": 2, "vary": True},
            ...     "center": {"value": 0.0, "min": -1, "max": 1, "vary": True},
            ...     "fwhmg": {"value": 0.5, "min": 0.1, "max": 2.0, "vary": True},
            ... }}}
            >>> cfg = UnifiedFittingConfig(peaks=peaks)
            >>> bundle = cfg.build_composite_model()
            >>> "p1_amplitude" in bundle.params
            True
        """
        return build_composite_bundle(self.components)

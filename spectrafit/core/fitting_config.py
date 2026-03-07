"""Unified fitting configuration model for SpectraFit.

This module provides a single Pydantic model that captures the full fitting
configuration consumed by both the CLI and notebook interfaces.  It supports
loading from JSON, YAML, and TOML files and can produce the legacy dict
format expected by the current solver pipeline.
"""

from __future__ import annotations

import json

from pathlib import Path

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
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.global_fitting import GlobalFittingConfig
from spectrafit.models.global_fitting import GlobalMode
from spectrafit.models.mcmc_config import MCMCConfig
from spectrafit.models.meta_config import MetaConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.preprocessing_config import PreprocessingConfig
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
    def coerce_to_str(cls, v: object) -> str:
        """Coerce numeric column indices to strings.

        Args:
            v: Column value to coerce.

        Returns:
            str: String representation of the column value.
        """
        return str(v)


# Keys that belong in the [data] section of a v2 TOML.
_DATA_KEYS: frozenset[str] = frozenset(
    {"infile", "separator", "header", "decimal", "comment"}
)

# Keys that belong in the [preprocessing] section of a v2 TOML.
_PREPROC_KEYS: frozenset[str] = frozenset(
    {"energy_start", "energy_stop", "smooth", "shift", "oversampling"}
)


class UnifiedFittingConfig(BaseModel):
    """Unified fitting configuration consumed by CLI and notebook.

    The v2 design philosophy: **the structured config file is the user interface.**
    Fitting parameters, data loading, and pre-processing are all declared in the
    ``[data]``, ``[preprocessing]``, and ``[[components]]`` sections of a TOML/JSON
    file.  The CLI is a minimal launcher; no flat per-parameter flags exist.

    Attributes:
        peaks: Nested peak parameter definitions keyed by peak index, model
            name, and parameter constraints (v1 format, still supported).
        minimizer: Minimizer options forwarded to *lmfit*.
        optimizer: Optimizer options forwarded to *lmfit*.
        column: Column-name mapping for the input data (compat bridge for
            frozen preprocessing / model_parameters modules).
        global_: Global fitting mode — ``GlobalMode.NONE`` (0) for standard
            single-dataset fits; ``GlobalMode.STANDARD`` (1) or
            ``GlobalMode.WITH_PRE`` (2) for multi-dataset global fitting.
        conf_interval: Confidence-interval configuration.  ``False`` disables
            CI calculation; a dict is forwarded to *lmfit* ``conf_interval``.
        meta: Optional project metadata (``[meta]`` section in TOML).
        data: Data-loading configuration (``[data]`` section in TOML).
        preprocessing: Pre-processing configuration (``[preprocessing]`` section).
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
        description="Column name mapping — compat bridge for frozen modules",
    )
    global_: GlobalMode = Field(
        default=GlobalMode.NONE,
        alias="global",
        description="Global fitting mode (0=none, 1=standard, 2=with-pre)",
    )
    conf_interval: bool | dict[str, object] = Field(
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
    def _migrate_v2_format(cls, data: dict[str, object]) -> dict[str, object]:
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

        # Keep the `data` dict in place — Pydantic will parse it as DataConfig.
        # We also populate `column` for the frozen-module compat bridge.
        if isinstance(data.get("data"), dict):
            d = data["data"]
            if not isinstance(d, dict):
                msg = "Expected 'data' to be a dict"
                raise TypeError(msg)
            data.setdefault(
                "column",
                {"x": d.get("x_col", "energy"), "y": d.get("y_col", "intensity")},
            )

        if "solver" in data:
            s = data.pop("solver")
            if not isinstance(s, dict):
                msg = "Expected 'solver' to be a dict"
                raise TypeError(msg)
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

        # Drop non-model metadata keys; `meta` stays → Pydantic parses as MetaConfig.
        for key in ("schema_version", "config_type"):
            data.pop(key, None)

        return data

    @classmethod
    def _migrate_v1_full_wrapper(cls, data: dict[str, object]) -> dict[str, object]:
        """Unwrap ``{"fitting": {...}, "settings": {...}}`` (v1 Pattern 1).

        Args:
            data: Raw input dict containing a top-level ``fitting`` key.

        Returns:
            dict: Flattened dict with peaks/minimizer/optimizer at root.
        """
        fitting = data["fitting"]
        result: dict[str, object] = {}
        if "settings" in data:
            settings = data["settings"]
            if isinstance(settings, dict):
                result |= settings
        if isinstance(fitting, dict):
            if "peaks" in fitting:
                result["peaks"] = fitting["peaks"]
            params = fitting.get("parameters", {})
            if isinstance(params, dict):
                for key in ("minimizer", "optimizer"):
                    if key in params:
                        result[key] = params[key]
        result.update(
            {k: v for k, v in data.items() if k not in ("fitting", "settings")}
        )
        return result

    @classmethod
    def _migrate_v1_inner(cls, data: dict[str, object]) -> dict[str, object]:
        """Unwrap ``{"parameters": {...}, "peaks": {...}}`` (v1 Pattern 2).

        Args:
            data: Raw input dict with a ``parameters`` wrapper around
                minimizer/optimizer keys.

        Returns:
            dict: Flattened dict with minimizer/optimizer hoisted to root.
        """
        params = data["parameters"]
        result = {k: v for k, v in data.items() if k != "parameters"}
        if isinstance(params, dict):
            for key in ("minimizer", "optimizer"):
                if key in params:
                    result[key] = params[key]
        return result

    @classmethod
    def _coerce_flat_data_keys(cls, data: dict[str, object]) -> dict[str, object]:
        """Coerce flat data keys into a ``data`` sub-dict.

        Args:
            data: Mutable normalised dict (v1 or v2 flat form).

        Returns:
            dict: Updated dict, potentially with a new ``data`` key.
        """
        if isinstance(data.get("data"), dict):
            return data
        flat_data: dict[str, object] = {}
        for k in list(data):
            if k in _DATA_KEYS:
                flat_data[k] = data.pop(k)
        if flat_data:
            col = data.get("column", [])
            if isinstance(col, list) and len(col) >= 2:  # noqa: PLR2004
                flat_data.setdefault("x_col", str(col[0]))
                flat_data.setdefault("y_col", str(col[1]))
            data["data"] = flat_data
        return data

    @classmethod
    def _coerce_flat_preproc_keys(cls, data: dict[str, object]) -> dict[str, object]:
        """Coerce flat preprocessing keys into a ``preprocessing`` sub-dict.

        Args:
            data: Mutable normalised dict.

        Returns:
            dict: Updated dict, potentially with a new ``preprocessing`` key.
        """
        if isinstance(data.get("preprocessing"), dict):
            return data
        flat_preproc: dict[str, object] = {}
        for k in list(data):
            if k in _PREPROC_KEYS:
                flat_preproc[k] = data.pop(k)
        if flat_preproc:
            data["preprocessing"] = flat_preproc
        return data

    @model_validator(mode="before")
    @classmethod
    def migrate_v1_format(cls, data: object) -> object:
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

        Flat data / pre-processing keys are then coerced into their respective
        sub-models (``data`` / ``preprocessing``) so that compat ``@property``
        accessors work correctly.

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
            data = cls._migrate_v1_full_wrapper(data)
        elif "parameters" in data and "peaks" in data and "minimizer" not in data:
            data = cls._migrate_v1_inner(data)

        data = cls._coerce_flat_data_keys(data)
        return cls._coerce_flat_preproc_keys(data)

    @field_validator("column", mode="before")
    @classmethod
    def coerce_column(cls, v: object) -> object:
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
    def validate_peak_keys(cls, v: object) -> object:
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
                raw: object = tomli.load(fb)
        elif path.suffix == ".json":
            with path.open(encoding="utf-8") as ft:
                raw = json.load(ft)
        elif path.suffix in {".yaml", ".yml"}:
            with path.open(encoding="utf-8") as ft:
                raw = yaml.load(ft, Loader=yaml.FullLoader)
        else:
            msg = (
                f"Unsupported file format '{path.suffix}'. "
                "Supported formats are: .json, .yaml, .yml, .toml"
            )
            raise OSError(msg)

        return cls.model_validate(raw)

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> UnifiedFittingConfig:
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

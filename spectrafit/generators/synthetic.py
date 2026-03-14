"""Synthetic spectrum generator for testing and scientific validation.

This module provides a Pydantic-based generator that creates reproducible
synthetic spectra with known ground-truth parameters. It replaces static
example data and enables:

- Parametric test generation with exact ground truths
- Noise injection for numerical stability testing
- Reproducible spectra via seed control
- Direct interop with SpectraFit input format (JSON/DataFrame)
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING
from typing import Literal
from typing import TypedDict
from typing import cast

import numpy as np

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from pydantic import model_validator

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.registry import REGISTRY
from spectrafit.models.types import CanonicalComponentInput
from spectrafit.models.types import CanonicalSpectraFitInput
from spectrafit.models.types import LegacySpectraFitInput


if TYPE_CHECKING:
    from collections.abc import Callable

    import pandas as pd

    from numpy.typing import NDArray

    from spectrafit.models.registry import ModelInfo
    from spectrafit.models.types import ModelParameterSpec


_SYNTHETIC_COMPONENT_ID = "synthetic"


def _registered_model_info(model_name: str) -> ModelInfo:
    """Return canonical metadata for a registered model name."""
    return REGISTRY.get(model_name)


class PeakInfoDict(TypedDict):
    """Per-peak ground-truth information produced by :meth:`SyntheticSpectrum.generate`.

    Attributes:
        index: Zero-based peak index within the spectrum definition.
        model: Model name as registered in the SpectraFit model registry.
        params: Mapping of parameter name → fitted/true float value.
    """

    index: int
    model: str
    params: dict[str, float]


class SyntheticGroundTruth(TypedDict):
    """Ground-truth data returned by :meth:`SyntheticSpectrum.generate`.

    Attributes:
        y_clean: Noise-free summed spectrum intensity array.
        noise: Noise array that was added to the clean signal.
        components: Per-peak intensity arrays before summation.
        peaks: Ordered list of per-peak ground-truth metadata.
        noise_level: Standard deviation of the injected noise.
        noise_type: Noise distribution used (``"gaussian"`` or ``"poisson"``).
        seed: Random seed used for reproducibility (``None`` = non-deterministic).
    """

    y_clean: NDArray[np.float64]
    noise: NDArray[np.float64]
    components: list[NDArray[np.float64]]
    peaks: list[PeakInfoDict]
    noise_level: float
    noise_type: str
    seed: int | None


class PeakDefinition(Component):
    """Definition of a single peak/component in the synthetic spectrum.

    Args:
        model: Name of the distribution model (must match SpectraFit model names).
        params: Model parameters as keyword arguments matching the model signature.

    Raises:
        ValueError: If the model name is unknown or parameters are invalid.

    Examples:
        >>> peak = PeakDefinition(
        ...     model="gaussian",
        ...     params={"amplitude": 1.0, "center": 0.0, "fwhmg": 0.5},
        ... )
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: str = Field(default=_SYNTHETIC_COMPONENT_ID, exclude=True)
    parameters: dict[str, FitParameter] = Field(default_factory=dict, alias="params")

    @staticmethod
    def _fit_parameter_from_scalar(parameter_value: float) -> FitParameter:
        """Promote a scalar shorthand into a canonical FitParameter model."""
        if parameter_value == 0.0:
            return FitParameter(
                value=parameter_value,
                vary=False,
                min=0.0,
                max=0.0,
            )

        return FitParameter(
            value=parameter_value,
            vary=True,
            min=(
                parameter_value * 0.5 if parameter_value > 0 else parameter_value * 1.5
            ),
            max=(
                parameter_value * 1.5 if parameter_value > 0 else parameter_value * 0.5
            ),
        )

    @field_validator("parameters", mode="before")
    @classmethod
    def _coerce_parameters(
        cls,
        value: object,
    ) -> object:
        """Promote shorthand scalar parameters into canonical FitParameter models."""
        if not isinstance(value, Mapping):
            return value

        normalized: dict[str, FitParameter] = {}
        for raw_name, raw_parameter in value.items():
            param_name = str(raw_name)
            if isinstance(raw_parameter, FitParameter):
                normalized[param_name] = raw_parameter
            elif isinstance(raw_parameter, int | float):
                normalized[param_name] = cls._fit_parameter_from_scalar(
                    float(raw_parameter)
                )
            elif isinstance(raw_parameter, Mapping):
                normalized[param_name] = FitParameter.model_validate(raw_parameter)
            else:
                msg = (
                    f"Parameter '{param_name}' for model '{getattr(cls, 'model', 'unknown')}' "
                    "must be a scalar, mapping, or FitParameter."
                )
                raise TypeError(msg)
        return normalized

    @model_validator(mode="after")
    def _validate_params(self) -> PeakDefinition:
        """Validate that params match the model's expected parameters."""
        try:
            expected_params = _registered_model_info(self.model).parameters
        except KeyError as exc:
            msg = f"Unknown model '{self.model}'. Available: {REGISTRY.names()}"
            raise ValueError(msg) from exc
        if missing := set(expected_params) - set(self.parameters):
            msg = (
                f"Model '{self.model}' missing required params: {sorted(missing)}. "
                f"Expected: {expected_params}"
            )
            raise ValueError(msg)
        if extra := set(self.parameters) - set(expected_params):
            msg = (
                f"Model '{self.model}' got unexpected params: {sorted(extra)}. "
                f"Expected: {expected_params}"
            )
            raise ValueError(msg)
        return self

    @property
    def parameter_values(self) -> dict[str, float]:
        """Return the generator-ready scalar values for this component."""
        return {
            parameter_name: parameter.value
            for parameter_name, parameter in self.parameters.items()
        }

    @property
    def params(self) -> dict[str, float]:
        """Compatibility alias for the generator-ready scalar parameter values."""
        return self.parameter_values

    def to_component(self, component_id: str | int) -> Component:
        """Render this synthetic peak definition as a canonical v2 component."""
        return Component(
            id=str(component_id),
            model=self.model,
            parameters={
                name: parameter.model_copy(deep=True)
                for name, parameter in self.parameters.items()
            },
        )


class SyntheticSpectrum(BaseModel):
    """Generate synthetic spectra with known ground truth for testing.

    !!! info "Synthetic Data Generator"

        Creates reproducible synthetic spectra from a list of peak definitions.
        The ground-truth parameters are known exactly, enabling scientific
        validation of fitting results.

    Args:
        x_min: Lower bound of the x-axis range.
        x_max: Upper bound of the x-axis range.
        num_points: Number of points in the x-axis grid.
        noise_level: Standard deviation of Gaussian noise (0.0 = no noise).
        noise_type: Type of noise to add ("gaussian" or "poisson").
        peaks: List of peak/component definitions.
        seed: Random seed for reproducibility (None = non-deterministic).

    Examples:
        >>> spectrum = SyntheticSpectrum(
        ...     x_min=-5.0,
        ...     x_max=5.0,
        ...     num_points=500,
        ...     noise_level=0.01,
        ...     peaks=[
        ...         PeakDefinition(
        ...             model="gaussian",
        ...             params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
        ...         ),
        ...     ],
        ...     seed=42,
        ... )
        >>> x, y, ground_truth = spectrum.generate()
    """

    x_min: float
    x_max: float
    num_points: int = Field(default=1000, ge=2)
    noise_level: float = Field(default=0.0, ge=0.0)
    noise_type: Literal["gaussian", "poisson"] = "gaussian"
    peaks: list[PeakDefinition] = Field(min_length=1)
    seed: int | None = None

    @model_validator(mode="after")
    def _validate_range(self) -> SyntheticSpectrum:
        """Validate that x_min < x_max."""
        if self.x_min >= self.x_max:
            msg = f"x_min ({self.x_min}) must be less than x_max ({self.x_max})"
            raise ValueError(msg)
        return self

    def generate(
        self,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], SyntheticGroundTruth]:
        """Generate synthetic spectrum data.

        Returns:
            tuple: ``(x, y, ground_truth)`` where:
                - ``x``: x-axis values as 1D numpy array
                - ``y``: Spectrum intensity (signal + noise) as 1D numpy array
                - ``ground_truth``: Dict with clean signal, noise, and per-peak info
        """
        rng = np.random.default_rng(self.seed)
        x = np.linspace(self.x_min, self.x_max, self.num_points)

        # Compute each peak contribution
        components: list[NDArray[np.float64]] = []
        peak_info: list[PeakInfoDict] = []
        for i, peak in enumerate(self.peaks):
            func = cast(
                "Callable[..., object]",
                _registered_model_info(peak.model).function,
            )
            y_component = cast("NDArray[np.float64]", func(x, **peak.parameter_values))
            components.append(y_component)
            peak_info.append(
                PeakInfoDict(
                    index=i,
                    model=peak.model,
                    params=dict(peak.parameter_values),
                ),
            )

        # Sum all components
        y_clean = np.sum(components, axis=0)

        # Add noise
        if self.noise_level > 0:
            if self.noise_type == "gaussian":
                noise = rng.normal(0, self.noise_level, size=x.shape)
            else:
                noise = rng.poisson(np.maximum(np.abs(y_clean), 1e-10)) - np.maximum(
                    np.abs(y_clean),
                    1e-10,
                )
                noise = noise * self.noise_level
        else:
            noise = np.zeros_like(x)

        y = y_clean + noise

        ground_truth: SyntheticGroundTruth = {
            "y_clean": y_clean,
            "noise": noise,
            "components": components,
            "peaks": peak_info,
            "noise_level": self.noise_level,
            "noise_type": self.noise_type,
            "seed": self.seed,
        }

        return x, y, ground_truth

    def to_dataframe(
        self,
        energy_col: str = "energy",
        intensity_col: str = "intensity",
    ) -> pd.DataFrame:
        """Generate spectrum and return as DataFrame.

        Args:
            energy_col: Column name for x-axis values.
            intensity_col: Column name for y-axis values.

        Returns:
            pd.DataFrame: DataFrame with energy and intensity columns,
                compatible with SpectraFit input format.
        """
        import pandas as pd  # noqa: PLC0415

        x, y, _ = self.generate()
        return pd.DataFrame({energy_col: x, intensity_col: y})

    def to_components(self) -> list[Component]:
        """Render the synthetic peaks as canonical v2 components."""
        return [
            peak.to_component(f"p{index}")
            for index, peak in enumerate(self.peaks, start=1)
        ]

    def to_config(self) -> UnifiedFittingConfig:
        """Generate a canonical v2 fitting config for this synthetic spectrum."""
        return UnifiedFittingConfig(components=self.to_components())

    @staticmethod
    def _component_payload(component: Component) -> CanonicalComponentInput:
        """Serialize a canonical component into a v2 component payload."""
        return CanonicalComponentInput(
            id=component.id,
            model=component.model,
            parameters={
                param_name: parameter.model_dump(mode="json", exclude_none=True)
                for param_name, parameter in component.parameters.items()
            },
        )

    def _to_legacy_peaks_payload(self) -> LegacySpectraFitInput:
        """Generate the quarantined legacy v1 peaks mapping."""
        peaks_config: dict[str, dict[str, ModelParameterSpec]] = {}
        for index, component in enumerate(self.to_components(), start=1):
            peaks_config[str(index)] = {
                component.model: {
                    param_name: parameter.model_dump(mode="json", exclude_none=True)
                    for param_name, parameter in component.parameters.items()
                }
            }
        return LegacySpectraFitInput(peaks=peaks_config)

    def _to_canonical_payload(self) -> CanonicalSpectraFitInput:
        """Generate the canonical v2 serialized config payload."""
        return CanonicalSpectraFitInput(
            components=[
                self._component_payload(component) for component in self.to_components()
            ]
        )

    def to_spectrafit_input(
        self,
        *,
        legacy: bool = False,
    ) -> CanonicalSpectraFitInput | LegacySpectraFitInput:
        """Generate a SpectraFit-compatible input configuration.

        Returns:
            dict: Input dict in canonical v2 format by default. Pass
                ``legacy=True`` to render the quarantined legacy v1 ``peaks``
                mapping for compatibility.

        Examples:
            >>> spectrum = SyntheticSpectrum(
            ...     x_min=-5, x_max=5,
            ...     peaks=[
            ...         PeakDefinition(
            ...             model="gaussian",
            ...             params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
            ...         ),
            ...     ],
            ... )
            >>> config = spectrum.to_spectrafit_input()
            >>> config["components"][0]["parameters"]["amplitude"]["value"]
            1.0
        """
        if legacy:
            return self._to_legacy_peaks_payload()
        return self._to_canonical_payload()

    def to_json(self) -> str:
        """Serialize the spectrum definition to JSON.

        Returns:
            str: JSON string of the spectrum configuration.
        """
        return self.model_dump_json(indent=2)

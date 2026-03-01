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

from typing import TYPE_CHECKING
from typing import Any
from typing import Literal

import numpy as np

from pydantic import BaseModel
from pydantic import Field
from pydantic import model_validator

from spectrafit.models.registry import REGISTRY


if TYPE_CHECKING:
    import pandas as pd

    from numpy.typing import NDArray


# Model name → (function, parameter names) — derived from central registry
_MODEL_REGISTRY: dict[str, tuple[Any, list[str]]] = {
    info.name: (info.function, info.parameters) for info in REGISTRY.list_models()
}

ModelName = Literal[
    "gaussian",
    "orcagaussian",
    "lorentzian",
    "voigt",
    "pseudovoigt",
    "exponential",
    "power",
    "linear",
    "constant",
    "erf",
    "heaviside",
    "atan",
    "log",
    "cgaussian",
    "clorentzian",
    "cvoigt",
    "polynom2",
    "polynom3",
    "pearson1",
    "pearson2",
    "pearson3",
    "pearson4",
]


class PeakDefinition(BaseModel):
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

    model: ModelName
    params: dict[str, float]

    @model_validator(mode="after")
    def _validate_params(self) -> PeakDefinition:
        """Validate that params match the model's expected parameters."""
        if self.model not in _MODEL_REGISTRY:
            msg = f"Unknown model '{self.model}'. Available: {sorted(_MODEL_REGISTRY)}"
            raise ValueError(msg)
        _, expected_params = _MODEL_REGISTRY[self.model]
        missing = set(expected_params) - set(self.params)
        if missing:
            msg = (
                f"Model '{self.model}' missing required params: {sorted(missing)}. "
                f"Expected: {expected_params}"
            )
            raise ValueError(msg)
        extra = set(self.params) - set(expected_params)
        if extra:
            msg = (
                f"Model '{self.model}' got unexpected params: {sorted(extra)}. "
                f"Expected: {expected_params}"
            )
            raise ValueError(msg)
        return self


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
    ) -> tuple[NDArray[np.float64], NDArray[np.float64], dict[str, Any]]:
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
        peak_info: list[dict[str, Any]] = []
        for i, peak in enumerate(self.peaks):
            func, _ = _MODEL_REGISTRY[peak.model]
            y_component = func(x, **peak.params)
            components.append(y_component)
            peak_info.append(
                {
                    "index": i,
                    "model": peak.model,
                    "params": dict(peak.params),
                }
            )

        # Sum all components
        y_clean = np.sum(components, axis=0)

        # Add noise
        if self.noise_level > 0:
            if self.noise_type == "gaussian":
                noise = rng.normal(0, self.noise_level, size=x.shape)
            else:
                noise = rng.poisson(np.maximum(np.abs(y_clean), 1e-10)) - np.maximum(
                    np.abs(y_clean), 1e-10
                )
                noise = noise * self.noise_level
        else:
            noise = np.zeros_like(x)

        y = y_clean + noise

        ground_truth: dict[str, Any] = {
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

    def to_spectrafit_input(self) -> dict[str, Any]:
        """Generate a SpectraFit-compatible input configuration.

        Returns:
            dict: Input dict with peaks defined in SpectraFit format, suitable
                for JSON/YAML/TOML serialization.

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
            >>> config["peaks"]["1"]["gaussian"]["amplitude"]["value"]
            1.0
        """
        peaks_config: dict[str, dict[str, dict[str, dict[str, Any]]]] = {}
        for i, peak in enumerate(self.peaks, start=1):
            param_config: dict[str, dict[str, Any]] = {}
            for param_name, param_value in peak.params.items():
                param_config[param_name] = {
                    "value": param_value,
                    "vary": True,
                    "min": param_value * 0.5 if param_value > 0 else param_value * 1.5,
                    "max": param_value * 1.5 if param_value > 0 else param_value * 0.5,
                }
            peaks_config[str(i)] = {peak.model: param_config}

        return {"peaks": peaks_config}

    def to_json(self) -> str:
        """Serialize the spectrum definition to JSON.

        Returns:
            str: JSON string of the spectrum configuration.
        """
        return self.model_dump_json(indent=2)

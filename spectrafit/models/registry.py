"""Model registry for distribution models.

This module provides a centralized registry for all distribution models used in
curve fitting. It replaces fragile string-based dispatch with a structured
lookup mechanism.
"""

from __future__ import annotations

from collections.abc import Callable  # noqa: TC003
from typing import Literal

import lmfit

from pydantic import BaseModel
from pydantic import ConfigDict

from spectrafit.models.functions.regular import atan_step
from spectrafit.models.functions.regular import cgaussian
from spectrafit.models.functions.regular import clorentzian
from spectrafit.models.functions.regular import constant
from spectrafit.models.functions.regular import cvoigt
from spectrafit.models.functions.regular import erf_step
from spectrafit.models.functions.regular import exponential
from spectrafit.models.functions.regular import gaussian
from spectrafit.models.functions.regular import heaviside
from spectrafit.models.functions.regular import linear
from spectrafit.models.functions.regular import log_step
from spectrafit.models.functions.regular import lorentzian
from spectrafit.models.functions.regular import orcagaussian
from spectrafit.models.functions.regular import pearson1
from spectrafit.models.functions.regular import pearson2
from spectrafit.models.functions.regular import pearson3
from spectrafit.models.functions.regular import pearson4
from spectrafit.models.functions.regular import polynom2
from spectrafit.models.functions.regular import polynom3
from spectrafit.models.functions.regular import power
from spectrafit.models.functions.regular import pseudovoigt
from spectrafit.models.functions.regular import voigt


ModelCategory = Literal[
    "peak",
    "step",
    "cumulative",
    "polynomial",
    "background",
    "pearson",
]


class ModelInfo(BaseModel):
    """Metadata about a distribution model.

    Args:
        name: Canonical model name (e.g., "gaussian").
        category: Model category for grouping.
        function: The actual math function from regular.py.
        parameters: Parameter names in order (excluding ``x``).
        description: Human-readable description of the model.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    category: ModelCategory
    function: Callable[..., object]
    parameters: list[str]
    description: str

    def make_lmfit_model(self, prefix: str) -> lmfit.Model:
        """Create an lmfit.Model instance wrapping this model's numpy function.

        The model uses :attr:`function` (from ``regular.py``) as the
        underlying callable so that parameter names match SpectraFit's
        conventions exactly (e.g. ``fwhmg``, not ``sigma``).

        Args:
            prefix: lmfit parameter prefix, typically ``f"{component_id}_"``.
                Must start with a letter (see
                :func:`~spectrafit.models.naming.sanitize_component_id`).

        Returns:
            lmfit.Model instance with ``independent_vars=["x"]``.

        Examples:
            >>> from spectrafit.models.registry import REGISTRY
            >>> m = REGISTRY.get("gaussian").make_lmfit_model("p1_")
            >>> sorted(m.make_params().keys())
            ['p1_amplitude', 'p1_center', 'p1_fwhmg']
        """
        return lmfit.Model(self.function, prefix=prefix, independent_vars=["x"])


class ModelRegistry:
    """Central registry for distribution models.

    Provides structured lookup of model functions and metadata,
    replacing fragile string-based dispatch.

    Examples:
        >>> from spectrafit.models.registry import REGISTRY
        >>> info = REGISTRY.get("gaussian")
        >>> info.name
        'gaussian'
        >>> "gaussian" in REGISTRY
        True
    """

    def __init__(self) -> None:
        """Initialize an empty registry."""
        self._models: dict[str, ModelInfo] = {}

    def register(self, info: ModelInfo) -> None:
        """Register a model.

        Args:
            info: Model metadata to register.
        """
        self._models[info.name] = info

    def get(self, name: str) -> ModelInfo:
        """Get model info by name.

        Args:
            name: Canonical model name.

        Returns:
            ModelInfo: The model metadata.

        Raises:
            KeyError: If model name is not registered.
        """
        if name not in self._models:
            msg = f"Unknown model '{name}'. Available: {sorted(self._models.keys())}"
            raise KeyError(msg)
        return self._models[name]

    def list_models(self, category: str | None = None) -> list[ModelInfo]:
        """List all models or filter by category.

        Args:
            category: Optional category filter. If None, returns all models.

        Returns:
            list[ModelInfo]: List of matching model info objects.
        """
        if category is None:
            return list(self._models.values())
        return [m for m in self._models.values() if m.category == category]

    def __contains__(self, name: str) -> bool:
        """Check if a model is registered.

        Args:
            name: Model name to check.

        Returns:
            bool: True if model is registered.
        """
        return name in self._models

    def names(self) -> list[str]:
        """Return all registered model names.

        Returns:
            list[str]: Sorted list of model names.
        """
        return sorted(self._models.keys())


def _build_registry() -> ModelRegistry:
    """Build and populate the default model registry.

    Returns:
        ModelRegistry: Pre-populated registry with all 22 distribution models.
    """
    registry = ModelRegistry()

    _models: list[ModelInfo] = [
        # Peak models
        ModelInfo(
            name="gaussian",
            category="peak",
            function=gaussian,
            parameters=["amplitude", "center", "fwhmg"],
            description="Normalized Gaussian distribution",
        ),
        ModelInfo(
            name="orcagaussian",
            category="peak",
            function=orcagaussian,
            parameters=["amplitude", "center", "width"],
            description="ORCA-style Gaussian distribution",
        ),
        ModelInfo(
            name="lorentzian",
            category="peak",
            function=lorentzian,
            parameters=["amplitude", "center", "fwhml"],
            description="Lorentzian distribution",
        ),
        ModelInfo(
            name="voigt",
            category="peak",
            function=voigt,
            parameters=["center", "fwhmv", "gamma"],
            description="Voigt profile distribution",
        ),
        ModelInfo(
            name="pseudovoigt",
            category="peak",
            function=pseudovoigt,
            parameters=["amplitude", "center", "fwhmg", "fwhml"],
            description="Pseudo-Voigt distribution",
        ),
        # Step models
        ModelInfo(
            name="erf",
            category="step",
            function=erf_step,
            parameters=["amplitude", "center", "sigma"],
            description="Error function step",
        ),
        ModelInfo(
            name="heaviside",
            category="step",
            function=heaviside,
            parameters=["amplitude", "center", "sigma"],
            description="Heaviside step function",
        ),
        ModelInfo(
            name="atan",
            category="step",
            function=atan_step,
            parameters=["amplitude", "center", "sigma"],
            description="Arctan step function",
        ),
        ModelInfo(
            name="log",
            category="step",
            function=log_step,
            parameters=["amplitude", "center", "sigma"],
            description="Logarithmic step function",
        ),
        # Cumulative models
        ModelInfo(
            name="cgaussian",
            category="cumulative",
            function=cgaussian,
            parameters=["amplitude", "center", "fwhmg"],
            description="Cumulative Gaussian function",
        ),
        ModelInfo(
            name="clorentzian",
            category="cumulative",
            function=clorentzian,
            parameters=["amplitude", "center", "fwhml"],
            description="Cumulative Lorentzian function",
        ),
        ModelInfo(
            name="cvoigt",
            category="cumulative",
            function=cvoigt,
            parameters=["amplitude", "center", "fwhmv", "gamma"],
            description="Cumulative Voigt function",
        ),
        # Polynomial models
        ModelInfo(
            name="polynom2",
            category="polynomial",
            function=polynom2,
            parameters=["coefficient0", "coefficient1", "coefficient2"],
            description="Second-order polynomial",
        ),
        ModelInfo(
            name="polynom3",
            category="polynomial",
            function=polynom3,
            parameters=[
                "coefficient0",
                "coefficient1",
                "coefficient2",
                "coefficient3",
            ],
            description="Third-order polynomial",
        ),
        # Background models
        ModelInfo(
            name="linear",
            category="background",
            function=linear,
            parameters=["slope", "intercept"],
            description="Linear function",
        ),
        ModelInfo(
            name="constant",
            category="background",
            function=constant,
            parameters=["amplitude"],
            description="Constant value",
        ),
        ModelInfo(
            name="exponential",
            category="background",
            function=exponential,
            parameters=["amplitude", "decay", "intercept"],
            description="Exponential decay",
        ),
        ModelInfo(
            name="power",
            category="background",
            function=power,
            parameters=["amplitude", "exponent", "intercept"],
            description="Power function",
        ),
        # Pearson models
        ModelInfo(
            name="pearson1",
            category="pearson",
            function=pearson1,
            parameters=["amplitude", "center", "sigma", "exponent"],
            description="Pearson type I distribution",
        ),
        ModelInfo(
            name="pearson2",
            category="pearson",
            function=pearson2,
            parameters=["amplitude", "center", "sigma", "exponent"],
            description="Pearson type II distribution",
        ),
        ModelInfo(
            name="pearson3",
            category="pearson",
            function=pearson3,
            parameters=["amplitude", "center", "sigma", "exponent", "skewness"],
            description="Pearson type III distribution",
        ),
        ModelInfo(
            name="pearson4",
            category="pearson",
            function=pearson4,
            parameters=[
                "amplitude",
                "center",
                "sigma",
                "exponent",
                "skewness",
                "kurtosis",
            ],
            description="Pearson type IV distribution",
        ),
    ]

    for model_info in _models:
        registry.register(model_info)

    return registry


REGISTRY = _build_registry()

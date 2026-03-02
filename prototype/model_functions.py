"""Model functions and naming utilities for the prototype fitting pipeline.

This module is intentionally self-contained: it has zero imports from spectrafit.*.
All mathematical model functions are reimplemented here as pure numpy functions so
the prototype can run in complete isolation.

Naming contract
---------------
``lmfit parameter name = {sanitized_id}_{field_name}``

Examples::

    lmfit_param_name("p1", "amplitude")  ->  "p1_amplitude"
    lmfit_param_name("1",  "center")     ->  "p1_center"
    lmfit_param_name("bg", "slope")      ->  "bg_slope"
"""

from __future__ import annotations

import re

from collections.abc import Callable
from math import log
from math import pi
from math import sqrt

import numpy as np

from numpy.typing import NDArray
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


# ---------------------------------------------------------------------------
# Math constants
# ---------------------------------------------------------------------------
_SQ2PI = sqrt(2.0 * pi)
_FWHMG2SIG = 1.0 / (2.0 * sqrt(2.0 * log(2.0)))
_FWHML2SIG = 0.5
_MIN_SIGMA = 1.0e-13


# ---------------------------------------------------------------------------
# Model functions  (pure numpy, no spectrafit imports)
# ---------------------------------------------------------------------------


def gaussian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 1.0,
) -> NDArray[np.float64]:
    """Normalised Gaussian peak.

    Args:
        x: x-values.
        amplitude: Peak area / amplitude.
        center: Peak center position.
        fwhmg: Full width at half maximum.

    Returns:
        Gaussian evaluated at each x.
    """
    sigma = max(fwhmg * _FWHMG2SIG, _MIN_SIGMA)
    norm = amplitude / (_SQ2PI * sigma)
    return np.array(norm * np.exp(-0.5 * ((x - center) / sigma) ** 2))


def lorentzian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhml: float = 1.0,
) -> NDArray[np.float64]:
    """Lorentzian (Cauchy) peak.

    Args:
        x: x-values.
        amplitude: Peak area / amplitude.
        center: Peak center position.
        fwhml: Full width at half maximum.

    Returns:
        Lorentzian evaluated at each x.
    """
    sigma = max(fwhml * _FWHML2SIG, _MIN_SIGMA)
    return np.array(amplitude / (1.0 + ((x - center) / sigma) ** 2) / (pi * sigma))


def pseudovoigt(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 1.0,
    fwhml: float = 1.0,
) -> NDArray[np.float64]:
    """Pseudo-Voigt peak (linear mix of Gaussian and Lorentzian).

    Uses the Thompson-Cox-Hastings approximation for the mixing parameter eta.
    Reference: J. Appl. Cryst. (2000). 33, 1311-1316.

    Args:
        x: x-values.
        amplitude: Peak area / amplitude.
        center: Peak center position.
        fwhmg: Gaussian FWHM component.
        fwhml: Lorentzian FWHM component.

    Returns:
        Pseudo-Voigt evaluated at each x.
    """
    f = np.power(
        fwhmg**5
        + 2.69269 * fwhmg**4 * fwhml
        + 2.42843 * fwhmg**3 * fwhml**2
        + 4.47163 * fwhmg**2 * fwhml**3
        + 0.07842 * fwhmg * fwhml**4
        + fwhml**5,
        0.2,
    )
    n = 1.36603 * (fwhml / f) - 0.47719 * (fwhml / f) ** 2 + 0.11116 * (fwhml / f) ** 3
    return np.array(
        n * lorentzian(x, amplitude=amplitude, center=center, fwhml=fwhml)
        + (1 - n) * gaussian(x, amplitude=amplitude, center=center, fwhmg=fwhmg)
    )


def linear(
    x: NDArray[np.float64],
    slope: float = 0.0,
    intercept: float = 0.0,
) -> NDArray[np.float64]:
    """Linear background.

    Args:
        x: x-values.
        slope: Slope of the line.
        intercept: y-intercept.

    Returns:
        Linear function evaluated at each x.
    """
    return np.array(slope * x + intercept)


# ---------------------------------------------------------------------------
# Model registry
# ---------------------------------------------------------------------------


class ModelInfo(BaseModel):
    """Metadata about a single model function.

    Attributes:
        name: Canonical model key (e.g. ``"gaussian"``).
        function: The numpy callable.
        parameters: Parameter names (excluding ``x``).
        description: Short human-readable description.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True)

    name: str
    function: Callable[..., NDArray[np.float64]]
    parameters: list[str] = Field(default_factory=list)
    description: str = ""


MODEL_REGISTRY: dict[str, ModelInfo] = {
    "gaussian": ModelInfo(
        name="gaussian",
        function=gaussian,
        parameters=["amplitude", "center", "fwhmg"],
        description="Normalised Gaussian peak",
    ),
    "lorentzian": ModelInfo(
        name="lorentzian",
        function=lorentzian,
        parameters=["amplitude", "center", "fwhml"],
        description="Lorentzian (Cauchy) peak",
    ),
    "pseudovoigt": ModelInfo(
        name="pseudovoigt",
        function=pseudovoigt,
        parameters=["amplitude", "center", "fwhmg", "fwhml"],
        description="Pseudo-Voigt (Gaussian + Lorentzian mix)",
    ),
    "linear": ModelInfo(
        name="linear",
        function=linear,
        parameters=["slope", "intercept"],
        description="Linear background",
    ),
}


# ---------------------------------------------------------------------------
# Naming utilities
# ---------------------------------------------------------------------------


def sanitize_component_id(raw_id: str) -> str:
    """Ensure a component id is a valid lmfit prefix (must start with a letter).

    Numeric ids such as ``"1"`` are automatically prefixed with ``"p"``.

    Args:
        raw_id: User-supplied component id (e.g. ``"1"``, ``"main"``, ``"bg"``).

    Returns:
        Sanitized id safe to use as an lmfit prefix.

    Examples:
        >>> sanitize_component_id("1")
        'p1'
        >>> sanitize_component_id("main")
        'main'
    """
    return re.sub(r"^(\d)", r"p\1", raw_id)


def lmfit_param_name(component_id: str, field_name: str) -> str:
    """Canonical lmfit parameter name: ``{sanitized_id}_{field_name}``.

    This is the **only** place this formula is written in the prototype.

    Args:
        component_id: Component id (raw; sanitization is applied here).
        field_name: Parameter field name (e.g. ``"amplitude"``).

    Returns:
        Unique lmfit parameter name.

    Examples:
        >>> lmfit_param_name("p1", "amplitude")
        'p1_amplitude'
        >>> lmfit_param_name("1", "center")
        'p1_center'
        >>> lmfit_param_name("bg", "slope")
        'bg_slope'
    """
    return f"{sanitize_component_id(component_id)}_{field_name}"

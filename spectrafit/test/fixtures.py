"""Pydantic fixture models for SpectraFit tests.

Provides typed, validated test fixtures that replace raw ``dict[str, Any]``
definitions.  Each model exposes helpers to convert back to the nested-dict
format expected by SpectraFit's solver so that existing call-sites continue
to work unchanged.
"""

from __future__ import annotations

from math import inf
from typing import TYPE_CHECKING
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from spectrafit.generators.synthetic import PeakDefinition
from spectrafit.generators.synthetic import SyntheticSpectrum


if TYPE_CHECKING:
    import numpy as np

    from numpy.typing import NDArray


class ParameterSpec(BaseModel):
    """Specification for a single fitting parameter.

    Args:
        value: Initial guess for the parameter.
        min: Lower bound (``-inf`` means unbounded).
        max: Upper bound (``inf`` means unbounded).
        vary: Whether the parameter is free during fitting.
        expr: Optional constraint expression referencing other parameters.

    Examples:
        >>> p = ParameterSpec(value=1.0, min=0.0, max=10.0)
        >>> p.to_dict()
        {'value': 1.0, 'min': 0.0, 'max': 10.0, 'vary': True}
    """

    value: float
    min: float = -inf
    max: float = inf
    vary: bool = True
    expr: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to the dict format consumed by SpectraFit.

        Returns:
            Dict with keys ``value``, ``min``, ``max``, ``vary``, and
            optionally ``expr``.
        """
        d: dict[str, Any] = {
            "value": self.value,
            "min": self.min,
            "max": self.max,
            "vary": self.vary,
        }
        if self.expr is not None:
            d["expr"] = self.expr
        return d


class PeakSpec(BaseModel):
    """Specification for a single peak with its model type and parameters.

    Args:
        model_name: Distribution model name (e.g. ``"gaussian"``).
        parameters: Mapping of parameter name to :class:`ParameterSpec`.

    Examples:
        >>> peak = PeakSpec(
        ...     model_name="gaussian",
        ...     parameters={
        ...         "amplitude": ParameterSpec(value=1.0, min=0, max=10),
        ...         "center": ParameterSpec(value=0.0, min=-5, max=5),
        ...         "fwhmg": ParameterSpec(value=0.5, min=0.01, max=5),
        ...     },
        ... )
        >>> peak.to_dict()["gaussian"]["amplitude"]["value"]
        1.0
    """

    model_name: str
    parameters: dict[str, ParameterSpec]

    def to_dict(self) -> dict[str, Any]:
        """Convert to the nested dict format expected by the solver.

        Returns:
            ``{model_name: {param_name: {value, min, max, vary, ...}, ...}}``
        """
        return {
            self.model_name: {
                name: spec.to_dict() for name, spec in self.parameters.items()
            }
        }


class FittingFixture(BaseModel):
    """A complete test fixture for spectrum fitting.

    Args:
        x_range: ``(x_min, x_max)`` for the synthetic x-axis.
        num_points: Number of data points.
        peaks: One or more :class:`PeakSpec` definitions.
        noise_level: Standard deviation of additive Gaussian noise.
        seed: Random seed for reproducibility.
        minimizer: Minimizer settings forwarded to *lmfit*.
        optimizer: Optimizer settings forwarded to *lmfit*.

    Examples:
        >>> from spectrafit.test.fixtures import single_gaussian
        >>> fix = single_gaussian()
        >>> x, y = fix.generate_data()
        >>> x.shape == (fix.num_points,)
        True
    """

    x_range: tuple[float, float] = (-10.0, 10.0)
    num_points: int = Field(default=1000, ge=2)
    peaks: list[PeakSpec]
    noise_level: float = Field(default=0.0, ge=0.0)
    seed: int = 42
    minimizer: dict[str, Any] = Field(
        default_factory=lambda: {"nan_policy": "propagate", "calc_covar": True}
    )
    optimizer: dict[str, Any] = Field(
        default_factory=lambda: {"max_nfev": 1000, "method": "leastsq"}
    )

    def to_peaks_dict(self) -> dict[str, Any]:
        """Convert peaks list to the SpectraFit nested peaks dict.

        Returns:
            ``{"1": {...}, "2": {...}, ...}`` keyed by 1-based string IDs.
        """
        return {str(i): peak.to_dict() for i, peak in enumerate(self.peaks, start=1)}

    def to_input_dict(self) -> dict[str, Any]:
        """Convert to a full input dict for :class:`SolverModels`.

        Returns:
            Dict with ``column``, ``minimizer``, ``optimizer``, ``peaks``,
            and ``global_`` keys.
        """
        return {
            "column": ["energy", "intensity"],
            "minimizer": dict(self.minimizer),
            "optimizer": dict(self.optimizer),
            "peaks": self.to_peaks_dict(),
            "global_": 0,
        }

    def generate_data(self) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Generate synthetic x/y data using :class:`SyntheticSpectrum`.

        Returns:
            ``(x, y)`` numpy arrays with ``num_points`` elements each.
        """
        peak_defs = [
            PeakDefinition(
                model=peak.model_name,  # type: ignore[arg-type]
                params={name: spec.value for name, spec in peak.parameters.items()},
            )
            for peak in self.peaks
        ]
        spectrum = SyntheticSpectrum(
            x_min=self.x_range[0],
            x_max=self.x_range[1],
            num_points=self.num_points,
            noise_level=self.noise_level,
            peaks=peak_defs,
            seed=self.seed,
        )
        x, y, _ = spectrum.generate()
        return x, y


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------


def single_gaussian(
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 0.5,
) -> FittingFixture:
    """Create a fixture with a single Gaussian peak.

    Args:
        amplitude: Peak amplitude.
        center: Peak center position.
        fwhmg: Gaussian full-width at half-maximum.

    Returns:
        A ready-to-use :class:`FittingFixture`.
    """
    return FittingFixture(
        peaks=[
            PeakSpec(
                model_name="gaussian",
                parameters={
                    "amplitude": ParameterSpec(
                        value=amplitude, min=0.0, max=amplitude * 3
                    ),
                    "center": ParameterSpec(
                        value=center, min=center - 5, max=center + 5
                    ),
                    "fwhmg": ParameterSpec(value=fwhmg, min=0.01, max=fwhmg * 5),
                },
            ),
        ],
    )


def single_lorentzian(
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhml: float = 0.5,
) -> FittingFixture:
    """Create a fixture with a single Lorentzian peak.

    Args:
        amplitude: Peak amplitude.
        center: Peak center position.
        fwhml: Lorentzian full-width at half-maximum.

    Returns:
        A ready-to-use :class:`FittingFixture`.
    """
    return FittingFixture(
        peaks=[
            PeakSpec(
                model_name="lorentzian",
                parameters={
                    "amplitude": ParameterSpec(
                        value=amplitude, min=0.0, max=amplitude * 3
                    ),
                    "center": ParameterSpec(
                        value=center, min=center - 5, max=center + 5
                    ),
                    "fwhml": ParameterSpec(value=fwhml, min=0.01, max=fwhml * 5),
                },
            ),
        ],
    )


def double_gaussian(separation: float = 3.0) -> FittingFixture:
    """Create a fixture with two Gaussian peaks.

    Args:
        separation: Distance between the two peak centers (symmetric about 0).

    Returns:
        A ready-to-use :class:`FittingFixture`.
    """
    half = separation / 2
    return FittingFixture(
        peaks=[
            PeakSpec(
                model_name="gaussian",
                parameters={
                    "amplitude": ParameterSpec(value=1.0, min=0.0, max=3.0),
                    "center": ParameterSpec(value=-half, min=-10.0, max=0.0),
                    "fwhmg": ParameterSpec(value=0.8, min=0.01, max=4.0),
                },
            ),
            PeakSpec(
                model_name="gaussian",
                parameters={
                    "amplitude": ParameterSpec(value=0.7, min=0.0, max=3.0),
                    "center": ParameterSpec(value=half, min=0.0, max=10.0),
                    "fwhmg": ParameterSpec(value=0.8, min=0.01, max=4.0),
                },
            ),
        ],
    )


def gaussian_with_background() -> FittingFixture:
    """Create a fixture with a Gaussian peak on a constant background.

    Returns:
        A ready-to-use :class:`FittingFixture`.
    """
    return FittingFixture(
        peaks=[
            PeakSpec(
                model_name="gaussian",
                parameters={
                    "amplitude": ParameterSpec(value=1.0, min=0.0, max=3.0),
                    "center": ParameterSpec(value=0.0, min=-5.0, max=5.0),
                    "fwhmg": ParameterSpec(value=0.5, min=0.01, max=3.0),
                },
            ),
            PeakSpec(
                model_name="constant",
                parameters={
                    "amplitude": ParameterSpec(value=0.1, min=0.0, max=1.0),
                },
            ),
        ],
    )

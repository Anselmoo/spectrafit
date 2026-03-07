"""Generate synthetic CSV data for all SpectraFit v2 example directories.

This script is self-contained — it has zero imports from spectrafit.* — and
uses inline math for Gaussian, Pseudo-Voigt, and linear models.

Usage::

    uv run python scripts/generate_examples.py
    uv run python scripts/generate_examples.py --seed 123

Each invocation writes:
    examples/basic/data.csv
    examples/two-peak-constrained/data.csv
"""

from __future__ import annotations

from math import log
from math import pi
from math import sqrt
from pathlib import Path

import numpy as np
import pandas as pd
import typer


# ---------------------------------------------------------------------------
# Math constants (mirror spectrafit/models/regular.py — no import needed)
# ---------------------------------------------------------------------------

_SQ2PI: float = sqrt(2.0 * pi)
_FWHMG2SIG: float = 1.0 / (2.0 * sqrt(2.0 * log(2.0)))
_FWHML2SIG: float = 0.5

# ---------------------------------------------------------------------------
# Inline model functions
# ---------------------------------------------------------------------------


def _gaussian(
    x: np.ndarray,
    amplitude: float,
    center: float,
    fwhmg: float,
) -> np.ndarray:
    """Normalised Gaussian peak — matches spectrafit.models.regular.gaussian.

    Args:
        x: x-axis values.
        amplitude: Peak amplitude.
        center: Peak center.
        fwhmg: Full width at half maximum (Gaussian).

    Returns:
        1-D array of Gaussian values.
    """
    sigma = fwhmg * _FWHMG2SIG
    norm = amplitude / (_SQ2PI * sigma)
    return norm * np.exp(-0.5 * ((x - center) / sigma) ** 2)


def _lorentzian(
    x: np.ndarray,
    amplitude: float,
    center: float,
    fwhml: float,
) -> np.ndarray:
    """Lorentzian peak — helper for pseudo-Voigt.

    Args:
        x: x-axis values.
        amplitude: Peak amplitude.
        center: Peak center.
        fwhml: Full width at half maximum (Lorentzian).

    Returns:
        1-D array of Lorentzian values.
    """
    sigma = fwhml * _FWHML2SIG
    return amplitude / (pi * sigma * (1.0 + ((x - center) / sigma) ** 2))


def _pseudovoigt(
    x: np.ndarray,
    amplitude: float,
    center: float,
    fwhmg: float,
    fwhml: float,
) -> np.ndarray:
    """Pseudo-Voigt profile — matches spectrafit.models.regular.pseudovoigt.

    Uses the Thompson, Cox & Hastings (1987) mixing parameter formula;
    see J. Appl. Cryst. (2000). 33, 1311-1316.

    Args:
        x: x-axis values.
        amplitude: Peak amplitude.
        center: Peak center.
        fwhmg: Gaussian FWHM component.
        fwhml: Lorentzian FWHM component.

    Returns:
        1-D array of pseudo-Voigt values.
    """
    f = (
        fwhmg**5
        + 2.69269 * fwhmg**4 * fwhml
        + 2.42843 * fwhmg**3 * fwhml**2
        + 4.47163 * fwhmg**2 * fwhml**3
        + 0.07842 * fwhmg * fwhml**4
        + fwhml**5
    ) ** 0.2
    ratio = fwhml / f
    eta = 1.36603 * ratio - 0.47719 * ratio**2 + 0.11116 * ratio**3
    return eta * _lorentzian(x, amplitude, center, fwhml) + (1.0 - eta) * _gaussian(
        x, amplitude, center, fwhmg
    )


def _linear(x: np.ndarray, slope: float, intercept: float) -> np.ndarray:
    """Linear background — matches spectrafit.models.regular.linear.

    Args:
        x: x-axis values.
        slope: Slope of the line.
        intercept: y-intercept.

    Returns:
        1-D array of linear values.
    """
    return slope * x + intercept


# ---------------------------------------------------------------------------
# Spectrum generators
# ---------------------------------------------------------------------------


def _generate_basic(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Compute clean signal + noise for the basic single-peak example.

    Ground truth:
        - Gaussian: amplitude=1.0, center=0.0, fwhmg=0.4
        - Linear bg: slope=0.0, intercept=0.02
        - Noise: Gaussian, scale=0.02

    Args:
        x: x-axis array (200 points, -2 to 2).
        rng: Seeded random generator.

    Returns:
        Noisy intensity array.
    """
    y = (
        _gaussian(x, amplitude=1.0, center=0.0, fwhmg=0.4)
        + _linear(x, slope=0.0, intercept=0.02)
    )
    return y + rng.normal(0.0, 0.02, size=y.shape)


def _generate_two_peak_constrained(x: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Compute clean signal + noise for the two-peak-constrained example.

    Ground truth:
        - p1 Gaussian:     amplitude=1.0, center=-0.5, fwhmg=0.3
        - p2 Pseudo-Voigt: amplitude=0.8, center=0.5 (= p1.center + 1.0),
                           fwhmg=0.25, fwhml=0.25
        - bg Linear:       slope=0.0, intercept=0.02
        - Noise: Gaussian, scale=0.02

    Args:
        x: x-axis array (200 points, -2 to 2).
        rng: Seeded random generator.

    Returns:
        Noisy intensity array.
    """
    y = (
        _gaussian(x, amplitude=1.0, center=-0.5, fwhmg=0.3)
        + _pseudovoigt(x, amplitude=0.8, center=0.5, fwhmg=0.25, fwhml=0.25)
        + _linear(x, slope=0.0, intercept=0.02)
    )
    return y + rng.normal(0.0, 0.02, size=y.shape)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

app = typer.Typer(
    help="Generate synthetic CSV data for SpectraFit v2 examples.",
    no_args_is_help=False,
)

_REPO_ROOT = Path(__file__).parent.parent


@app.command()
def main(
    seed: int = typer.Option(42, "--seed", help="Random seed for reproducibility."),
) -> None:
    """Write synthetic CSV files for all example directories.

    Args:
        seed: Integer seed passed to ``numpy.random.default_rng``.
    """
    rng = np.random.default_rng(seed)
    x = np.linspace(-2.0, 2.0, 200)

    _write_csv(
        path=_REPO_ROOT / "examples" / "basic" / "data.csv",
        x=x,
        y=_generate_basic(x, rng),
        label="basic/data.csv",
    )
    _write_csv(
        path=_REPO_ROOT / "examples" / "two-peak-constrained" / "data.csv",
        x=x,
        y=_generate_two_peak_constrained(x, rng),
        label="two-peak-constrained/data.csv",
    )


def _write_csv(path: Path, x: np.ndarray, y: np.ndarray, label: str) -> None:
    """Write a two-column (energy, intensity) CSV and print a green checkmark.

    Args:
        path: Destination file path (parent directories must already exist).
        x: Energy axis values.
        y: Intensity values.
        label: Short label printed in the success message.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"energy": x, "intensity": y}).to_csv(path, index=False)
    typer.echo(typer.style(f"✓  Written: {label}", fg=typer.colors.GREEN))


if __name__ == "__main__":
    app()

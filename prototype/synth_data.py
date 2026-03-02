"""Synthetic spectrum generator for the prototype fitting pipeline.

Generates a ``synth.csv`` file with known peak positions and noise, which can
be used as input data for the prototype fitting pipeline.

This module is self-contained — no imports from spectrafit.*.

Usage::

    uv run python prototype/synth_data.py

This writes ``prototype/synth.csv``.  The ground-truth component parameters
match the initial values in ``prototype/input.toml``.
"""

from __future__ import annotations

import sys

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import typer


# Allow running as a script from the repo root: ``python prototype/synth_data.py``
sys.path.insert(0, str(Path(__file__).parent))

from input_output_interface import ComponentSpec
from input_output_interface import FitParameterSpec
from model_functions import MODEL_REGISTRY


DEFAULT_SEED: int = 42

app = typer.Typer(
    help="Generate synthetic spectral data for prototype fitting.",
    no_args_is_help=False,
)


# ---------------------------------------------------------------------------
# Core generation functions
# ---------------------------------------------------------------------------


def clean_signal(
    x: np.ndarray,
    components: list[ComponentSpec],
) -> np.ndarray:
    """Evaluate and sum all model components over x.

    Each component is a validated :class:`ComponentSpec`; parameter values
    are extracted from ``spec.parameters[name].value`` — no raw dict access.

    Args:
        x: x-axis array.
        components: List of :class:`ComponentSpec` instances describing the
            ground-truth spectrum.

    Returns:
        1-D array of clean (noiseless) signal values.

    Raises:
        KeyError: If a component model name is not in MODEL_REGISTRY.
    """
    y = np.zeros_like(x, dtype=float)
    for spec in components:
        info = MODEL_REGISTRY[spec.model]
        kwargs = {name: ps.value for name, ps in spec.parameters.items()}
        y += info.function(x, **kwargs)
    return y


def add_noise(
    y: np.ndarray,
    mode: Literal["gaussian", "poisson", "none"] = "gaussian",
    scale: float = 0.02,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Add configurable noise to a signal array.

    Args:
        y: Clean signal array.
        mode: Noise type:
            - ``"gaussian"`` — additive white noise: ``y + N(0, scale)``.
            - ``"poisson"`` — Poisson counting noise: values are re-sampled
              via ``rng.poisson(y / scale) * scale`` (requires y ≥ 0).
            - ``"none"`` — no noise added; returns a copy of ``y``.
        scale: Noise scale parameter.  For Gaussian this is the standard
            deviation; for Poisson it is the count-rate normalisation factor.
        rng: Optional seeded numpy ``Generator``.  Defaults to
            ``np.random.default_rng(42)``.

    Returns:
        Noisy signal array (same shape as ``y``).

    Raises:
        ValueError: If ``mode`` is not one of the allowed values.
    """
    if rng is None:
        rng = np.random.default_rng(42)

    if mode == "none":
        return y.copy()

    if mode == "gaussian":
        return y + rng.normal(0.0, scale, size=y.shape)

    if mode == "poisson":
        y_safe = np.clip(y, 0.0, None)
        counts = rng.poisson(y_safe / scale)
        return counts.astype(float) * scale

    raise ValueError(
        f"Unknown noise mode {mode!r}. Use 'gaussian', 'poisson', or 'none'."
    )


def generate_spectrum(
    x_range: tuple[float, float] = (-2.0, 2.0),
    n_points: int = 200,
    components: list[ComponentSpec] | None = None,
    noise: Literal["gaussian", "poisson", "none"] = "gaussian",
    noise_scale: float = 0.02,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a synthetic spectrum DataFrame.

    The default ground-truth parameters match the initial values in
    ``prototype/input.toml``:
    - Gaussian peak: amplitude=1.0, center=-0.5, fwhmg=0.3
    - Pseudo-Voigt peak: amplitude=0.8, center=0.5, fwhmg=0.25, fwhml=0.2
    - Linear background: slope=0.0, intercept=0.02

    Args:
        x_range: ``(x_min, x_max)`` interval for the x-axis.
        n_points: Number of equally-spaced x points.
        components: List of ground-truth component dicts.  Uses the default
            two-peak + background spec when ``None``.
        noise: Noise model (``"gaussian"``, ``"poisson"``, or ``"none"``).
        noise_scale: Scale parameter for the noise model.
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns ``["energy", "intensity"]``.
    """
    if components is None:
        components = _default_components()

    x = np.linspace(x_range[0], x_range[1], n_points)
    y_clean = clean_signal(x, components)
    rng = np.random.default_rng(seed)
    y_noisy = add_noise(y_clean, mode=noise, scale=noise_scale, rng=rng)

    return pd.DataFrame({"energy": x, "intensity": y_noisy})


def _default_components() -> list[ComponentSpec]:
    """Ground-truth component spec matching ``prototype/input.toml``.

    Returns:
        List of :class:`ComponentSpec` instances with initial parameter values.
    """
    return [
        ComponentSpec(
            id="p1",
            model="gaussian",
            parameters={
                "amplitude": FitParameterSpec(value=1.0, bounds=[0.0, 3.0]),
                "center": FitParameterSpec(value=-0.5, bounds=[-2.0, 0.0]),
                "fwhmg": FitParameterSpec(value=0.3, bounds=[0.05, 1.0]),
            },
        ),
        ComponentSpec(
            id="p2",
            model="pseudovoigt",
            parameters={
                "amplitude": FitParameterSpec(value=0.8, bounds=[0.0, 3.0]),
                "center": FitParameterSpec(
                    value=0.5, vary=False, expr="p1.center + 1.0"
                ),
                "fwhmg": FitParameterSpec(value=0.25, bounds=[0.05, 1.0]),
                "fwhml": FitParameterSpec(value=0.25, vary=False, expr="p2.fwhmg"),
            },
        ),
        ComponentSpec(
            id="bg",
            model="linear",
            parameters={
                "slope": FitParameterSpec(value=0.0, vary=False),
                "intercept": FitParameterSpec(value=0.02, bounds=[0.0, 0.2]),
            },
        ),
    ]


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    output_path: Path = typer.Argument(
        None,
        help="Destination CSV file (defaults to prototype/synth.csv).",
    ),
    n_points: int = typer.Option(
        200, "--points", "-n", help="Number of x-axis points."
    ),
    noise: str = typer.Option(
        "gaussian", "--noise", help="Noise model: gaussian, poisson, none."
    ),
    noise_scale: float = typer.Option(
        0.02, "--noise-scale", help="Noise scale parameter."
    ),
    seed: int = typer.Option(42, "--seed", help="Random seed."),
) -> None:
    """Generate a synthetic spectrum and save it as CSV."""
    if output_path is None:
        output_path = Path(__file__).parent / "synth.csv"

    df = generate_spectrum(
        x_range=(-2.0, 2.0),
        n_points=n_points,
        noise=noise,  # type: ignore[arg-type]
        noise_scale=noise_scale,
        seed=seed,
    )

    df.to_csv(output_path, index=False)

    typer.echo(
        typer.style(f"Synthetic data written to: {output_path}", fg=typer.colors.GREEN)
    )
    typer.echo(f"Shape: {df.shape}")
    typer.echo(str(df.head()))


if __name__ == "__main__":
    app()

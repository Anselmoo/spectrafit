"""Three-panel matplotlib visualization for prototype fit results.

Produces a single figure with three stacked panels:

- **Top** — scatter of raw data with total fit overlay.
- **Middle** — residuals (data − fit) with ±1σ band.
- **Bottom** — individual component curves plus dashed total fit.

The figure can be:

- Saved to a PNG file via ``save_path``.
- Displayed interactively via ``show=True`` (attempts to switch backend).

This module is self-contained — zero imports from spectrafit.*.

Usage::

    from visualization import plot_fit_result
    save_path = plot_fit_result(output, show=False, save_path=Path("fit_plot.png"))
"""

from __future__ import annotations

import sys
import warnings

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np


# Use non-interactive backend by default — safe in headless / CI environments.
# Interactive mode is attempted only when show=True is passed to plot_fit_result.
matplotlib.use("Agg")

sys.path.insert(0, str(Path(__file__).parent))

from input_output_interface import ComponentResult
from input_output_interface import PrototypeOutput


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_FIGURE_DPI: int = 150
_FIGURE_SIZE: tuple[int, int] = (9, 10)
_AXIS_LABEL_SIZE: int = 11
_LEGEND_SIZE: int = 9
_GRID_STYLE: dict = {"ls": ":", "lw": 0.6, "alpha": 0.5}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _component_colors(n: int) -> list:
    """Return a qualitative colour palette for ``n`` components.

    Uses the ``tab10`` colormap (10 distinct colours); cycles if n > 10.

    Args:
        n: Number of colours required.

    Returns:
        List of matplotlib colour specs of length ``n``.
    """
    cmap = matplotlib.colormaps["tab10"]
    return [cmap(i % 10) for i in range(n)]
    """Return a qualitative colour palette for ``n`` components.

    Uses the ``tab10`` colormap (10 distinct colours); cycles if n > 10.

    Args:
        n: Number of colours required.

    Returns:
        List of matplotlib colour specs of length ``n``.
    """
    cmap = matplotlib.colormaps["tab10"]
    return [cmap(i % 10) for i in range(n)]


def _render_panel_fit(
    ax: plt.Axes,  # type: ignore[name-defined]
    x: np.ndarray,
    y_data: np.ndarray,
    y_fit: np.ndarray,
) -> None:
    """Render Panel 1: scatter data + total-fit line.

    Args:
        ax: Target matplotlib Axes.
        x: x-axis array.
        y_data: Observed intensity values.
        y_fit: Total fitted intensity values.
    """
    ax.scatter(x, y_data, s=8, color="dimgray", alpha=0.65, label="Data", zorder=2)
    ax.plot(x, y_fit, color="crimson", lw=1.8, label="Total fit", zorder=3)
    ax.set_ylabel("Intensity", fontsize=_AXIS_LABEL_SIZE)
    ax.legend(fontsize=_LEGEND_SIZE, framealpha=0.7)
    ax.set_title("Prototype Fit Result", fontsize=13, fontweight="bold")
    ax.grid(True, **_GRID_STYLE)


def _render_panel_residuals(
    ax: plt.Axes,  # type: ignore[name-defined]
    x: np.ndarray,
    residuals: np.ndarray,
) -> None:
    """Render Panel 2: residuals line with ±1σ shaded band.

    Args:
        ax: Target matplotlib Axes.
        x: x-axis array.
        residuals: ``y_data − y_fit`` array.
    """
    sigma = float(np.std(residuals))
    ax.plot(x, residuals, color="steelblue", lw=1.2, label="Residuals")
    ax.axhline(0.0, color="black", lw=0.9, ls="--")
    ax.fill_between(
        x,
        -sigma,
        sigma,
        color="steelblue",
        alpha=0.12,
        label=f"±1σ ({sigma:.3f})",
    )
    ax.set_ylabel("Residuals", fontsize=_AXIS_LABEL_SIZE)
    ax.legend(fontsize=_LEGEND_SIZE, framealpha=0.7)
    ax.grid(True, **_GRID_STYLE)


def _render_panel_components(
    ax: plt.Axes,  # type: ignore[name-defined]
    x: np.ndarray,
    y_fit: np.ndarray,
    components: list[ComponentResult],
) -> None:
    """Render Panel 3: individual component curves + dashed total fit.

    Args:
        ax: Target matplotlib Axes.
        x: x-axis array.
        y_fit: Total fitted intensity values (dashed overlay).
        components: List of per-component result objects.
    """
    colours = _component_colors(len(components))
    for comp, colour in zip(components, colours):
        ax.plot(
            x,
            np.array(comp.curve),
            color=colour,
            lw=1.5,
            label=f"{comp.id} ({comp.model})",
        )
    ax.plot(
        x,
        y_fit,
        color="crimson",
        lw=1.2,
        ls="--",
        alpha=0.6,
        label="Total fit",
        zorder=2,
    )
    ax.set_xlabel("Energy", fontsize=_AXIS_LABEL_SIZE)
    ax.set_ylabel("Intensity", fontsize=_AXIS_LABEL_SIZE)
    ax.legend(fontsize=_LEGEND_SIZE, framealpha=0.7)
    ax.grid(True, **_GRID_STYLE)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def plot_fit_result(
    output: PrototypeOutput,
    *,
    show: bool = False,
    save_path: Path | None = None,
) -> Path | None:
    """Create a three-panel fit-result figure.

    Panels:

    1. **Data + Total Fit** — grey scatter of raw data, coloured total-fit line.
    2. **Residuals** — ``y_data − y_fit`` line with ±1σ band.
    3. **Components** — individual component curves labelled by id, plus a
       dashed total-fit overlay.

    Args:
        output: Fitted :class:`~input_output_interface.PrototypeOutput`
            instance with all arrays populated.
        show: If ``True``, attempt to switch to an interactive backend and
            call ``plt.show()``.  A warning is emitted if this fails.
        save_path: File path to write the PNG.  Skipped when ``None``.

    Returns:
        Path where the PNG was saved, or ``None`` if ``save_path`` was not
        provided.
    """
    if show:
        try:
            matplotlib.use("TkAgg")
        except Exception as exc:  # noqa: BLE001
            warnings.warn(
                f"Interactive backend unavailable, falling back to Agg: {exc}",
                stacklevel=2,
            )

    x_arr = np.array(output.x)
    y_data_arr = np.array(output.y_data)
    y_fit_arr = np.array(output.y_fit)
    residuals = y_data_arr - y_fit_arr

    fig, axes = plt.subplots(
        3,
        1,
        figsize=_FIGURE_SIZE,
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1.5, 2.5]},
    )
    fig.subplots_adjust(hspace=0.08)

    _render_panel_fit(axes[0], x_arr, y_data_arr, y_fit_arr)
    _render_panel_residuals(axes[1], x_arr, residuals)
    _render_panel_components(axes[2], x_arr, y_fit_arr, output.components)

    saved: Path | None = None
    if save_path is not None:
        fig.savefig(save_path, dpi=_FIGURE_DPI, bbox_inches="tight")
        saved = save_path

    if show:
        try:
            plt.show()
        except Exception as exc:  # noqa: BLE001
            warnings.warn(f"Could not display plot: {exc}", stacklevel=2)

    plt.close(fig)
    return saved

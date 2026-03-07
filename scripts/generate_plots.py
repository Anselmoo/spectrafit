"""Generate fit-validation PNG plots for every SpectraFit v2 example.

For each ``examples/*/input.toml`` the script runs ``FittingPipeline``,
produces a 2-panel figure (data + fit components on top, residuals on bottom),
and writes ``examples/<name>/fit_validation.png``.

Usage::

    uv run python scripts/generate_plots.py
    uv run python scripts/generate_plots.py --show          # open interactive window
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl


mpl.use("Agg")  # Headless-safe; must be called before pyplot import

import matplotlib.pyplot as plt
import typer

from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.core.pipeline import FittingPipeline


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_EXAMPLES_DIR = _REPO_ROOT / "examples"
_GREEN = "\033[92m"
_RED = "\033[91m"
_RESET = "\033[0m"

app = typer.Typer(add_completion=False, pretty_exceptions_enable=False)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_config(input_toml: Path) -> UnifiedFittingConfig:
    """Load and patch a config so that *infile* resolves to an absolute path.

    The pipeline resolves ``infile`` relative to the current working directory.
    Patching it here ensures the script works regardless of the invocation CWD.

    Args:
        input_toml: Absolute path to the example ``input.toml``.

    Returns:
        A validated ``UnifiedFittingConfig`` with an absolute ``infile``.
    """
    raw = UnifiedFittingConfig.from_file(input_toml).model_dump()
    if raw.get("data") is not None:
        raw["data"]["infile"] = str((input_toml.parent / "data.csv").resolve())
    return UnifiedFittingConfig.model_validate(raw)


def _plot_example(input_toml: Path, *, show: bool) -> Path:
    """Run the pipeline for one example and save a validation figure.

    Args:
        input_toml: Absolute path to ``examples/<name>/input.toml``.
        show: When *True* open an interactive Matplotlib window after saving.

    Returns:
        Path to the saved PNG file.

    Raises:
        RuntimeError: If the fit did not converge.
    """
    example_name = input_toml.parent.name
    cfg = _load_config(input_toml)
    fit = FittingPipeline(config=cfg).run()

    if not fit.success:
        msg = f"Fit did not converge for '{example_name}': {fit.result.message}"
        raise RuntimeError(msg)

    df = fit.df
    component_ids = [c.id for c in cfg.components]

    # ── Figure layout ──────────────────────────────────────────────────────
    fig, (ax_fit, ax_res) = plt.subplots(
        2,
        1,
        figsize=(8, 6),
        sharex=True,
        gridspec_kw={"height_ratios": [3, 1]},
    )

    # ── Top panel: data + fit + individual components ──────────────────────
    ax_fit.scatter(df["energy"], df["intensity"], s=8, color="black", label="data", zorder=3)
    ax_fit.plot(df["energy"], df["fit"], color="red", lw=2, label="fit")

    colors = plt.cm.tab10.colors  # type: ignore[attr-defined]
    for i, cid in enumerate(component_ids):
        if cid in df.columns:
            ax_fit.plot(
                df["energy"],
                df[cid],
                "--",
                color=colors[i % 10],
                lw=1,
                label=cid,
            )

    ax_fit.set_ylabel("Intensity")
    ax_fit.legend(fontsize=8)
    ax_fit.set_title(f"{example_name} — fit validation")

    # ── Bottom panel: residuals ────────────────────────────────────────────
    ax_res.axhline(0, color="gray", lw=0.8, ls="--")
    ax_res.plot(df["energy"], df["residual"], color="steelblue", lw=1)
    ax_res.set_ylabel("Residual")
    ax_res.set_xlabel("Energy")

    fig.tight_layout()

    out_path = input_toml.parent / "fit_validation.png"
    fig.savefig(out_path, dpi=150)

    if show:
        plt.show()

    plt.close(fig)
    return out_path


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------


@app.command()
def main(
    show: bool = typer.Option(
        False,
        "--show",
        help="Open an interactive Matplotlib window for each plot (disabled in CI).",
    ),
) -> None:
    """Generate fit-validation plots for all examples and save them as PNG files.

    Args:
        show: When *True* open each figure interactively.  Defaults to *False*
              so the script is safe to run in headless / CI environments.
    """
    input_tomls = sorted(_EXAMPLES_DIR.glob("*/input.toml"))

    if not input_tomls:
        typer.echo(f"{_RED}✗ No input.toml files found under {_EXAMPLES_DIR}{_RESET}")
        raise typer.Exit(code=1)

    errors: list[tuple[str, str]] = []

    for input_toml in input_tomls:
        example_name = input_toml.parent.name
        try:
            out_path = _plot_example(input_toml, show=show)
            size_kb = out_path.stat().st_size // 1024
            typer.echo(f"{_GREEN}✓{_RESET}  {example_name}  →  {out_path}  ({size_kb} KB)")
        except Exception as exc:  # noqa: BLE001
            typer.echo(f"{_RED}✗  {example_name}: {exc}{_RESET}", err=True)
            errors.append((example_name, str(exc)))

    if errors:
        typer.echo(f"\n{_RED}{len(errors)} example(s) failed.{_RESET}", err=True)
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()

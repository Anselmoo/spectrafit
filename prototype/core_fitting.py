"""Clean lmfit fitting pipeline — the reference architecture prototype.

This module is intentionally self-contained — zero imports from spectrafit.*.

Design principles
-----------------
- **No nested for-loops over string keys.**  Components are processed as a
  typed ``list[ComponentSpec]`` via list-comprehensions and
  ``functools.reduce``.
- **Single naming function.**  All lmfit parameter names are built
  exclusively through :func:`~prototype.model_functions.lmfit_param_name`.
  No inline ``f"{a}_{b}"`` string formatting for parameter names elsewhere.
- **lmfit-native composition.**  ``model_all = m1 + m2 + ... + mn`` via
  lmfit's own ``__add__`` operator — no manual parameter dict iteration.
- **Pure functions.**  Every step is a standalone function; the orchestrator
  :func:`fit` sequences them.

Usage::

    uv run python prototype/core_fitting.py
"""

from __future__ import annotations

import functools
import operator
import sys

from pathlib import Path

import lmfit
import numpy as np
import pandas as pd
import typer


# Allow running as a script from the repo root
sys.path.insert(0, str(Path(__file__).parent))

from input_output_interface import ComponentResult
from input_output_interface import ComponentSpec
from input_output_interface import DataConfig
from input_output_interface import FitStatistics
from input_output_interface import ParameterResult
from input_output_interface import PrototypeInput
from input_output_interface import PrototypeOutput
from input_output_interface import SolverConfig
from model_functions import MODEL_REGISTRY
from model_functions import sanitize_component_id


app = typer.Typer(help="Prototype fitting pipeline.", no_args_is_help=True)


# ---------------------------------------------------------------------------
# Step 1 — Data loading
# ---------------------------------------------------------------------------


def load_data(config: DataConfig) -> tuple[np.ndarray, np.ndarray]:
    """Load x and y arrays from the CSV file specified in DataConfig.

    Args:
        config: Data configuration with file path and column names.

    Returns:
        Tuple ``(x, y)`` of 1-D float64 arrays.

    Raises:
        FileNotFoundError: If ``config.infile`` does not exist.
        KeyError: If the specified column names are absent.
    """
    df = pd.read_csv(config.infile)
    x = df[config.x_col].to_numpy(dtype=np.float64)
    y = df[config.y_col].to_numpy(dtype=np.float64)
    return x, y


# ---------------------------------------------------------------------------
# Step 2 — Build lmfit models
# ---------------------------------------------------------------------------


def make_lmfit_model(spec: ComponentSpec) -> lmfit.Model:
    """Create an lmfit.Model for a single ComponentSpec.

    The model prefix is ``f"{sanitized_id}_"`` so all parameter names are
    constructed as ``{sanitized_id}_{param_name}`` — matching the output of
    :func:`~prototype.model_functions.lmfit_param_name`.

    Args:
        spec: Validated component specification.

    Returns:
        An ``lmfit.Model`` wrapping the corresponding numpy function.
    """
    info = MODEL_REGISTRY[spec.model]
    prefix = f"{sanitize_component_id(spec.id)}_"
    return lmfit.Model(info.function, prefix=prefix, independent_vars=["x"])


def apply_hints(model: lmfit.Model, spec: ComponentSpec) -> None:
    """Apply parameter hints to an individual model via ``set_param_hint``.

    This is the idiomatic lmfit pattern: hints (value, min, max, vary, expr)
    are registered on the model BEFORE ``make_params()`` is called on the
    composite.  ``set_param_hint`` takes the un-prefixed field name; lmfit
    applies the component prefix internally.

    Cross-component ``expr`` values (e.g. ``"p1_center + 1.0"``) are already
    translated from dot-notation by :class:`FitParameterSpec`'s validator
    before reaching this function.

    Args:
        model: Individual lmfit.Model for this component.
        spec: Component specification with user constraints.
    """
    for field_name, constraint in spec.parameters.items():
        hint: dict = {
            "value": constraint.value,
            "min": constraint.min,
            "max": constraint.max,
            "vary": constraint.vary,
        }
        if constraint.expr is not None:
            hint["expr"] = constraint.expr
        model.set_param_hint(field_name, **hint)


def build_composite(
    specs: list[ComponentSpec],
) -> tuple[lmfit.Model, lmfit.Parameters, list[tuple[str, lmfit.Model]]]:
    """Build a composite lmfit model from a list of ComponentSpec objects.

    Uses ``functools.reduce(operator.add, ...)`` for lmfit-native composition
    via the model's ``__add__`` operator.  Each individual model is retained
    in ``parts`` for post-fit decomposition.

    Args:
        specs: Ordered list of component specifications.

    Returns:
        A 3-tuple ``(composite_model, params, parts)`` where:
        - ``composite_model`` is the summed lmfit model.
        - ``params`` is the merged lmfit.Parameters with all constraints applied.
        - ``parts`` is a list of ``(component_id, lmfit.Model)`` pairs.

    Raises:
        ValueError: If ``specs`` is empty.
    """
    if not specs:
        msg = "Cannot build a composite model from an empty component list."
        raise ValueError(msg)

    parts: list[tuple[str, lmfit.Model]] = [
        (spec.id, make_lmfit_model(spec)) for spec in specs
    ]
    # Hints applied to each individual model BEFORE composition so that
    # make_params() on the composite picks them up cleanly — including expr.
    for spec, (_, model) in zip(specs, parts, strict=True):
        apply_hints(model, spec)

    composite = functools.reduce(operator.add, (model for _, model in parts))
    params = composite.make_params()

    return composite, params, parts


# ---------------------------------------------------------------------------
# Step 3 — Fit
# ---------------------------------------------------------------------------


def run_fit(
    composite: lmfit.Model,
    params: lmfit.Parameters,
    x: np.ndarray,
    y: np.ndarray,
    solver: SolverConfig,
) -> lmfit.model.ModelResult:
    """Run the lmfit minimisation.

    Args:
        composite: Composite lmfit model (sum of all components).
        params: Initial parameters with constraints applied.
        x: x-axis data.
        y: Observed y-axis data.
        solver: Solver configuration (method, max_nfev, nan_policy).

    Returns:
        lmfit ModelResult after fitting.
    """
    return composite.fit(
        y,
        params,
        x=x,
        method=solver.method,
        max_nfev=solver.max_nfev,
        nan_policy=solver.nan_policy,
    )


# ---------------------------------------------------------------------------
# Step 4 — Decompose
# ---------------------------------------------------------------------------


def decompose(
    parts: list[tuple[str, lmfit.Model]],
    result_params: lmfit.Parameters,
    x: np.ndarray,
) -> dict[str, np.ndarray]:
    """Evaluate each component individually using the fitted parameters.

    This is a single dict-comprehension — no nested for-loops over string keys.

    Args:
        parts: List of ``(component_id, lmfit.Model)`` pairs.
        result_params: Fitted lmfit Parameters from the ModelResult.
        x: x-axis array.

    Returns:
        Dict mapping component id → fitted curve array.
    """
    return {cid: model.eval(result_params, x=x) for cid, model in parts}


# ---------------------------------------------------------------------------
# Step 5 — Extract results
# ---------------------------------------------------------------------------


def extract_statistics(result: lmfit.model.ModelResult) -> FitStatistics:
    """Extract summary fit statistics from an lmfit ModelResult.

    Args:
        result: Fitted lmfit ModelResult.

    Returns:
        :class:`~prototype.input_output_interface.FitStatistics` instance.
    """
    return FitStatistics(
        chi_squared=float(result.chisqr),
        redchi=float(result.redchi),
        nfev=int(result.nfev),
        ndata=int(result.ndata),
        nvarys=int(result.nvarys),
        nfree=int(result.nfree),
        success=bool(result.success),
        message=str(result.message),
    )


def extract_parameters(result: lmfit.model.ModelResult) -> list[ParameterResult]:
    """Extract per-parameter fit results from an lmfit ModelResult.

    Args:
        result: Fitted lmfit ModelResult.

    Returns:
        List of :class:`~prototype.input_output_interface.ParameterResult` objects.
    """
    return [
        ParameterResult(
            name=name,
            init_value=(
                float(param.init_value)
                if param.init_value is not None
                else float(param.value)
            ),
            best_value=float(param.value),
            stderr=float(param.stderr) if param.stderr is not None else None,
            vary=bool(param.vary),
            expr=param.expr,
        )
        for name, param in result.params.items()
    ]


# ---------------------------------------------------------------------------
# Step 6 — Orchestrator
# ---------------------------------------------------------------------------


def fit(
    input_path: Path,
    output_path: Path,
    *,
    show_plot: bool = False,
    save_plot: Path | None = None,
) -> PrototypeOutput:
    """Run the full fitting pipeline from input file to output JSON file.

    Pipeline steps:

    1. Load and validate input config.
    2. Load data CSV.
    3. Build composite model (no nested key loops).
    4. Run lmfit minimisation.
    5. Decompose per-component curves.
    6. Extract statistics and parameters.
    7. Generate and save plot PNG.
    8. Save ``output.json``.

    Args:
        input_path: Path to TOML/JSON/YAML input file.
        output_path: Path for the JSON output file.
        show_plot: If ``True``, display the plot interactively.
        save_plot: Optional path to save the plot PNG.  If ``None``,
            defaults to ``output_path.parent / "fit_plot.png"``.

    Returns:
        :class:`~prototype.input_output_interface.PrototypeOutput` with all
        results populated.
    """
    # 1 — Load config
    cfg = PrototypeInput.load(input_path)

    # Resolve infile relative to input_path's directory if not absolute
    if not cfg.data.infile.is_absolute():
        cfg.data.infile = input_path.parent / cfg.data.infile

    # 2 — Load data
    x, y = load_data(cfg.data)

    # 3 — Build composite model
    composite, params, parts = build_composite(cfg.components)

    # 4 — Fit
    result = run_fit(composite, params, x, y, cfg.solver)

    # 5 — Decompose
    component_curves = decompose(parts, result.params, x)

    # 6 — Extract results
    statistics = extract_statistics(result)
    parameters = extract_parameters(result)
    component_results = [
        ComponentResult(id=cid, model=spec.model, curve=curve.tolist())
        for (cid, _), spec, curve in zip(
            parts, cfg.components, component_curves.values(), strict=True
        )
    ]

    output = PrototypeOutput(
        input_snapshot=cfg.model_dump(mode="json"),
        statistics=statistics,
        parameters=parameters,
        components=component_results,
        x=x.tolist(),
        y_data=y.tolist(),
        y_fit=result.best_fit.tolist(),
    )

    # 7 — Generate plot
    plot_out = save_plot or (output_path.parent / "fit_plot.png")
    from visualization import plot_fit_result  # local import avoids circular deps

    plot_fit_result(output, show=show_plot, save_path=plot_out)

    # 8 — Save JSON
    output.save(output_path)

    return output


# ---------------------------------------------------------------------------
# Script entry point
# ---------------------------------------------------------------------------


@app.command()
def main(
    input_path: Path = typer.Argument(
        Path("prototype/input.toml"),
        help="Path to TOML/JSON/YAML input file.",
        exists=True,
    ),
    output_path: Path = typer.Option(
        None,
        "--output",
        "-o",
        help="Destination for the JSON output (defaults to <input_dir>/output.json).",
    ),
    show_plot: bool = typer.Option(False, "--show", help="Display plot interactively."),
) -> None:
    """Run the prototype fitting pipeline."""
    _base = input_path.parent
    if output_path is None:
        output_path = _base / "output.json"

    _result = fit(
        input_path=input_path,
        output_path=output_path,
        show_plot=show_plot,
        save_plot=_base / "fit_plot.png",
    )

    typer.echo(typer.style("\n=== Fit Statistics ===", bold=True))
    typer.echo(f"  chi²         : {_result.statistics.chi_squared:.6f}")
    typer.echo(f"  reduced chi² : {_result.statistics.redchi:.6f}")
    typer.echo(f"  nfev         : {_result.statistics.nfev}")
    typer.echo(f"  success      : {_result.statistics.success}")
    typer.echo(f"  message      : {_result.statistics.message}")

    typer.echo(typer.style("\n=== Fitted Parameters ===", bold=True))
    for p in _result.parameters:
        stderr_str = f" ± {p.stderr:.4f}" if p.stderr is not None else " (fixed)"
        typer.echo(f"  {p.name:<22s}: {p.best_value:.4f}{stderr_str}")

    typer.echo(typer.style(f"\nOutput saved to : {output_path}", fg=typer.colors.GREEN))
    typer.echo(
        typer.style(
            f"Plot saved to   : {_base / 'fit_plot.png'}", fg=typer.colors.GREEN
        )
    )


if __name__ == "__main__":
    app()

"""Scaffolding commands for SpectraFit CLI.

Provides ``init`` and ``new-config`` commands to bootstrap projects and
generate configuration files.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Annotated

import typer
import yaml

from spectrafit.cli._types import OutputFormatEnum
from spectrafit.cli._types import reset_keyboard_protocol
from spectrafit.models.registry import REGISTRY


# ---------------------------------------------------------------------------
# Default parameter values per common parameter name
# ---------------------------------------------------------------------------

_PARAM_DEFAULTS: dict[str, dict[str, object]] = {
    "amplitude": {"min": 0, "max": 2, "vary": True, "value": 1.0},
    "center": {"min": -2, "max": 2, "vary": True, "value": 0.0},
    "fwhmg": {"min": 0.02, "max": 0.5, "vary": True, "value": 0.1},
    "fwhml": {"min": 0.01, "max": 0.5, "vary": True, "value": 0.1},
    "fwhmv": {"min": 0.02, "max": 0.5, "vary": True, "value": 0.1},
    "gamma": {"min": 0.0, "max": 1.0, "vary": True, "value": 0.5},
    "sigma": {"min": 0.01, "max": 1.0, "vary": True, "value": 0.1},
    "width": {"min": 0.02, "max": 0.5, "vary": True, "value": 0.1},
    "slope": {"min": -10, "max": 10, "vary": True, "value": 0.0},
    "intercept": {"min": -10, "max": 10, "vary": True, "value": 0.0},
    "decay": {"min": 0.01, "max": 10, "vary": True, "value": 1.0},
    "exponent": {"min": 0.1, "max": 10, "vary": True, "value": 1.0},
    "skewness": {"min": -5, "max": 5, "vary": True, "value": 0.0},
    "kurtosis": {"min": -5, "max": 5, "vary": True, "value": 0.0},
    "coefficient0": {"min": -10, "max": 10, "vary": True, "value": 0.0},
    "coefficient1": {"min": -10, "max": 10, "vary": True, "value": 0.0},
    "coefficient2": {"min": -10, "max": 10, "vary": True, "value": 0.0},
    "coefficient3": {"min": -10, "max": 10, "vary": True, "value": 0.0},
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_for_param(name: str) -> dict[str, object]:
    """Return sensible default bounds for a parameter name.

    Args:
        name: Parameter name (e.g. ``"amplitude"``).

    Returns:
        Dictionary with ``min``, ``max``, ``vary``, and ``value`` keys.
    """
    return _PARAM_DEFAULTS.get(name, {"min": -1, "max": 1, "vary": True, "value": 0.0})


def _build_peak(model_name: str) -> dict[str, dict[str, object]]:
    """Build a single peak entry for a given model.

    Args:
        model_name: Registered model name (e.g. ``"gaussian"``).

    Returns:
        Nested dict ``{model_name: {param: defaults, ...}}``.
    """
    info = REGISTRY.get(model_name)
    return {model_name: {p: _default_for_param(p) for p in info.parameters}}


def _build_config(peaks: list[tuple[int, str]]) -> dict[str, object]:
    """Build a full SpectraFit configuration dictionary.

    Args:
        peaks: List of ``(peak_number, model_name)`` pairs.

    Returns:
        Complete configuration dict ready for serialisation.
    """
    peaks_dict: dict[str, object] = {
        str(num): _build_peak(model) for num, model in peaks
    }
    return {
        "fitting": {
            "description": {"project_name": "SpectraFit Project"},
            "parameters": {
                "minimizer": {"nan_policy": "propagate", "calc_covar": True},
                "optimizer": {"max_nfev": 1000, "method": "leastsq"},
            },
            "peaks": peaks_dict,
        },
    }


def _write_config(config: dict[str, object], path: Path, fmt: OutputFormatEnum) -> None:
    """Serialise *config* to *path* in the requested format.

    Args:
        config: Configuration dictionary.
        path: Target file path.
        fmt: Desired output format.
    """
    if fmt == OutputFormatEnum.JSON:
        with path.open("w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
            f.write("\n")
    elif fmt == OutputFormatEnum.YAML:
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    elif fmt == OutputFormatEnum.TOML:
        try:
            import tomli_w

            with path.open("wb") as f:
                tomli_w.dump(config, f)
        except ImportError:
            from spectrafit.cli.commands.convert import _dict_to_toml

            with path.open("w", encoding="utf-8") as f:
                f.write(_dict_to_toml(config))


def _config_to_stdout(config: dict[str, object], fmt: OutputFormatEnum) -> None:
    """Print *config* to stdout in the requested format.

    Args:
        config: Configuration dictionary.
        fmt: Desired output format.
    """
    if fmt == OutputFormatEnum.JSON:
        typer.echo(json.dumps(config, indent=2))
    elif fmt == OutputFormatEnum.YAML:
        typer.echo(
            yaml.dump(config, default_flow_style=False, sort_keys=False).rstrip(),
        )
    elif fmt == OutputFormatEnum.TOML:
        try:
            import tomli_w

            typer.echo(tomli_w.dumps(config))
        except ImportError:
            from spectrafit.cli.commands.convert import _dict_to_toml

            typer.echo(_dict_to_toml(config))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def init(
    project_name: Annotated[
        str,
        typer.Argument(help="Name of the project directory to create."),
    ],
    fmt: Annotated[
        OutputFormatEnum,
        typer.Option(
            "-f",
            "--format",
            help="Format for the template configuration file.",
        ),
    ] = OutputFormatEnum.JSON,
) -> None:
    """Scaffold a new SpectraFit fitting project.

    Creates a project directory with a template configuration file and
    standard sub-directories for data and results.
    """
    project_path = Path(project_name)

    if project_path.exists():
        reset_keyboard_protocol()
        overwrite = typer.confirm(
            f"Directory '{project_name}' already exists. Continue?",
            default=False,
        )
        if not overwrite:
            typer.echo("Aborted.")
            raise typer.Abort

    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "data").mkdir(exist_ok=True)
    (project_path / "results").mkdir(exist_ok=True)

    # Write template config with one gaussian peak
    config = _build_config([(1, "gaussian")])
    config_file = project_path / f"config.{fmt.value}"
    _write_config(config, config_file, fmt)

    typer.echo(f"✅ Project '{project_name}' created with structure:")
    typer.echo(f"   {project_name}/")
    typer.echo(f"   ├── config.{fmt.value}")
    typer.echo("   ├── data/")
    typer.echo("   └── results/")


def new_config(
    num_peaks: Annotated[
        int,
        typer.Option(
            "-n",
            "--num-peaks",
            help="Number of peaks to include.",
            min=1,
        ),
    ] = 1,
    model: Annotated[
        str,
        typer.Option(
            "-m",
            "--model",
            help="Model type for all peaks (e.g. gaussian, lorentzian, voigt).",
        ),
    ] = "gaussian",
    fmt: Annotated[
        OutputFormatEnum,
        typer.Option(
            "-f",
            "--format",
            help="Output format.",
        ),
    ] = OutputFormatEnum.JSON,
    output: Annotated[
        Path | None,
        typer.Option(
            "-o",
            "--output",
            help="Write config to file instead of stdout.",
        ),
    ] = None,
) -> None:
    """Generate a SpectraFit configuration file.

    Builds a valid configuration with sensible defaults for the chosen
    model type and writes it to stdout or a file.
    """
    # Validate model name
    if model not in REGISTRY:
        available = ", ".join(REGISTRY.names())
        typer.echo(f"❌ Unknown model '{model}'. Available: {available}", err=True)
        raise typer.Exit(1)

    peaks = [(i + 1, model) for i in range(num_peaks)]
    config = _build_config(peaks)

    if output is not None:
        _write_config(config, output, fmt)
        typer.echo(f"✅ Config written to {output}")
    else:
        _config_to_stdout(config, fmt)

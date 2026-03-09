"""Scaffolding commands for SpectraFit CLI.

Provides ``init`` and ``new-config`` commands to bootstrap projects and
generate configuration files.
"""

from __future__ import annotations

import json

from enum import Enum
from enum import unique
from pathlib import Path
from typing import Annotated

import tomli_w
import typer
import yaml

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.cli._types import OutputFormatEnum
from spectrafit.cli._types import reset_keyboard_protocol
from spectrafit.models.peak_models import Component
from spectrafit.models.peak_models import FitParameter
from spectrafit.models.registry import REGISTRY


# ---------------------------------------------------------------------------
# InitEnvironment + InitConfig — typed configuration capture
# ---------------------------------------------------------------------------


@unique
class InitEnvironment(str, Enum):
    """Target environment for the scaffolded project.

    Attributes:
        CLI: Generate a TOML configuration file only.
        JUPYTER: Generate a Jupyter ``.ipynb`` notebook only.
        BOTH: Generate both a TOML config and a notebook.

    Examples:
        >>> InitEnvironment.CLI == "cli"
        True
    """

    CLI = "cli"
    JUPYTER = "jupyter"
    BOTH = "both"


class InitConfig(BaseModel):
    """Typed configuration for the ``spectrafit init`` wizard.

    Attributes:
        project_name: Name of the project directory to create.
        environment: Target scaffolding environment (CLI / Jupyter / Both).
        output_dir: Parent directory where the project folder is created.
        overwrite: Whether to overwrite an existing project directory.
        fmt: Configuration file format (JSON / TOML / YAML).

    Examples:
        >>> cfg = InitConfig(project_name="my_project", environment=InitEnvironment.BOTH)
        >>> cfg.project_name
        'my_project'
    """

    model_config = ConfigDict(extra="forbid")

    project_name: str
    environment: InitEnvironment = InitEnvironment.CLI
    output_dir: Path = Field(default_factory=Path)
    overwrite: bool = False
    fmt: OutputFormatEnum = OutputFormatEnum.TOML


# ---------------------------------------------------------------------------
# Default parameter values per common parameter name
# ---------------------------------------------------------------------------

_PARAM_DEFAULTS: dict[str, FitParameter] = {
    "amplitude": FitParameter(value=1.0, min=0.0, max=2.0, vary=True),
    "center": FitParameter(value=0.0, min=-2.0, max=2.0, vary=True),
    "fwhmg": FitParameter(value=0.1, min=0.02, max=0.5, vary=True),
    "fwhml": FitParameter(value=0.1, min=0.01, max=0.5, vary=True),
    "fwhmv": FitParameter(value=0.1, min=0.02, max=0.5, vary=True),
    "gamma": FitParameter(value=0.5, min=0.0, max=1.0, vary=True),
    "sigma": FitParameter(value=0.1, min=0.01, max=1.0, vary=True),
    "width": FitParameter(value=0.1, min=0.02, max=0.5, vary=True),
    "slope": FitParameter(value=0.0, min=-10.0, max=10.0, vary=True),
    "intercept": FitParameter(value=0.0, min=-10.0, max=10.0, vary=True),
    "decay": FitParameter(value=1.0, min=0.01, max=10.0, vary=True),
    "exponent": FitParameter(value=1.0, min=0.1, max=10.0, vary=True),
    "skewness": FitParameter(value=0.0, min=-5.0, max=5.0, vary=True),
    "kurtosis": FitParameter(value=0.0, min=-5.0, max=5.0, vary=True),
    "coefficient0": FitParameter(value=0.0, min=-10.0, max=10.0, vary=True),
    "coefficient1": FitParameter(value=0.0, min=-10.0, max=10.0, vary=True),
    "coefficient2": FitParameter(value=0.0, min=-10.0, max=10.0, vary=True),
    "coefficient3": FitParameter(value=0.0, min=-10.0, max=10.0, vary=True),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _default_for_param(name: str) -> FitParameter:
    """Return sensible default bounds for a parameter name.

    Args:
        name: Parameter name (e.g. ``"amplitude"``).

    Returns:
        :class:`~spectrafit.models.peak_models.FitParameter` with sensible defaults.
    """
    return _PARAM_DEFAULTS.get(name, FitParameter(value=0.0, min=-1.0, max=1.0))


def _build_component(model_name: str, num: int) -> Component:
    """Build a single :class:`~spectrafit.models.peak_models.Component` for *model_name*.

    Args:
        model_name: Registered model name (e.g. ``"gaussian"``).
        num: Peak number used as the component ``id``.

    Returns:
        Validated :class:`~spectrafit.models.peak_models.Component` instance.
    """
    info = REGISTRY.get(model_name)
    return Component(
        id=str(num),
        model=model_name,
        parameters={p: _default_for_param(p) for p in info.parameters},
    )


def _build_config(peaks: list[tuple[int, str]]) -> dict[str, object]:
    """Build a full SpectraFit v2 configuration dictionary.

    The returned dict uses the v2 ``components`` format accepted by
    :class:`~spectrafit.core.fitting_config.UnifiedFittingConfig`.

    Args:
        peaks: List of ``(peak_number, model_name)`` pairs.

    Returns:
        Complete v2 configuration dict ready for serialisation.
    """
    components = [_build_component(model, num) for num, model in peaks]
    return {
        "components": [c.model_dump(exclude_none=True) for c in components],
        "minimizer": {"nan_policy": "propagate", "calc_covar": True},
        "optimizer": {"max_nfev": 1000, "method": "leastsq"},
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
        with path.open("wb") as f:
            tomli_w.dump(config, f)


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
        typer.echo(tomli_w.dumps(config))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


def _run_init(cfg: InitConfig) -> None:
    """Execute the scaffolding described by *cfg*.

    Shared implementation called from both the interactive wizard path and
    the non-interactive CLI flag path.

    Args:
        cfg: Validated :class:`InitConfig` capturing all user choices.
    """
    from rich.console import Console

    console = Console()
    project_path = cfg.output_dir / cfg.project_name

    if project_path.exists() and not cfg.overwrite:
        reset_keyboard_protocol()
        if not typer.confirm(
            f"Directory '{project_path}' already exists. Overwrite?", default=False
        ):
            typer.echo("Aborted.")
            raise typer.Abort

    # Create directory structure
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "data").mkdir(exist_ok=True)
    (project_path / "results").mkdir(exist_ok=True)

    generated: list[str] = []

    # --- CLI config file ---
    if cfg.environment in (InitEnvironment.CLI, InitEnvironment.BOTH):
        config = _build_config([(1, "gaussian")])
        config_file = project_path / f"config.{cfg.fmt.value}"
        _write_config(config, config_file, cfg.fmt)
        generated.append(f"config.{cfg.fmt.value}")

    # --- Jupyter notebook ---
    if cfg.environment in (InitEnvironment.JUPYTER, InitEnvironment.BOTH):
        from spectrafit.jupyter.templates.starter_nb import write_starter_notebook

        nb_path = project_path / "spectrafit_getting_started.ipynb"
        write_starter_notebook(cfg.project_name, nb_path)
        generated.append("spectrafit_getting_started.ipynb")

    # --- spectrafit.toml project meta file ---
    from spectrafit import __version__
    from spectrafit.models.project_config import ProjectConfig
    from spectrafit.models.project_config import ProjectFiles
    from spectrafit.models.project_config import ProjectMeta

    pc = ProjectConfig(
        project=ProjectMeta(
            name=cfg.project_name,
            description=f"SpectraFit project: {cfg.project_name}",
            spectrafit_version=__version__,
            files=ProjectFiles(
                default_notebook=(
                    "spectrafit_getting_started.ipynb"
                    if cfg.environment
                    in (InitEnvironment.JUPYTER, InitEnvironment.BOTH)
                    else ""
                ),
                default_config=(
                    f"config.{cfg.fmt.value}"
                    if cfg.environment in (InitEnvironment.CLI, InitEnvironment.BOTH)
                    else ""
                ),
            ),
        )
    )
    meta_path = project_path / "spectrafit.toml"
    with meta_path.open("wb") as fh:
        tomli_w.dump(pc.to_toml_dict(), fh)
    generated.append("spectrafit.toml")

    # --- Summary output ---
    from rich.panel import Panel
    from rich.text import Text

    tree_lines = [
        f"[cyan]{cfg.project_name}/[/cyan]",
        *[f"  [green]├── {name}[/green]" for name in generated],
        "  [green]├── data/[/green]",
        "  [green]└── results/[/green]",
    ]

    summary = Text.from_markup(
        "[bold green]✅ Project created[/bold green]\n\n"
        + "\n".join(tree_lines)
        + "\n\n"
        + "[dim]Next:[/dim] "
        + "[cyan]cd "
        + cfg.project_name
        + " && spectrafit fit data/<file> config."
        + cfg.fmt.value
        + "[/cyan]"
    )
    console.print(Panel(summary, border_style="bright_blue"))


def init(
    project_name: Annotated[
        str | None,
        typer.Argument(help="Name of the project directory to create."),
    ] = None,
    cli_flag: Annotated[
        bool,
        typer.Option(
            "--cli",
            help="Scaffold a TOML configuration file only (non-interactive).",
        ),
    ] = False,
    jupyter_flag: Annotated[
        bool,
        typer.Option(
            "--jupyter",
            help="Scaffold a Jupyter notebook only (non-interactive).",
        ),
    ] = False,
    both_flag: Annotated[
        bool,
        typer.Option(
            "--both",
            help="Scaffold both a TOML config and a Jupyter notebook.",
        ),
    ] = False,
    output_dir: Annotated[
        Path,
        typer.Option(
            "-o",
            "--output-dir",
            help="Parent directory for the new project.",
        ),
    ] = Path(),
    fmt: Annotated[
        OutputFormatEnum,
        typer.Option(
            "-f",
            "--format",
            help="Format for the template configuration file.",
        ),
    ] = OutputFormatEnum.TOML,
    overwrite: Annotated[
        bool,
        typer.Option(
            "--overwrite",
            help="Overwrite an existing project directory without prompting.",
        ),
    ] = False,
) -> None:
    r"""Scaffold a new SpectraFit fitting project.

    Without flags, launches an **interactive Rich wizard** that asks for the
    project name and target environment.  Pass ``--cli``, ``--jupyter``, or
    ``--both`` to skip the wizard and create files immediately.

    \b
    Examples:
        spectrafit init                          # interactive wizard
        spectrafit init my_rixs --cli            # TOML config only
        spectrafit init my_rixs --jupyter        # notebook only
        spectrafit init my_rixs --both           # config + notebook
        spectrafit init my_rixs --both -f toml   # with TOML format
    """
    # --- Determine environment from flags ---
    if sum([cli_flag, jupyter_flag, both_flag]) > 1:
        typer.echo(
            typer.style(
                "❌ Specify at most one of --cli, --jupyter, --both.",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(1)

    if cli_flag:
        env = InitEnvironment.CLI
    elif jupyter_flag:
        env = InitEnvironment.JUPYTER
    elif both_flag:
        env = InitEnvironment.BOTH
    else:
        env = None  # will be resolved by wizard

    # --- Non-interactive path (flags + name provided) ---
    if env is not None and project_name is not None:
        _run_init(
            InitConfig(
                project_name=project_name,
                environment=env,
                output_dir=output_dir,
                overwrite=overwrite,
                fmt=fmt,
            )
        )
        return

    # --- Interactive Rich wizard ---
    from rich.console import Console
    from rich.prompt import Prompt

    console = Console()

    console.print("[bold]SpectraFit Init Wizard[/bold]\n")

    resolved_name: str = project_name or Prompt.ask(
        "[cyan]Project name[/cyan]", default="my_spectrafit_project"
    )

    if env is None:
        env_choice = Prompt.ask(
            "[cyan]Environment[/cyan]",
            choices=["cli", "jupyter", "both"],
            default="cli",
        )
        env = InitEnvironment(env_choice)

    _run_init(
        InitConfig(
            project_name=resolved_name,
            environment=env,
            output_dir=output_dir,
            overwrite=overwrite,
            fmt=fmt,
        )
    )


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
    ] = OutputFormatEnum.TOML,
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
        typer.echo(
            typer.style(
                f"❌ Unknown model '{model}'. Available: {available}",
                fg=typer.colors.RED,
            ),
            err=True,
        )
        raise typer.Exit(1)

    peaks = [(i + 1, model) for i in range(num_peaks)]
    config = _build_config(peaks)

    if output is not None:
        _write_config(config, output, fmt)
        typer.echo(typer.style(f"✅ Config written to {output}", fg=typer.colors.GREEN))
    else:
        _config_to_stdout(config, fmt)

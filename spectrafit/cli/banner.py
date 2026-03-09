"""Rich startup banner for the SpectraFit CLI."""

from __future__ import annotations

import importlib.metadata
import platform
import random
import sys

from pathlib import Path
from typing import TYPE_CHECKING

from rich.panel import Panel
from rich.text import Text

from spectrafit.models.fitting_context import EnvironmentMode
from spectrafit.models.fitting_context import detect_environment


if TYPE_CHECKING:
    from rich.console import Console


# ---------------------------------------------------------------------------
# Rotating tips shown in the banner footer
# ---------------------------------------------------------------------------
_TIPS: list[str] = [
    "Run [bold cyan]spectrafit fit --help[/] to see all fit options.",
    "Use [bold cyan]spectrafit init[/] to scaffold a new project with a starter config.",
    "Combine [bold cyan]--jupyter[/] with init to generate a reference notebook.",
    "Pipe a config via stdin: [bold cyan]cat config.toml | spectrafit fit data.csv -[/]",
    "Run [bold cyan]spectrafit new-config -m voigt -n 3[/] to generate a 3-peak template.",
    "Add [bold cyan]--noplot[/] to skip plot generation in non-interactive runs.",
    "Use [bold cyan]spectrafit validate config.toml[/] to check your config before fitting.",
    "Try [bold cyan]spectrafit report --help[/] for HTML, PDF, and Excel reports.",
]


def _env_label(env: EnvironmentMode) -> str:
    """Return the Rich colour name for an environment mode.

    Args:
        env: Current runtime environment.

    Returns:
        Colour name string (e.g. ``"green"``) for use in Rich style tuples.
    """
    colours = {
        EnvironmentMode.CLI: "green",
        EnvironmentMode.NOTEBOOK: "magenta",
        EnvironmentMode.API: "yellow",
    }
    return colours.get(env, "white")


def render_startup_panel(console: Console, env: EnvironmentMode | None = None) -> None:
    """Render a Rich startup panel to *console*.

    The panel is **suppressed** when stdout is not a terminal (e.g. CI, piped
    output) so it never pollutes non-interactive output streams.

    Args:
        console: Rich :class:`~rich.console.Console` instance to render into.
        env: Runtime environment; auto-detected if ``None``.

    Examples:
        >>> from rich.console import Console
        >>> from spectrafit.cli.banner import render_startup_panel
        >>> render_startup_panel(Console(force_terminal=False))
    """
    if not console.is_terminal:
        return

    if env is None:
        env = detect_environment()

    try:
        version = importlib.metadata.version("spectrafit")
    except importlib.metadata.PackageNotFoundError:
        version = "dev"

    py_ver = (
        f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    cwd = Path.cwd().name
    tip = random.choice(_TIPS)  # noqa: S311 — cosmetic only, not security-sensitive

    content = Text.assemble(
        ("SpectraFit ", "bold white"),
        (f"v{version}", "bold cyan"),
        "  |  Python ",
        (py_ver, "cyan"),
        "  |  ",
        platform.system(),
        "\n",
        "Environment: ",
        (env.value.upper(), _env_label(env)),
        "  |  Working dir: ",
        (cwd, "dim"),
        "\n\n",
        Text.from_markup(f"[dim]{tip}[/dim]"),
    )

    console.print(
        Panel(
            content,
            title="[bold magenta]SpectraFit[/bold magenta]",
            subtitle="[dim]https://anselmoo.github.io/spectrafit/[/dim]",
            border_style="bright_blue",
            padding=(0, 2),
        )
    )

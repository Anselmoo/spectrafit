"""Mössbauer spectroscopy plugin for SpectraFit.

This plugin provides Mössbauer spectroscopy models and utilities.
"""

from __future__ import annotations

import typer

from spectrafit.plugins.protocol import SpectraFitPlugin


class MoessbauerPlugin:
    """Mössbauer spectroscopy plugin.

    Provides mathematical models for Mössbauer spectroscopy including
    singlet, doublet, sextet, and octet patterns.
    """

    name = "moessbauer"
    version = "1.0.0"
    description = (
        "Mössbauer spectroscopy models for singlet, doublet, sextet, and octet patterns"
    )

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register Mössbauer-related commands with the parent Typer app.

        Args:
            parent_app: The parent Typer application to register commands with.
        """

        @parent_app.command(name="moessbauer-info")
        def moessbauer_info() -> None:
            """Display information about Mössbauer spectroscopy models.

            Shows available Mössbauer models and their parameters.
            """
            typer.echo("\n🔬 Mössbauer Spectroscopy Models\n")
            typer.echo("Available models:")
            typer.echo("  • moessbauer_singlet  - Single absorption line")
            typer.echo("  • moessbauer_doublet  - Two-line quadrupole splitting")
            typer.echo(
                "  • moessbauer_sextet   - Six-line magnetic hyperfine splitting"
            )
            typer.echo("  • moessbauer_octet    - Eight-line complex pattern")
            typer.echo(
                "\nThese models are available for use in fitting configuration files."
            )
            typer.echo(
                "\nFor detailed documentation, visit: "
                "https://anselmoo.github.io/spectrafit/\n"
            )

    def register_models(self) -> list[type]:
        """Return list of Pydantic models this plugin provides.

        Returns:
            List of Mössbauer-related Pydantic models.
        """
        try:
            from spectrafit.api.physical_constants import (  # noqa: PLC0415
                MoessbauerConstants,
            )
        except ImportError:
            return []
        else:
            return [MoessbauerConstants]


# Verify protocol implementation at module load time
if __name__ != "__main__":
    _plugin_instance = MoessbauerPlugin()
    if not isinstance(_plugin_instance, SpectraFitPlugin):
        msg = "MoessbauerPlugin does not implement SpectraFitPlugin protocol"
        raise TypeError(msg)

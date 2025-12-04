"""RIXS Visualizer plugin for SpectraFit.

This plugin provides interactive RIXS plane visualization capabilities.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Annotated

import typer


if TYPE_CHECKING:
    from pathlib import Path

from spectrafit.plugins.protocol import SpectraFitPlugin


class RIXSPlugin:
    """RIXS Visualizer plugin.

    Provides interactive 2D/3D visualization for Resonant Inelastic X-ray
    Scattering (RIXS) data.
    """

    name = "rixs"
    version = "1.0.0"
    description = "Interactive RIXS plane viewer for 2D/3D visualization"

    def register_commands(self, parent_app: typer.Typer) -> None:
        """Register RIXS visualizer command with the parent Typer app.

        Args:
            parent_app: The parent Typer application to register commands with.
        """

        @parent_app.command(name="rixs")
        def rixs(
            infile: Annotated[
                Path,
                typer.Argument(
                    help="Input file for RIXS data (json, toml, npy, or npz format).",
                    exists=True,
                    file_okay=True,
                    dir_okay=False,
                    readable=True,
                ),
            ],
            port: Annotated[
                int,
                typer.Option(
                    "-p",
                    "--port",
                    help="Port for the Dash server.",
                ),
            ] = 8050,
            debug: Annotated[
                bool,
                typer.Option(
                    "-d",
                    "--debug",
                    help="Run in debug mode.",
                ),
            ] = False,
        ) -> None:
            """Launch the RIXS Visualizer for interactive 2D/3D visualization.

            The RIXS Visualizer is an interactive tool for viewing Resonant Inelastic
            X-ray Scattering (RIXS) data in a 2D plane with 3D surface visualization.

            Supported input formats:
            - JSON (.json)
            - TOML (.toml)
            - NumPy binary (.npy, .npz)

            The input file should contain:
            - incident_energy: 1D array of incident energies
            - emission_energy: 1D array of emission energies
            - rixs_map: 2D array of RIXS intensities
            """
            try:
                from spectrafit.plugins.rixs_visualizer import RIXSApp  # noqa: PLC0415
                from spectrafit.plugins.rixs_visualizer import (  # noqa: PLC0415
                    RIXSVisualizer,
                )

                typer.echo(f"📊 Loading RIXS data from '{infile}'...")
                data = RIXSVisualizer.load_data(infile)

                typer.echo(f"🚀 Starting RIXS Visualizer on port {port}...")
                typer.echo("   Press Ctrl+C to stop the server.\n")

                app = RIXSApp(
                    incident_energy=data.incident_energy,
                    emission_energy=data.emission_energy,
                    rixs_map=data.rixs_map,
                    port=port,
                    debug=debug,
                )
                app.app_run()

            except ImportError as e:
                typer.echo(
                    "❌ RIXS Visualizer dependencies are not installed.",
                    err=True,
                )
                typer.echo(
                    "   Install with: pip install spectrafit[jupyter-dash]",
                    err=True,
                )
                typer.echo(f"\n   Error: {e}", err=True)
                raise typer.Exit(1) from e
            except ValueError as e:
                typer.echo(f"❌ Error loading RIXS data: {e}", err=True)
                raise typer.Exit(1) from e
            except Exception as e:
                typer.echo(f"❌ Unexpected error: {e}", err=True)
                raise typer.Exit(1) from e

    def register_models(self) -> list[type]:
        """Return list of Pydantic models this plugin provides.

        Returns:
            List of RIXS-related Pydantic models.
        """
        try:
            from spectrafit.api.rixs_model import MainTitleAPI  # noqa: PLC0415
            from spectrafit.api.rixs_model import RIXSModelAPI  # noqa: PLC0415
            from spectrafit.api.rixs_model import SizeRatioAPI  # noqa: PLC0415
            from spectrafit.api.rixs_model import XAxisAPI  # noqa: PLC0415
            from spectrafit.api.rixs_model import YAxisAPI  # noqa: PLC0415
            from spectrafit.api.rixs_model import ZAxisAPI  # noqa: PLC0415
        except ImportError:
            return []
        else:
            return [
                RIXSModelAPI,
                SizeRatioAPI,
                XAxisAPI,
                YAxisAPI,
                ZAxisAPI,
                MainTitleAPI,
            ]


# Verify protocol implementation at module load time
if __name__ != "__main__":
    _plugin_instance = RIXSPlugin()
    if not isinstance(_plugin_instance, SpectraFitPlugin):
        msg = "RIXSPlugin does not implement SpectraFitPlugin protocol"
        raise TypeError(msg)

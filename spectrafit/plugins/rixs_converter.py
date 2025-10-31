"""Transform the raw pkl data into a JSON, TOML, or numpy file for RIXS."""

from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any
from typing import Optional

import numpy as np
import tomli_w
import typer

from spectrafit.api.rixs_model import RIXSModelAPI
from spectrafit.plugins.converter import Converter
from spectrafit.tools import pkl2any
from spectrafit.tools import pure_fname


if TYPE_CHECKING:
    from collections.abc import MutableMapping

choices_fformat = {"latin1", "utf-8", "utf-16", "utf-32"}
choices_export = {"json", "toml", "lock", "npy", "npz"}
choices_mode = {"sum", "mean"}

# Create Typer app
app = typer.Typer(
    help="Convert 'SpectraFit' pickle files to JSON, TOML, or numpy formats for RIXS-Visualizer.",
    add_completion=False,
)


class RIXSConverter(Converter):
    """Convert raw pickle data into JSON, TOML, or numpy formats."""

    @staticmethod
    def convert(infile: Path, file_format: str) -> MutableMapping[str, Any]:
        """Convert the pkl file to a dictionary.

        Args:
            infile (Path): The input file.
            file_format (str): The file format for the optional encoding of the pickle
                file.

        Returns:
            MutableMapping[str, Any]: The data dictionary from the pkl file.

        """
        data_dict = {}
        for _dict in pkl2any(infile, file_format):
            data_dict.update(_dict)
        return data_dict

    def create_rixs(
        self,
        data: MutableMapping[str, Any],
        incident_energy: str,
        emission_energy: str,
        rixs_map: str,
        mode: str,
    ) -> RIXSModelAPI:
        """Create the RIXS map from the pkl file.

        Args:
            data (MutableMapping[str, Any]): The data dictionary from the pkl file.
            incident_energy (str): The name of the incident energy.
            emission_energy (str): The name of the emitted energy.
            rixs_map (str): The name of the RIXS map.
            mode (str): The mode of the RIXS map post-processing, e.g. 'sum' or 'max'.

        Raises:
            ValueError: If the mode is not in the choices.
            KeyError: If the incident energy, emission energy, or RIXS map is not in
                the data.

        Returns:
            RIXSModelAPI: The RIXS map as a RIXSModelAPI pydantic object.

        """
        if mode not in choices_mode:
            msg = f"Mode '{mode}' not in {choices_mode}."
            raise ValueError(msg)
        if incident_energy not in data:
            self.raise_error(incident_energy, data)
        if emission_energy not in data:
            self.raise_error(incident_energy, data)
        if rixs_map not in data:
            self.raise_error(incident_energy, data)

        if mode == "sum":
            rixs_val = np.sum(data[rixs_map], axis=0)
        elif mode == "mean":
            rixs_val = np.mean(data[rixs_map], axis=0)
        return RIXSModelAPI(
            incident_energy=data[incident_energy],
            emission_energy=data[emission_energy],
            rixs_map=rixs_val,
        )

    @staticmethod
    def raise_error(wrong_key: str, data: Any) -> None:
        """Raise an error if the key is not in the data.

        Args:
            wrong_key (str): The key which is not in the data.
            data (Any): The data dictionary from the pkl file.

        Raises:
            KeyError: If the key is not in the data.

        """
        msg = f"Key '{wrong_key}' not in data. Aailable keys are: {list(data.keys())}."
        raise KeyError(
            msg,
        )

    def save(self, data: Any, fname: Path, export_format: str) -> None:
        """Save the data to a file.

        Args:
            data (Any): The data to save.
            fname (Path): The filename.
            export_format (str): The file extension for the export.

        Raises:
            ValueError: If the export format is not in the choices.

        """
        if export_format not in choices_export:
            msg = f"Export format '{export_format}' not in {choices_export}."
            raise ValueError(
                msg,
            )

        if export_format == "json":
            with (
                pure_fname(fname)
                .with_suffix(f".{export_format}")
                .open("w", encoding="utf-8")
            ) as f:
                json.dump(self.numpydict2listdict(data), f, indent=4)
        elif export_format in {"toml", "lock"}:
            with pure_fname(fname).with_suffix(f".{export_format}").open("wb") as f:
                tomli_w.dump(self.numpydict2listdict(data), f, multiline_strings=False)
        elif export_format == "npy":
            np.save(pure_fname(fname).with_suffix(f".{export_format}"), data)
        elif export_format == "npz":
            np.savez(pure_fname(fname).with_suffix(f".{export_format}"), **data)

    @staticmethod
    def numpydict2listdict(data: MutableMapping[str, Any]) -> MutableMapping[str, Any]:
        """Convert a dictionary with numpy arrays to a dictionary with lists.

        Args:
            data (MutableMapping[str, Any]): The data dictionary.

        Returns:
            MutableMapping[str, Any]: The data dictionary with lists.

        """
        return {k: v.tolist() for k, v in data.items()}


@app.command()
def cli_main(
    infile: Annotated[
        Path, typer.Argument(help="Path to the pickle file to be converted.")
    ],
    file_format: Annotated[
        str,
        typer.Option(
            "-f",
            "--file-format",
            help="Encoding format of the pickle file (default: 'latin1').",
        ),
    ] = "latin1",
    export_format: Annotated[
        str,
        typer.Option(
            "-e",
            "--export-format",
            help="Desired export file format (default: 'json').",
        ),
    ] = "json",
    incident_energy: Annotated[
        str | None,
        typer.Option(
            "-ie",
            "--incident-energy",
            help="Label for the incident energy.",
        ),
    ] = None,
    emission_energy: Annotated[
        str | None,
        typer.Option(
            "-ee",
            "--emission-energy",
            help="Label for the emitted energy.",
        ),
    ] = None,
    rixs_map: Annotated[
        str | None,
        typer.Option(
            "-rm",
            "--rixs-map",
            help="Label for the RIXS map.",
        ),
    ] = None,
    mode: Annotated[
        str,
        typer.Option(
            "-m",
            "--mode",
            help="Post-processing mode for the RIXS map (default: 'sum').",
        ),
    ] = "sum",
) -> None:
    """Convert pickle files to JSON, TOML, or numpy formats for RIXS."""
    # Validate choices
    if file_format not in choices_fformat:
        typer.echo(
            f"Error: Invalid file format '{file_format}'. "
            f"Choose from: {', '.join(sorted(choices_fformat))}",
            err=True,
        )
        raise typer.Exit(1)
    if export_format not in choices_export:
        typer.echo(
            f"Error: Invalid export format '{export_format}'. "
            f"Choose from: {', '.join(sorted(choices_export))}",
            err=True,
        )
        raise typer.Exit(1)
    if mode not in choices_mode:
        typer.echo(
            f"Error: Invalid mode '{mode}'. "
            f"Choose from: {', '.join(sorted(choices_mode))}",
            err=True,
        )
        raise typer.Exit(1)

    # Create converter instance and run conversion
    converter = RIXSConverter()
    try:
        data = converter.convert(infile, file_format)
        rixs_data = converter.create_rixs(
            data=data,
            incident_energy=incident_energy,
            emission_energy=emission_energy,
            rixs_map=rixs_map,
            mode=mode,
        )
        converter.save(
            data=rixs_data.model_dump(),
            fname=infile,
            export_format=export_format,
        )
        typer.echo(f"Successfully converted {infile}")
    except (ValueError, TypeError) as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def command_line_runner() -> None:
    """Entry point for the RIXS converter CLI."""
    app()

"""Transform the raw pkl data into a JSON, TOML, or numpy file for RIXS."""

import argparse
import json

from pathlib import Path
from typing import Any
from typing import Dict
from typing import MutableMapping

import numpy as np
import tomli_w

from spectrafit.api.rixs_model import RIXSModelAPI
from spectrafit.plugins.converter import Converter
from spectrafit.tools import pkl2any
from spectrafit.tools import pure_fname


choices_fformat = {"latin1", "utf-8", "utf-16", "utf-32"}
choices_export = {"json", "toml", "lock", "npy", "npz"}
choices_mode = {"sum", "mean"}


class RIXSConverter(Converter):
    """Transform the raw pkl data into a JSON, TOML, or numpy file for RIXS."""

    def get_args(self) -> Dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                additional information beyond the command line arguments.
        """
        parser = argparse.ArgumentParser(
            description="Converter for 'SpectraFit' from pkl files to a JSON, TOML, "
            "or numpy file for RIXS-Visualizer."
        )
        parser.add_argument(
            "infile",
            type=Path,
            help="Filename of the pkl file to convert to JSON, TOML, or numpy.",
        )
        parser.add_argument(
            "-f",
            "--file-format",
            help="File format for the optional encoding of the pickle file."
            " Default is 'latin1'.",
            type=str,
            default="latin1",
            choices=choices_fformat,
        )
        parser.add_argument(
            "-e",
            "--export-format",
            help="File extension for the export.",
            type=str,
            default="json",
            choices=choices_export,
        )
        parser.add_argument(
            "-ie",
            "--incident_energy",
            help="Name of the incident energy",
            type=str,
        )
        parser.add_argument(
            "-ee",
            "--emission_energy",
            help="Name of the emitted energy",
            type=str,
        )
        parser.add_argument(
            "-rm",
            "--rixs_map",
            help="Name of the RIXS map",
        )
        parser.add_argument(
            "-m",
            "--mode",
            help="Mode of the RIXS map post-processing, e.g. 'sum' or 'max'."
            "Default is 'sum'.",
            type=str,
            default="sum",
            choices=choices_mode,
        )
        return vars(parser.parse_args())

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
            raise ValueError(f"Mode '{mode}' not in {choices_mode}.")
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
        raise KeyError(
            f"Key '{wrong_key}' not in data. Aailable keys are: {list(data.keys())}."
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
            raise ValueError(
                f"Export format '{export_format}' not in {choices_export}."
            )

        if export_format == "json":
            with open(
                pure_fname(fname).with_suffix(f".{export_format}"),
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(self.numpydict2listdict(data), f, indent=4)
        elif export_format in {"toml", "lock"}:
            with open(
                pure_fname(fname).with_suffix(f".{export_format}"),
                "wb",
            ) as f:
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

    def __call__(self) -> None:
        """Run the converter."""
        args = self.get_args()
        self.save(
            data=self.create_rixs(
                data=self.convert(args["infile"], args["file_format"]),
                incident_energy=args["incident_energy"],
                emission_energy=args["emission_energy"],
                rixs_map=args["rixs_map"],
                mode=args["mode"],
            ).dict(),
            fname=args["infile"],
            export_format=args["export_format"],
        )


def command_line_runner() -> None:
    """Run the command line script."""
    RIXSConverter()()

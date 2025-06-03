"""Convert the input and output files to the preferred file format."""

from __future__ import annotations

import argparse
import json

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

import tomli_w
import yaml

from spectrafit.plugins.converter import Converter
from spectrafit.tools import read_input_file


if TYPE_CHECKING:
    from collections.abc import MutableMapping


class FileConverter(Converter):
    """Convert the input and output file to the preferred file format.

    !!! info "Supported file formats"

        Currently supported file formats:

        -[x] JSON
        -[x] YAML (YML)
        -[x] TOML (LOCK for the lock file)

    Attributes:
        choices (ClassVar[set[str]]): The choices for the file format.

    """

    choices: ClassVar[set[str]] = {"json", "yaml", "yml", "toml", "lock"}

    def get_args(self) -> dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                additional information beyond the command line arguments.

        """
        parser = argparse.ArgumentParser(
            description="Converter for 'SpectraFit' input and output files.",
            usage="%(prog)s [options] infile",
        )
        parser.add_argument(
            "infile",
            type=Path,
            help="Filename of the 'SpectraFit' input or output file.",
        )
        parser.add_argument(
            "-f",
            "--file-format",
            help="File format for the conversion.",
            type=str,
            choices=self.choices,
        )
        parser.add_argument(
            "-e",
            "--export-format",
            help="File format for the export.",
            type=str,
            default="json",
            choices=self.choices,
        )
        return vars(parser.parse_args())

    @staticmethod
    def convert(infile: Path, file_format: str) -> MutableMapping[str, Any]:
        """Convert the input file to the output file.

        Args:
            infile (Path): The input file as a path object.
            file_format (str): The output file format.

        Raises:
            ValueError: If the input file format is not supported.

        Returns:
            MutableMapping[str, Any] : The converted file as a dictionary.

        """
        if file_format not in FileConverter.choices:
            msg = f"The input file format '{file_format}' is not supported."
            raise ValueError(msg)

        return read_input_file(infile)

    def save(self, data: Any, fname: Path, export_format: str) -> None:
        """Save the converted file.

        Raises:
            ValueError: If the input file format is identical with the output format.
            ValueError: If the output file format is not supported.

        Args:
            data (Any): The converted file as a dictionary.
            fname (Path): The input file as a path object.
            export_format (str): The output file format.

        """
        if fname.suffix[1:] == export_format:
            msg = (
                f"The input file suffix '{fname.suffix[1:]}' is similar to the"
                f" output file format '{export_format}'."
                "Please use a different output file suffix."
            )
            raise ValueError(
                msg,
            )

        if export_format not in self.choices:
            msg = f"The output file format '{export_format}' is not supported."
            raise ValueError(
                msg,
            )

        if export_format == "json":
            with fname.with_suffix(f".{export_format}").open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(data, f, indent=4)
        elif export_format in {"yaml", "yml"}:
            with fname.with_suffix(f".{export_format}").open(
                "w",
                encoding="utf-8",
            ) as f:
                yaml.dump(data, f, default_flow_style=False)
        elif export_format in {"toml", "lock"}:
            with fname.with_suffix(f".{export_format}").open("wb+") as f:
                tomli_w.dump(dict(**data), f)

    def __call__(self) -> None:
        """Run the converter via cmd commands."""
        args = self.get_args()
        self.save(
            data=self.convert(infile=args["infile"], file_format=args["file_format"]),
            fname=args["infile"],
            export_format=args["export_format"],
        )


def command_line_runner() -> None:
    """Run the converter from the command line."""
    FileConverter()()

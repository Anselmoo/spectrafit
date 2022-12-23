"""Convert the input and output files to the preferred file format."""
import argparse
import json

from pathlib import Path
from typing import Any
from typing import Dict

import tomli_w
import yaml

from spectrafit.plugins.converter import Converter
from spectrafit.tools import read_input_file


choices = {"json", "yaml", "yml", "toml", "lock"}


class FileConverter(Converter):
    """Convert the input and output file to the preferred file format.

    !!! info "Supported file formats"

        Currently supported file formats:

        -[x] JSON
        -[x] YAML (YML)
        -[x] TOML (LOCK for the lock file)
    """

    def get_args(self) -> Dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                additional information beyond the command line arguments.
        """
        parser = argparse.ArgumentParser(
            description="Converter for 'SpectraFit' input and output files."
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
            choices=choices,
        )
        return vars(parser.parse_args())

    def convert(self, infile: Path, file_format: str) -> None:
        """Convert the input file to the output file.

        Args:
            infile (Path): The input file as a path object.
            file_format (str): The output file format.

        Raises:
            ValueError: If the input file format is identical with the output format.
            ValueError: If the output file format is not supported.
        """
        if infile.suffix[1:] == file_format:
            raise ValueError(
                f"The input file suffix '{infile.suffix[1:]}' is similar to the"
                f" output file format '{file_format}'."
                "Please use a different output file suffix."
            )

        if file_format not in choices:
            raise ValueError(
                f"The output file format '{file_format}' is not supported."
            )

        data = read_input_file(infile)

        if file_format == "json":
            # Convert the input file to a JSON file
            with open(infile.with_suffix(f".{file_format}"), "w", encoding="utf8") as f:
                json.dump(data, f, indent=4)
        elif file_format in {"yaml", "yml"}:
            with open(infile.with_suffix(f".{file_format}"), "w", encoding="utf8") as f:
                yaml.dump(data, f, default_flow_style=False)
        elif file_format in {"toml", "lock"}:
            with open(
                infile.with_suffix(f".{file_format}"),
                "wb+",
            ) as f:
                tomli_w.dump(dict(**data), f)

    def __call__(self) -> None:
        """Run the converter via cmd commands."""
        self.convert(**self.get_args())


def command_line_runner() -> None:
    """Run the converter from the command line."""
    FileConverter()()

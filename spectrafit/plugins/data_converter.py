"""Transform the input data to a CSV file."""

import argparse
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

import pandas as pd

from spectrafit.api.file_model import DataFileAPI
from spectrafit.plugins.converter import Converter


def get_athena_column(fname: Path, comment: str = "#") -> Optional[List[str]]:
    """Get the header of the file.

    Args:
        fname (Path): The file name of the data file.
        comment (str, optional): The comment marker. Defaults to "#".

    Returns:
        Optional[List[str]]: The column names of the data file as a list.

    """
    with open(fname, encoding="utf-8") as f:
        data = f.read()
        lines = data.splitlines()
        return next(
            (
                lines[i - 1].split(comment)[-1].split()
                for i, line in enumerate(lines)
                if re.match(r"^\s*\d", line)
            ),
            None,
        )


athena_format = DataFileAPI(
    skiprows=None,
    skipfooter=0,
    delimiter=r"\s+",
    comment="#",
    names=get_athena_column,
    file_suffixes=[".nor"],
)


txt_format = DataFileAPI(
    skiprows=None,
    skipfooter=0,
    delimiter=r"\s+",
    header=0,
    file_suffixes=[".txt", ".dat", ".out"],
)


@dataclass(frozen=True)
class DataFormats:
    """Data formats."""

    ATHENA = athena_format
    TXT = txt_format


# Remove the private attributes
choices = {
    choice for choice in list(DataFormats.__dict__.keys()) if not choice.startswith("_")
}

choices_export = {"csv", "txt", "dat", "out"}


class DataConverter(Converter):
    """Convert the data files to a CSV file.

    !!! info "Supported file formats"

        Currently supported file formats:

        -[x] ATHENA
        -[x] TXT
        -[ ] more to come

        `DataConverter` class can be also used in the Jupyter notebook.
    """

    def get_args(self) -> Dict[str, Any]:
        """Get the arguments from the command line.

        Returns:
            Dict[str, Any]: Return the input file arguments as a dictionary without
                additional information beyond the command line arguments.
        """
        parser = argparse.ArgumentParser(
            description="Converter for 'SpectraFit' from data files to CSV files."
        )
        parser.add_argument(
            "infile",
            type=Path,
            help="Filename of the data file to convert.",
        )
        parser.add_argument(
            "-f",
            "--file-format",
            help="File format for the conversion.",
            type=str,
            choices=choices,
        )
        parser.add_argument(
            "-e",
            "--export-format",
            help="File format for the export.",
            type=str,
            default="csv",
            choices=choices_export,
        )
        return vars(parser.parse_args())

    @staticmethod
    def convert(infile: Path, file_format: str) -> pd.DataFrame:
        """Convert the input file to the target file format.

        Args:
            infile (Path): Input file as a path object.
            file_format (str): Target file format.

        Raises:
            ValueError: If the file format is not supported.

        Returns:
            pd.DataFrame: The converted data as a pandas DataFrame.
        """
        if file_format.upper() not in choices:
            raise ValueError(f"File format '{file_format}' is not supported.")

        if callable(DataFormats.__dict__[file_format].names):
            names = DataFormats.__dict__[file_format].names(infile)
        else:
            names = DataFormats.__dict__[file_format].names
        DataFormats.__dict__[file_format].names = names

        return pd.read_csv(
            infile, **DataFormats.__dict__[file_format].dict(exclude={"file_suffixes"})
        )

    def save(self, data: Any, fname: Path, export_format: str) -> None:
        """Save the converted data to a CSV file.

        Raises:
            ValueError: If the export format is not supported.

        Args:
            data (Any): The converted data, which is a pandas DataFrame.
            fname (Path): The file name of the data file.
            export_format (str): The file format of the exported file.
        """
        if export_format.lower() not in choices_export:
            raise ValueError(f"Export format '{export_format}' is not supported.")
        data.to_csv(fname.with_suffix(f".{export_format}"), index=False)

    def __call__(self) -> None:
        """Run the converter."""
        args = self.get_args()
        self.save(
            data=self.convert(
                args["infile"],
                args["file_format"],
            ),
            fname=args["infile"],
            export_format=args["export_format"],
        )


def command_line_runner() -> None:
    """Run the converter from the command line."""
    DataConverter()()

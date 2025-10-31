"""Transform the input data to a CSV file."""

from __future__ import annotations

import re

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any

import pandas as pd
import typer

from spectrafit.api.file_model import DataFileAPI
from spectrafit.plugins.converter import Converter


if TYPE_CHECKING:
    from collections.abc import MutableMapping

# Create Typer app
app = typer.Typer(
    help="Converter for 'SpectraFit' from data files to CSV files.",
    add_completion=False,
)


def get_athena_column(fname: Path, comment: str = "#") -> list[str] | None:
    """Get the header of the file.

    Args:
        fname (Path): The file name of the data file.
        comment (str, optional): The comment marker. Defaults to "#".

    Returns:
        Optional[List[str]]: The column names of the data file as a list.

    """
    with fname.open(encoding="utf-8") as f:
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

    @staticmethod
    def convert(infile: Path, file_format: str) -> MutableMapping[str, Any]:
        """Convert the input file to the target file format.

        Args:
            infile (Path): Input file as a path object.
            file_format (str): Target file format.

        Raises:
            ValueError: If the file format is not supported.

        Returns:
            MutableMapping[str, Any]: The converted data as a MutableMapping[str, Any],
                which belongs to DataFrame.

        """
        if file_format.upper() not in choices:
            msg = f"File format '{file_format}' is not supported."
            raise ValueError(msg)

        if callable(DataFormats.__dict__[file_format].names):
            names = DataFormats.__dict__[file_format].names(infile)
        else:
            names = DataFormats.__dict__[file_format].names
        DataFormats.__dict__[file_format].names = names

        return pd.read_csv(
            infile,
            **DataFormats.__dict__[file_format].dict(exclude={"file_suffixes"}),
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
            msg = f"Export format '{export_format}' is not supported."
            raise ValueError(msg)
        data.to_csv(fname.with_suffix(f".{export_format}"), index=False)


@app.command()
def cli_main(
    infile: Annotated[
        Path, typer.Argument(help="Filename of the data file to convert.")
    ],
    file_format: Annotated[
        str | None,
        typer.Option(
            "-f",
            "--file-format",
            help="File format for the conversion.",
        ),
    ] = None,
    export_format: Annotated[
        str,
        typer.Option(
            "-e",
            "--export-format",
            help="File format for the export.",
        ),
    ] = "csv",
) -> None:
    """Convert data files to CSV format."""
    # Validate file format choices
    if file_format and file_format.upper() not in choices:
        typer.echo(
            f"Error: Invalid file format '{file_format}'. "
            f"Choose from: {', '.join(sorted(choices))}",
            err=True,
        )
        raise typer.Exit(1)

    if export_format.lower() not in choices_export:
        typer.echo(
            f"Error: Invalid export format '{export_format}'. "
            f"Choose from: {', '.join(sorted(choices_export))}",
            err=True,
        )
        raise typer.Exit(1)

    # Create converter instance and run conversion
    converter = DataConverter()  # type: ignore[abstract]
    try:
        data = converter.convert(infile, file_format)  # type: ignore[arg-type]
        converter.save(data=data, fname=infile, export_format=export_format)
        typer.echo(f"Successfully converted {infile} to {export_format} format")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def command_line_runner() -> None:
    """Entry point for the data converter CLI."""
    app()

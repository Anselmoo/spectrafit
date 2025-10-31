"""Convert the input and output files to the preferred file format."""

from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Annotated
from typing import Any
from typing import ClassVar

import tomli_w
import typer
import yaml

from spectrafit.plugins.converter import Converter
from spectrafit.tools import read_input_file


if TYPE_CHECKING:
    from collections.abc import MutableMapping

# Create Typer app
app = typer.Typer(
    help="Converter for 'SpectraFit' input and output files.",
    add_completion=False,
)


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


@app.command()
def cli_main(
    infile: Annotated[
        Path, typer.Argument(help="Filename of the 'SpectraFit' input or output file.")
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
    ] = "json",
) -> None:
    """Convert 'SpectraFit' input and output files between different formats."""
    # Validate file format choices
    choices = FileConverter.choices

    if file_format and file_format not in choices:
        typer.echo(
            f"Error: Invalid file format '{file_format}'. "
            f"Choose from: {', '.join(sorted(choices))}",
            err=True,
        )
        raise typer.Exit(1)

    if export_format not in choices:
        typer.echo(
            f"Error: Invalid export format '{export_format}'. "
            f"Choose from: {', '.join(sorted(choices))}",
            err=True,
        )
        raise typer.Exit(1)

    # Create converter instance and run conversion
    converter = FileConverter()
    try:
        data = converter.convert(infile=infile, file_format=file_format)
        converter.save(data=data, fname=infile, export_format=export_format)
        typer.echo(f"Successfully converted {infile} to {export_format} format")
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


def command_line_runner() -> None:
    """Entry point for the file converter CLI."""
    app()

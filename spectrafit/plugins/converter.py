"""Convert the input and output files to the preferred file format."""
import argparse
import json

from pathlib import Path
from typing import Any
from typing import Dict

import tomli_w
import yaml

from spectrafit.tools import read_input_file


choices = ["json", "yaml", "yml", "toml", "lock"]


def get_args() -> Dict[str, Any]:
    """Get the arguments from the command line.

    Returns:
        Dict[str, Any]: Return the input file arguments as a dictionary without
             additional information beyond the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Converter for 'SpectraFit' input and output files."
    )
    parser.add_argument(
        "infile", type=Path, help="Filename of the 'SpectraFit' input or output file."
    )
    parser.add_argument(
        "-f",
        "--format",
        help="File format for the conversion.",
        type=str,
        choices=choices,
    )
    return vars(parser.parse_args())


def convert(args: Dict[str, Any]) -> None:
    """Convert the input file to the output file.

    Args:
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.

    Raises:
        ValueError: If the input file format is identical with the output format.
        ValueError: If the output file format is not supported.
    """
    if args["infile"].suffix[1:] == args["format"]:
        raise ValueError(
            f"The input file suffix '{args['infile'].suffix[1:]}' is similar to the"
            f" output file format '{args['format']}'."
            "Please use a different output file suffix."
        )

    if args["format"] not in choices:
        raise ValueError(f"The output file format '{args['format']}' is not supported.")

    data = read_input_file(args["infile"])

    if args["format"] == "json":
        # Convert the input file to a JSON file
        with open(args["infile"].with_suffix(".json"), "w", encoding="utf8") as f:
            json.dump(data, f, indent=4)
    elif args["format"] == "yaml":
        with open(args["infile"].with_suffix(".yaml"), "w", encoding="utf8") as f:
            yaml.dump(data, f, default_flow_style=False)
    elif args["format"] in ["toml", "lock"]:
        with open(
            args["infile"].with_suffix(".toml"),
            "wb+",
        ) as f:
            tomli_w.dump(dict(**data), f)


def command_line_runner() -> None:
    """Run the converter via cmd commands."""
    convert(get_args())

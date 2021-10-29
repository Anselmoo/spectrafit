"""SpectraFit, the command line tool for fitting."""
import argparse

from datetime import datetime
from getpass import getuser
from socket import gethostname
from typing import Any
from typing import Dict
from typing import Tuple
from uuid import uuid4

import pandas as pd

from spectrafit import __version__
from spectrafit.models import SolverModels
from spectrafit.plotting import PlotSpectra
from spectrafit.report import PrintingResults
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.tools import SaveResult
from spectrafit.tools import load_data
from spectrafit.tools import read_input_file


def get_args() -> dict:
    """Get the arguments from the command line.

    Returns:
        dict: Return the input file arguments as a dictionary without additional
             information beyond the command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Fast Fitting Program for ascii txt files."
    )
    parser.add_argument("infile", type=str, help="Filename of the specta data")
    parser.add_argument(
        "-o",
        "--outfile",
        default="spectrafit_results",
        type=str,
        help="Filename for the export, default to set to 'spectrafit_results'.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="fitting_input.toml",
        help=(
            "Filename for the input parameter, default to set to 'fitting_input.toml'."
            "Supported fileformats are: '*.json', '*.yml', '*.yaml', and '*.toml'"
        ),
    )
    parser.add_argument(
        "-ov",
        "--oversampling",
        action="store_true",
        default=False,
        help="Oversampling the spectra by using factor of 5; default to False.",
    )
    parser.add_argument(
        "-e0",
        "--energy_start",
        type=float,
        default=None,
        help="Starting energy in eV; default to start of energy.",
    )
    parser.add_argument(
        "-e1",
        "--energy_stop",
        type=float,
        default=None,
        help="Ending energy in eV; default to end of energy.",
    )
    parser.add_argument(
        "-s",
        "--smooth",
        type=int,
        default=None,
        help="Number of smooth points for lmfit; default to 0.",
    )
    parser.add_argument(
        "-sh",
        "--shift",
        type=float,
        default=None,
        help="Constant applied energy shift; default to 0.0.",
    )
    parser.add_argument(
        "-c",
        "--column",
        nargs=2,
        type=int,
        default=[0, 1],
        help=(
            "Selected columns for the energy- and intensity-values; default to 0 for"
            " energy (x-axis) and 1 for intensity (y-axis)."
        ),
    )
    parser.add_argument(
        "-sep",
        "--separator",
        type=str,
        default="\t",
        choices=["\t", ",", ";", ":", "|", " ", "s+"],
        help="Redefine the type of separator; default to '\t'.",
    )
    parser.add_argument(
        "-dec",
        "--decimal",
        type=str,
        default=".",
        choices=[".", ","],
        help="Type of decimal separator; default to '.'.",
    )
    parser.add_argument(
        "-hd",
        "--header",
        type=int,
        default=None,
        help="Selected the header for the dataframe; default to None.",
    )
    parser.add_argument(
        "-np",
        "--noplot",
        help="No plotting the spectra and the fit of `spectrafit`.",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Display the current version of `spectrafit`.",
        action="store_true",
    )
    parser.add_argument(
        "-vb",
        "--verbose",
        help="Display the initial configuration parameters as a dictionary.",
        action="store_true",
    )
    parser.add_argument(
        "-g",
        "--global",
        type=int,
        default=0,
        choices=[0, 1, 2],
        help=(
            "Perform a global fit over the complete dataframe. The options are '0' "
            "for classic fit (default). The option '1' for global fitting with "
            "auto-definition of the peaks depending on the column size and '2' for "
            "self-defined global fitting routines."
        ),
    )
    return vars(parser.parse_args())


def command_line_runner(args: Dict[str, Any] = None) -> None:
    """Run spectrafit from the command line.

    Args:
        args (Dict[str, Any], optional): The input file arguments as a
             dictionary with additional information beyond the command line arguments.
             Defaults to None.
    """
    while True:
        if not args:
            args = extracted_from_command_line_runner()
        if args["version"]:
            print(f"Currently used version is: {__version__}")
            return
        df = load_data(args)

        print("Lets start fitting ...")
        df_result, args = fitting_routine(df=df, args=args)

        PlotSpectra(df=df_result, args=args)()

        SaveResult(df=df_result, args=args)

        args = None
        print("Fitting is done!")
        again = input("Would you like to fit again ...? Enter y/n: ").lower()
        if again == "n":
            print("Thanks for using ...!")
            return
        elif again == "y":
            continue
        else:
            print("You should enter either 'y' or 'n'.")


def extracted_from_command_line_runner() -> Dict[str, Any]:
    """Extract the input commands from the terminal.

    Raises:
        KeyError: Missing key `minimizer` in `parameters`.
        KeyError: Missing key `optimizer` in `parameters`.

    Returns:
        Dict[str, Any]: The input file arguments as a dictionary with additional
             information beyond the command line arguments.
    """
    result = get_args()
    _args = read_input_file(result["input"])
    if "settings" in _args.keys():
        for key in _args["settings"].keys():
            result[key] = _args["settings"][key]
    if "description" in _args["fitting"].keys():
        result["description"] = _args["fitting"]["description"]
    if "parameters" in _args["fitting"].keys():
        if "minimizer" in _args["fitting"]["parameters"].keys():
            result["minimizer"] = _args["fitting"]["parameters"]["minimizer"]
        else:
            raise SystemExit("Missing 'minimizer' in 'parameters'!")
        if "optimizer" in _args["fitting"]["parameters"].keys():
            result["optimizer"] = _args["fitting"]["parameters"]["optimizer"]
        else:
            raise SystemExit("Missing key 'optimizer' in 'parameters'!")
        if "report" in _args["fitting"]["parameters"].keys():
            result["report"] = _args["fitting"]["parameters"]["report"]
        else:
            result["report"] = {
                "show_correl": True,
                "min_correl": 0.1,
                "sort_pars": False,
            }
        if "conf_interval" in _args["fitting"]["parameters"].keys():
            result["conf_interval"] = _args["fitting"]["parameters"]["conf_interval"]
        else:
            result["conf_interval"] = None
    if "peaks" in _args["fitting"].keys():
        result["peaks"] = _args["fitting"]["peaks"]
    result["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result["ID"] = str(uuid4())
    result["user_name"] = getuser()
    result["user_system"] = gethostname()
    result["used_version"] = __version__
    return result


def fitting_routine(
    df: pd.DataFrame, args: Dict[str, Any]
) -> Tuple[pd.DataFrame, dict]:
    """Run the fitting algorithm.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.

    Returns:
        Tuple[pd.DataFrame, dict]: Can be both a DataFrame or a dictionary, which is
             containing the input data (`x` and `data`), as well as the best fit and
             the corresponding residuum. Hence, it will be extended by the single
             contribution of the model.
    """
    df, args = PreProcessing(df=df, args=args)()

    minimizer, result = SolverModels(df=df, args=args)()

    df, args = PostProcessing(df=df, args=args, minimizer=minimizer, result=result)()
    PrintingResults(args=args, minimizer=minimizer, result=result)()

    return df, args


if __name__ == "__main__":
    command_line_runner()

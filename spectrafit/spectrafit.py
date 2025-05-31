"""SpectraFit, the command line tool for fitting."""

from __future__ import annotations

import argparse

from typing import TYPE_CHECKING
from typing import Any

from spectrafit.api.cmd_model import CMDModelAPI
from spectrafit.models.builtin import SolverModels
from spectrafit.plotting import PlotSpectra
from spectrafit.report import PrintingResults
from spectrafit.report import PrintingStatus
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.tools import SaveResult
from spectrafit.tools import load_data
from spectrafit.tools import read_input_file


if TYPE_CHECKING:
    from collections.abc import MutableMapping

    import pandas as pd


__status__ = PrintingStatus()


def get_args() -> dict[str, Any]:
    """Get the arguments from the command line.

    Returns:
        Dict[str, Any]: Return the input file arguments as a dictionary without
             additional information beyond the command line arguments.

    """
    parser = argparse.ArgumentParser(
        description="Fast Fitting Program for ascii txt files.",
        usage="spectrafit [options] infile",
        epilog="For more information, visit https://anselmoo.github.io/spectrafit/",
        prog="spectrafit",
    )
    parser.add_argument("infile", type=str, help="Filename of the spectra data")
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
        help="Starting energy in eV; default to start of energy; default to None.",
    )
    parser.add_argument(
        "-e1",
        "--energy_stop",
        type=float,
        default=None,
        help="Ending energy in eV; default to end of energy; default to None.",
    )
    parser.add_argument(
        "-s",
        "--smooth",
        type=int,
        default=0,
        help="Number of smooth points for lmfit; default to 0.",
    )
    parser.add_argument(
        "-sh",
        "--shift",
        type=float,
        default=0,
        help="Constant applied energy shift; default to 0.",
    )
    parser.add_argument(
        "-c",
        "--column",
        nargs=2,
        default=[0, 1],
        help=(
            "Selected columns for the energy- and intensity-values; default to '0' for"
            " energy (x-axis) and '1' for intensity (y-axis). In case of working with"
            " header, the column should be set to the column names as 'str'; default"
            " to 0 and 1."
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
        "-cm",
        "--comment",
        type=str,
        default=None,
        help="Lines with comment characters like '#' should not be parsed;"
        " default to None.",
    )
    parser.add_argument(
        "-g",
        "--global_",
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
    parser.add_argument(
        "-auto",
        "--autopeak",
        help=(
            "Auto detection of peaks in the spectra based on `SciPy`. The position, "
            "height, and width are used as estimation for the `Gaussian` models. "
            "The default option is 'False' for manual peak definition."
        ),
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-np",
        "--noplot",
        help="No plotting the spectra and the fit of `SpectraFit`.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Display the current version of `SpectraFit`.",
        action="version",
        version=__status__.version(),
    )
    parser.add_argument(
        "-vb",
        "--verbose",
        help=(
            "Display the initial configuration parameters and fit results, as a table "
            "'1', as a dictionary '2', or not in the terminal '0'. The default option "
            "is set to 1 for table `printout`."
        ),
        type=int,
        default=1,
        choices=[0, 1, 2],
    )
    return vars(parser.parse_args())


def command_line_runner(args: dict[str, Any] | None = None) -> None:
    """Run spectrafit from the command line.

    Args:
        args (Dict[str, Any], optional): The input file arguments as a
             dictionary with additional information beyond the command line arguments.
             Defaults to None.

    """
    __status__.welcome()
    while True:
        if not args:
            args = extracted_from_command_line_runner()
        __status__.start()

        df_result, args = fitting_routine(args=args)
        PlotSpectra(df=df_result, args=args)()
        SaveResult(df=df_result, args=args)()
        args = None

        __status__.end()

        again = input("Would you like to fit again ...? Enter y/n: ").lower()
        if again == "n":
            __status__.thanks()
            __status__.credits()
            return
        if again == "y":
            continue
        __status__.yes_no()


def extracted_from_command_line_runner() -> dict[str, Any]:
    """Extract the input commands from the terminal.

    Raises:
        KeyError: Missing key `minimizer` in `parameters`.
        KeyError: Missing key `optimizer` in `parameters`.

    Returns:
        Dict[str, Any]: The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    """
    result: dict[str, Any] = get_args()
    _args: MutableMapping[str, Any] = read_input_file(result["input"])

    if "settings" in _args:
        for key in _args["settings"]:
            result[key] = _args["settings"][key]
    result = CMDModelAPI(**result).model_dump()
    if "description" in _args["fitting"]:
        result["description"] = _args["fitting"]["description"]
    if "parameters" in _args["fitting"]:
        if "minimizer" in _args["fitting"]["parameters"]:
            result["minimizer"] = _args["fitting"]["parameters"]["minimizer"]
        else:
            msg = "Missing 'minimizer' in 'parameters'!"
            raise KeyError(msg)
        if "optimizer" in _args["fitting"]["parameters"]:
            result["optimizer"] = _args["fitting"]["parameters"]["optimizer"]
        else:
            msg = "Missing key 'optimizer' in 'parameters'!"
            raise KeyError(msg)
        if "report" in _args["fitting"]["parameters"]:
            result["report"] = _args["fitting"]["parameters"]["report"]
        else:
            result["report"] = {
                "show_correl": True,
                "min_correl": 0.1,
                "sort_pars": False,
            }
        if "conf_interval" in _args["fitting"]["parameters"]:
            result["conf_interval"] = _args["fitting"]["parameters"]["conf_interval"]
        else:
            result["conf_interval"] = None

    if "peaks" in _args["fitting"]:
        result["peaks"] = _args["fitting"]["peaks"]
    return result


def fitting_routine(args: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Run the fitting algorithm.

    Args:
        args (Dict[str, Any]): The input file arguments as a dictionary with
             additional information beyond the command line arguments.

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Returns a DataFrame and a dictionary,
             which is containing the input data (`x` and `data`), as well as the best
             fit, single contributions of each peak and the corresponding residuum. The
             dictionary contains the raw input data, the best fit, the single
             contributions and the corresponding residuum. Furthermore, the dictionary
             is extended by advanced statistical information of the fit.

    """
    df: pd.DataFrame = load_data(args)
    df, args = PreProcessing(df=df, args=args)()
    minimizer, result = SolverModels(df=df, args=args)()
    df, args = PostProcessing(df=df, args=args, minimizer=minimizer, result=result)()
    PrintingResults(args=args, minimizer=minimizer, result=result)()

    return df, args

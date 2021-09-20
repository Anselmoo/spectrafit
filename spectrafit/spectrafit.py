"""SpectraFit, the command line tool for fitting."""
import argparse
import json

from datetime import datetime
from getpass import getuser
from pathlib import Path
from socket import gethostname
from typing import Any
from typing import MutableMapping
from typing import Tuple
from uuid import uuid4

import numpy as np
import pandas as pd
import toml
import yaml

from lmfit import Minimizer
from lmfit import Parameters
from lmfit import conf_interval
from spectrafit import __version__
from spectrafit.models import calculated_model
from spectrafit.models import solver_model
from spectrafit.plotting import plot_spectra
from spectrafit.report import fit_report_as_dict
from spectrafit.report import printing_regular_mode
from spectrafit.report import printing_verbose_mode
from spectrafit.tools import energy_range
from spectrafit.tools import energy_shift
from spectrafit.tools import intensity_smooth
from spectrafit.tools import oversampling
from spectrafit.tools import save_as_csv
from spectrafit.tools import save_as_json


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
    return vars(parser.parse_args())


def get_parameters(args: dict) -> dict:
    """Transforming the input parameters to a params-dictionary.

    Args:
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        dict: Transformed the pre-defined peaks in the `args` to the params dictionary
             of the lmfit-`minimizer`.
    """
    params = Parameters()

    for key_1, value_1 in args["peaks"].items():
        for key_2, value_2 in value_1.items():
            for key_3, value_3 in value_2.items():
                params.add(f"{key_2}_{key_3}_{key_1}", **value_3)
    return params


def read_input_file(fname: str) -> MutableMapping[str, Any]:
    """Read the input file.

    Read the input file as `toml`, `json`, or `yaml` files
    and return as a dictionary.

    Args:
        fname (str): Name of the input file.

    Raises:
        SystemExit: If the input file is not supported.

    Returns:
        dict: Return the input file arguments as a dictionary with additional
             information beyond the command line arguments.

    """
    _fname = Path(fname)

    if _fname.suffix == ".toml":
        with open(_fname, "r") as f:
            args = toml.load(fname)
    elif _fname.suffix == ".json":
        with open(_fname, "r") as f:
            args = json.load(f)
    elif _fname.suffix in [".yaml", ".yml"]:
        with open(_fname, "r") as f:
            args = yaml.load(f, Loader=yaml.FullLoader)
    else:
        raise SystemExit(
            f"ERROR: Input file {fname} has not supported file format.\n"
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        )
    return args


def command_line_runner(args: dict = None) -> None:
    """Running spectrafit from the command line.

    Args:
        args (dict, optional): The input file arguments as a dictionary with additional
             information beyond the command line arguments. Defaults to None.
    """
    while True:
        if not args:
            args = extracted_from_command_line_runner()
        if args["version"]:
            print(f"Currently used version is: {__version__}")
            return
        try:
            df = pd.read_csv(
                Path(args["infile"]),
                sep=args["separator"],
                header=args["header"],
                usecols=args["column"],
                dtype=np.float64,
                decimal=args["decimal"],
            )

            args["data_statistic"] = df.describe(
                percentiles=np.arange(0.1, 1, 0.1)
            ).to_dict()

        except ValueError as exc:
            print(f"Error: {exc} -> Dataframe contains non numeric data!")
            return
        print("Lets start fitting ...")
        df_result, args = fitting_routine(df=df, args=args)
        args["fit_result"] = df_result.to_dict(orient="list")
        if not args["noplot"]:
            plot_spectra(df=df_result)
        save_as_json(args)
        save_as_csv(df=df_result, args=args)

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


def extracted_from_command_line_runner() -> dict:
    """Extracting the input commands from the terminal.

    Raises:
        KeyError: Missing key `minimizer` in `parameters`.
        KeyError: Missing key `optimizer` in `parameters`.

    Returns:
        dict: The input file arguments as a dictionary with additional
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
            raise KeyError("Missing 'minimizer' in 'parameters'.")
        if "optimizer" in _args["fitting"]["parameters"].keys():
            result["optimizer"] = _args["fitting"]["parameters"]["optimizer"]
        else:
            raise KeyError("Missing key 'optimizer' in 'parameters'.")
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


def fitting_routine(df: pd.DataFrame, args: dict) -> Tuple[pd.DataFrame, dict]:
    """Running the fitting algorithm.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        Tuple[pd.DataFrame, dict]: Can be both a DataFrame or a dictionary, which is
             containing the input data (`x` and `data`), as well as the best fit and
             the corresponding residuum. Hence, it will be extended by the single
             contribution of the model.
    """
    df = energy_range(df=df, args=args)
    df = energy_shift(df=df, args=args)
    df = oversampling(df=df, args=args)
    df = intensity_smooth(df=df, args=args)

    params = get_parameters(args=args)
    mini = Minimizer(
        solver_model,
        params,
        fcn_args=(df[args["column"][0]].values, df[args["column"][1]].values),
        **args["minimizer"],
    )
    result = mini.minimize(**args["optimizer"])
    args["fit_insights"] = fit_report_as_dict(result, modelpars=result.params)
    if args["conf_interval"]:
        args["confidence_interval"] = conf_interval(
            mini, result, **args["conf_interval"]
        )
    df = df.rename(
        columns={args["column"][0]: "energy", args["column"][1]: "intensity"}
    )
    df["residual"] = result.residual
    df["fit"] = df["intensity"].values + result.residual
    df = calculated_model(params=result.params, x=df["energy"].values, df=df)
    _corr = df.corr()
    args["linear_correlation"] = _corr.to_dict()
    if args["verbose"]:
        printing_verbose_mode(args)
    else:
        printing_regular_mode(args, result=result, minimizer=mini, correlation=_corr)
    return df, args


if __name__ == "__main__":
    command_line_runner()

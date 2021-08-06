import argparse
import json
import pprint
import sys

from pathlib import Path
from typing import Any
from typing import Tuple

import numpy as np
import pandas as pd
import toml
import yaml

from lmfit import Minimizer
from lmfit import Parameters
from lmfit import conf_interval
from lmfit import report_ci
from lmfit import report_fit
from spectrafit import __version__
from spectrafit.models import calculated_models
from spectrafit.models import solver_model
from spectrafit.report import fit_report_as_dict
from tabulate import tabulate


pp = pprint.PrettyPrinter(indent=4)


def get_args() -> dict:
    parser = argparse.ArgumentParser(
        description="Fast Fitting Program for ascii txt files."
    )
    parser.add_argument("infile", type=str, help="Filename of the specta data")
    parser.add_argument(
        "-o",
        "--outfile",
        type=str,
        help="Filename for the export, default to set to input name.",
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        default="fitting_input.toml",
        help=(
            "Filename for the input parameter, default to set to 'fitting_input.toml'."
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
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
        "-disp",
        action="store_true",
        default=False,
        help="Hole or splitted Table on the Screen; default to 'hole'.",
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
        "--seperator",
        type=str,
        default="\t",
        choices=["\t", ",", ";", ":", "|", " ", "s+"],
        help="Redefine the type of seperator; default to '\t'.",
    )
    parser.add_argument(
        "-dec",
        "--decimal",
        type=str,
        default=".",
        choices=[".", ","],
        help="Type of decimal seperator; default to '.'.",
    )
    parser.add_argument(
        "-hd",
        "--header",
        type=int,
        default=None,
        help="Selected the header for the dataframe; default to None.",
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


def read_input_file(fname: str) -> dict:
    """Read the input file.

    Read the input file as `toml`, `json`, or `yaml` files
    and return as a dictionary.

    Args:
        fname (str): Name of the input file.

    Raises:
        TypeError: If the input file is not supported.

    Returns:
        dict: Table of the input file to a dictionary.
    """
    fname = Path(fname)
    try:
        if fname.suffix == ".toml":
            with open(fname, "r") as f:
                return toml.load(fname)
        elif fname.suffix == ".json":
            with open(fname, "r") as f:
                return json.load(f)
        elif fname.suffix == ".yaml":
            with open(fname, "r") as f:
                return yaml.load(f, Loader=yaml.FullLoader)
    except TypeError as exc:
        print(
            f"{exc}:  Input file {fname} has not supported file format.\n"
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        )
        sys.exit(1)
    except FileNotFoundError as exc:
        print(
            f"{exc}:  Standard input file {fname} has to be provided!"
            "\nOr you have to explicitly provide an input file with '-i' or '--input'.\n"
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        )
        sys.exit(1)


def command_line_runner(args: dict = None) -> None:

    while True:
        again = input("Would you like to fit ...? Enter y/n: ").lower()
        if again == "n":
            print("Thanks for using ...!")
            return
        elif again == "y":
            if not args:
                args = extracted_from_command_line_runner()
            if args["version"]:
                print(f"Currently used verison is: {__version__}")
                return
            try:
                df = pd.read_csv(
                    Path(args["infile"]),
                    sep=args["seperator"],
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
            save_as_json(args)
            save_as_csv(args, df=df_result)

            args = None
            # print("\nCorrelation:\n")
        else:
            print('You should enter either "y" or "n".')


def save_as_csv(args, df: pd.DataFrame) -> None:

    df.to_csv(Path(f"{args['outfile']}_fit.csv"), index=False)
    pd.DataFrame.from_dict(args["fit_insights"]["correlations"]).to_csv(
        Path(f"{args['outfile']}_correlation.csv"),
        index=True,
        index_label="attributes",
    )
    pd.DataFrame.from_dict(args["fit_insights"]["variables"]).to_csv(
        Path(f"{args['outfile']}_errors.csv"),
        index=True,
        index_label="attributes",
    )


def save_as_json(args):
    """Save the fitting result as json file.

    Args:
        args (dict): Dictionary of the fitting result.

    Returns:
        None
    """
    if args["outfile"]:
        with open(Path(f"{args['outfile']}_summary.json"), "w") as f:
            json.dump(args, f, indent=4)
    else:
        raise FileNotFoundError("No output file provided!")


def extracted_from_command_line_runner() -> dict:
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
    return result


def fitting_routine(df: pd.DataFrame, args: dict) -> Tuple[pd.DataFrame, dict]:

    # try:
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
    #
    # try:
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
    df["fit"] = df["intensity"].values - result.residual
    df = calculated_models(params=result.params, x=df["energy"].values, df=df)
    _corr = df.corr()
    args["linear_correlation"] = _corr.to_dict()
    if args["verbose"]:
        printing_verbose_mode(args)
    else:
        printing_regular_mode(args, result=result, minimizer=mini, correlation=_corr)
    return df, args


def printing_regular_mode(
    args, result: Any, minimizer: Minimizer, correlation: pd.DataFrame
) -> None:
    print("\nStatistic:\n")
    print(
        tabulate(
            pd.DataFrame.from_dict(args["data_statistic"]),
            headers="keys",
            tablefmt="fancy_grid",
            floatfmt=".2f",
        )
    )
    print("\nFit Results and Insights:\n")
    print(report_fit(result, modelpars=result.params, **args["report"]))
    if args["conf_interval"]:
        print("\nConfidence Interval:\n")
        report_ci(conf_interval(minimizer, result, **args["conf_interval"])[0])
    print("\nOverall Linear-Correlation:\n")
    print(tabulate(correlation, headers="keys", tablefmt="fancy_grid", floatfmt=".2f"))


def printing_verbose_mode(args: dict) -> None:
    print("\nStatistic:\n")
    pp.pprint(args["data_statistic"])
    print("Input Parameter:\n")
    pp.pprint(args)
    print("\nFit Results and Insights:\n")
    pp.pprint(args["fit_insights"])
    if args["conf_interval"]:
        print("\nConfidence Interval:\n")
        pp.pprint(args["confidence_interval"])
    print("\nOverall Linear-Correlation:\n")
    pp.pprint(args["linear_correlation"])


def get_parameters(args: dict) -> dict:
    """[summary]

    Args:
        args (dict): [description]

    Returns:
        dict: [description]
    """
    params = Parameters()

    for key_1, value_1 in args["peaks"].items():
        for key_2, value_2 in value_1.items():
            for key_3, value_3 in value_2.items():
                params.add(f"{key_2}_{key_3}_{key_1}", **value_3)
    return params


def energy_range(df: pd.DataFrame, args: dict) -> Tuple[pd.DataFrame, dict, dict]:
    """
    Select the energy range for fitting.
    """

    _e0 = args["energy_start"]
    _e1 = args["energy_stop"]

    if _e0 and _e1:
        return df[(df[args["column"][0]] >= _e0) & (df[args["column"][0]] <= _e1)]
    elif _e0:
        return df[df[args["column"][0]] >= _e0]
    elif _e1:
        return df[df[args["column"][0]] <= _e1]
    return df


def energy_shift(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    """
    Shift the energy axis by a given value.
    """
    if args["shift"]:
        df[args["column"][0]] = df[args["column"][0]] - args["shift"]
        return df
    return df


def oversampling(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    if args["oversampling"]:
        x_values = np.linspace(
            df[args["column"][0]].min(), df[args["column"][0]].max(x), 5 * df.shape[0]
        )
        return pd.DataFrame(
            {
                args["column"][0]: x_values,
                args["column"][1]: np.interp(
                    x_values, df[args["column"][0]].values, df[args["column"][1]].values
                ),
            }
        )
    return df


def intensity_smooth(df: pd.DataFrame, args: dict) -> pd.DataFrame:

    if args["smooth"]:
        box = np.ones(args["smooth"]) / args["smooth"]
        df[args["column"][1]] = np.convolve(
            df[args["column"][1]].values, box, mode="same"
        )
        return df
    return df


if __name__ == "__main__":
    command_line_runner()

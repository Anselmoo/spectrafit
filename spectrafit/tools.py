"""Collection of essential tools for running SpectraFit."""
import json

from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd


def energy_range(df: pd.DataFrame, args: dict) -> Tuple[pd.DataFrame, dict, dict]:
    """Select the energy range for fitting.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        Tuple[pd.DataFrame, dict, dict]: DataFrame containing the input data
             (`x` and `data`), as well as the best fit and the corresponding residuum.
             Hence, it will be extended by the single contribution of the model.
    """
    _e1 = args["energy_stop"]
    _e0 = args["energy_start"]

    if isinstance(_e0, (int, float)) and isinstance(_e1, (int, float)):
        return df[(df[args["column"][0]] >= _e0) & (df[args["column"][0]] <= _e1)]
    elif isinstance(_e0, (int, float)):
        return df[df[args["column"][0]] >= _e0]
    elif isinstance(_e1, (int, float)):
        return df[df[args["column"][0]] <= _e1]
    return df


def energy_shift(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    """Shift the energy axis by a given value.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        pd.DataFrame: DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
    """
    if args["shift"]:
        df[args["column"][0]] = df[args["column"][0]] - args["shift"]
        return df
    return df


def oversampling(df: pd.DataFrame, args: dict) -> pd.DataFrame:
    """Oversampling the data to increase the resolution of the data.

    !!! note "About Oversampling"
        In this implementation of oversampling, the data is oversampled by the factor of
         5. In case of data with only a few points, the increased resolution should
         allow to easier solve the optimization problem. The oversampling based on a
         simple linear regression.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        pd.DataFrame: DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
    """
    if args["oversampling"]:
        x_values = np.linspace(
            df[args["column"][0]].min(), df[args["column"][0]].max(), 5 * df.shape[0]
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
    """Smooth the intensity values.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        pd.DataFrame: DataFrame containing the input data (`x` and `data`), which are
             optionally smoothed.
    """
    if args["smooth"]:
        box = np.ones(args["smooth"]) / args["smooth"]
        df[args["column"][1]] = np.convolve(
            df[args["column"][1]].values, box, mode="same"
        )
        return df
    return df


def save_as_csv(df: pd.DataFrame, args: dict) -> None:
    """Save the the fit results to csv files.

    !!! note "About saving the fit results"
        The fit results are saved to csv files and are divided into three different
         categories:
            1. The fit results of the original used data.
            2. The correlation analysis of the fit results.
            3. The error analysis of the fit results.

    Args:
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        args (dict): Return the input file arguments as a dictionary with additional
             information beyond the command line arguments.
    """
    df.to_csv(Path(f"{args['outfile']}_fit.csv"), index=False)
    pd.DataFrame.from_dict(args["linear_correlation"]).to_csv(
        Path(f"{args['outfile']}_correlation.csv"),
        index=True,
        index_label="attributes",
    )
    pd.DataFrame.from_dict(args["fit_insights"]["variables"]).to_csv(
        Path(f"{args['outfile']}_errors.csv"),
        index=True,
        index_label="attributes",
    )


def save_as_json(args) -> None:
    """Save the fitting result as json file.

    Args:
        args (dict): The input file arguments as a dictionary with additional
             information beyond the command line arguments.
    """
    if args["outfile"]:
        with open(Path(f"{args['outfile']}_summary.json"), "w") as f:
            json.dump(args, f, indent=4)
    else:
        raise FileNotFoundError("No output file provided!")

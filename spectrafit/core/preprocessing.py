"""Pre-processing utilities for SpectraFit.

This module contains the PreProcessing class for data pre-processing.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


class PreProcessing:
    """Summarized all pre-processing-filters  together."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize PreProcessing class.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        self.df = df
        self.args = args

    def __call__(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Apply all pre-processing-filters.

        Returns:
            pd.DataFrame: DataFrame containing the input data (`x` and `data`), which
                 are optionally:

                    1. shrinked to a given range
                    2. shifted
                    3. linear oversampled
                    4. smoothed
            Dict[str,Any]: Adding a descriptive statistics to the input dictionary.

        """
        df_copy: pd.DataFrame = self.df.copy()
        self.args["data_statistic"] = df_copy.describe(
            percentiles=np.arange(0.1, 1.0, 0.1).tolist(),
        ).to_dict(orient="split")
        try:
            if isinstance(self.args["energy_start"], (int, float)) or isinstance(
                self.args["energy_stop"],
                (int, float),
            ):
                df_copy = self.energy_range(df_copy, self.args)
            if self.args["shift"]:
                df_copy = self.energy_shift(df_copy, self.args)
            if self.args["oversampling"]:
                df_copy = self.oversampling(df_copy, self.args)
            if self.args["smooth"]:
                df_copy = self.smooth_signal(df_copy, self.args)
        except KeyError as e:
            msg = f"Missing required preprocessing key: {e}"
            raise KeyError(msg) from e
        return (df_copy, self.args)

    @staticmethod
    def energy_range(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Select the energy range for fitting.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are shrinked according to the energy range.

        """
        energy_start: int | float = args["energy_start"]
        energy_stop: int | float = args["energy_stop"]

        df_copy = df.copy()
        if isinstance(energy_start, (int, float)) and isinstance(
            energy_stop,
            (int, float),
        ):
            return df_copy.loc[
                (df[args["column"][0]] >= energy_start)
                & (df[args["column"][0]] <= energy_stop)
            ]
        if isinstance(energy_start, (int, float)):
            return df_copy.loc[df[args["column"][0]] >= energy_start]
        if isinstance(energy_stop, (int, float)):
            return df_copy.loc[df[args["column"][0]] <= energy_stop]
        return None  # pragma: no cover

    @staticmethod
    def energy_shift(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Shift the energy axis by a given value.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are energy-shifted by the given value.

        """
        df_copy: pd.DataFrame = df.copy()
        df_copy.loc[:, args["column"][0]] = (
            df[args["column"][0]].to_numpy() + args["shift"]
        )
        return df_copy

    @staticmethod
    def oversampling(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Oversampling the data to increase the resolution of the data.

        !!! note "About Oversampling"
            In this implementation of oversampling, the data is oversampled by the
             factor of 5. In case of data with only a few points, the increased
             resolution should allow to easier solve the optimization problem. The
             oversampling based on a simple linear regression.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are oversampled by the factor of 5.

        """
        x_values = np.linspace(
            df[args["column"][0]].min(),
            df[args["column"][0]].max(),
            5 * df.shape[0],
        )
        y_values = np.interp(
            x_values,
            df[args["column"][0]].to_numpy(),
            df[args["column"][1]].to_numpy(),
        )
        return pd.DataFrame({args["column"][0]: x_values, args["column"][1]: y_values})

    @staticmethod
    def smooth_signal(df: pd.DataFrame, args: dict[str, Any]) -> pd.DataFrame:
        """Smooth the intensity values.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are smoothed by the given value.

        """
        box = np.ones(args["smooth"]) / args["smooth"]
        df_copy: pd.DataFrame = df.copy()
        df_copy.loc[:, args["column"][1]] = np.convolve(
            df[args["column"][1]].to_numpy(),
            box,
            mode="same",
        )
        return df_copy

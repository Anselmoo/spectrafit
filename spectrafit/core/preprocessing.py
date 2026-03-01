"""Pre-processing utilities for SpectraFit.

This module contains the PreProcessing class for data pre-processing.
"""

from __future__ import annotations

from typing import Any
from typing import TypedDict
from typing import cast

import numpy as np
import pandas as pd


class PreProcessingArgs(TypedDict, total=False):
    """Typed dictionary for preprocessing arguments.

    Attributes:
        energy_start: Starting energy for fitting range.
        energy_stop: Ending energy for fitting range.
        shift: Constant energy shift to apply.
        oversampling: Whether to oversample the data.
        smooth: Number of smoothing points.
        column: Column names for energy and intensity axes.

    """

    energy_start: float | None
    energy_stop: float | None
    shift: float
    oversampling: bool
    smooth: int
    column: list[str]


class PreProcessing:
    """Summarized all pre-processing-filters  together."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize PreProcessing class.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args: The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        self.df = df
        self.args = args

    def __call__(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Apply all pre-processing-filters.

        Returns:
            tuple: A tuple of (DataFrame, dict) where:

                - DataFrame containing the input data (`x` and `data`), which
                  are optionally shrunk, shifted, oversampled, or smoothed.
                - Dictionary with descriptive statistics added.

        """
        df_copy: pd.DataFrame = self.df.copy()
        # Create a new dictionary instead of modifying the original
        args_copy = self.args.copy()
        args_copy["data_statistic"] = df_copy.describe(
            percentiles=np.arange(0.1, 1.0, 0.1).tolist(),
        ).to_dict(orient="split")
        try:
            pp_args = cast("PreProcessingArgs", self.args)
            if isinstance(self.args["energy_start"], (int, float)) or isinstance(
                self.args["energy_stop"],
                (int, float),
            ):
                df_copy = self.energy_range(df_copy, pp_args)
            if self.args["shift"]:
                df_copy = self.energy_shift(df_copy, pp_args)
            if self.args["oversampling"]:
                df_copy = self.oversampling(df_copy, pp_args)
            if self.args["smooth"]:
                df_copy = self.smooth_signal(df_copy, pp_args)
        except KeyError as e:
            msg = f"Missing required preprocessing key: {e}"
            raise KeyError(msg) from e
        return (df_copy, args_copy)

    @staticmethod
    def energy_range(df: pd.DataFrame, args: PreProcessingArgs) -> pd.DataFrame:
        """Select the energy range for fitting.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (PreProcessingArgs): Preprocessing arguments containing
                 ``energy_start``, ``energy_stop``, and ``column`` keys.

        Returns:
            pd.DataFrame: DataFrame containing the `optimized` input data
                 (`x` and `data`), which are shrinked according to the energy range.

        """
        energy_start: int | float | None = args["energy_start"]
        energy_stop: int | float | None = args["energy_stop"]

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
    def energy_shift(df: pd.DataFrame, args: PreProcessingArgs) -> pd.DataFrame:
        """Shift the energy axis by a given value.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (PreProcessingArgs): Preprocessing arguments containing
                 ``column`` and ``shift`` keys.

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
    def oversampling(df: pd.DataFrame, args: PreProcessingArgs) -> pd.DataFrame:
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
            args (PreProcessingArgs): Preprocessing arguments containing
                 ``column`` key with energy and intensity column names.

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
    def smooth_signal(df: pd.DataFrame, args: PreProcessingArgs) -> pd.DataFrame:
        """Smooth the intensity values.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (PreProcessingArgs): Preprocessing arguments containing
                 ``smooth`` and ``column`` keys.

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

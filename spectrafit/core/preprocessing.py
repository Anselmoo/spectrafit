"""Pre-processing utilities for SpectraFit.

This module contains the PreProcessing class for data pre-processing.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from typing import Any

import numpy as np
import pandas as pd


if TYPE_CHECKING:
    from spectrafit.core.fitting_config import UnifiedFittingConfig


class PreProcessing:
    """Summarized all pre-processing-filters together."""

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Initialize PreProcessing class.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``).
            config: Validated fitting configuration providing column names,
                energy range, shift, oversampling, and smoothing settings.

        """
        self.df = df
        self.config = config

    def __call__(self) -> tuple[pd.DataFrame, dict[str, Any]]:
        """Apply all pre-processing-filters.

        Returns:
            tuple: A tuple of (DataFrame, dict) where:

                - DataFrame containing the input data (``x`` and ``data``), which
                  are optionally shrunk, shifted, oversampled, or smoothed.
                - Dictionary with ``data_statistic`` key containing descriptive
                  statistics of the raw input frame.

        """
        df_copy: pd.DataFrame = self.df.copy()
        result: dict[str, Any] = {
            "data_statistic": df_copy.describe(
                percentiles=np.arange(0.1, 1.0, 0.1).tolist(),
            ).to_dict(orient="split"),
        }
        if self.config.energy_start is not None or self.config.energy_stop is not None:
            df_copy = self.energy_range(df_copy, self.config)
        if self.config.shift:
            df_copy = self.energy_shift(df_copy, self.config)
        if self.config.oversampling:
            df_copy = self.oversampling(df_copy, self.config)
        if self.config.smooth:
            df_copy = self.smooth_signal(df_copy, self.config)
        return (df_copy, result)

    @staticmethod
    def energy_range(
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
    ) -> pd.DataFrame:
        """Select the energy range for fitting.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``).
            config: Fitting configuration with ``energy_start``, ``energy_stop``,
                and ``column`` fields.

        Returns:
            pd.DataFrame: DataFrame shrunk to the requested energy range.

        """
        energy_start = config.energy_start
        energy_stop = config.energy_stop
        x_col = config.column.x
        df_copy = df.copy()

        if energy_start is not None and energy_stop is not None:
            return df_copy.loc[(df[x_col] >= energy_start) & (df[x_col] <= energy_stop)]
        if energy_start is not None:
            return df_copy.loc[df[x_col] >= energy_start]
        if energy_stop is not None:
            return df_copy.loc[df[x_col] <= energy_stop]
        return df_copy

    @staticmethod
    def energy_shift(
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
    ) -> pd.DataFrame:
        """Shift the energy axis by a given value.

        Args:
            df: DataFrame containing the input data.
            config: Fitting configuration with ``column`` and ``shift`` fields.

        Returns:
            pd.DataFrame: DataFrame with energy axis shifted by ``config.shift``.

        """
        df_copy: pd.DataFrame = df.copy()
        x_col = config.column.x
        df_copy.loc[:, x_col] = df[x_col].to_numpy() + config.shift
        return df_copy

    @staticmethod
    def oversampling(
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
    ) -> pd.DataFrame:
        """Oversample the data to increase the resolution of the data.

        !!! note "About Oversampling"
            In this implementation of oversampling, the data is oversampled by the
             factor of 5. In case of data with only a few points, the increased
             resolution should allow to easier solve the optimization problem. The
             oversampling based on a simple linear regression.

        Args:
            df: DataFrame containing the input data.
            config: Fitting configuration with ``column`` field providing x and y
                column names.

        Returns:
            pd.DataFrame: DataFrame oversampled by a factor of 5.

        """
        x_col = config.column.x
        y_col = config.column.y
        x_values = np.linspace(
            df[x_col].min(),
            df[x_col].max(),
            5 * df.shape[0],
        )
        y_values = np.interp(
            x_values,
            df[x_col].to_numpy(),
            df[y_col].to_numpy(),
        )
        return pd.DataFrame({x_col: x_values, y_col: y_values})

    @staticmethod
    def smooth_signal(
        df: pd.DataFrame,
        config: UnifiedFittingConfig,
    ) -> pd.DataFrame:
        """Smooth the intensity values.

        Args:
            df: DataFrame containing the input data.
            config: Fitting configuration with ``smooth`` and ``column`` fields.

        Returns:
            pd.DataFrame: DataFrame with intensity values smoothed by a
                box-car filter of width ``config.smooth``.

        """
        box = np.ones(config.smooth) / config.smooth
        y_col = config.column.y
        df_copy: pd.DataFrame = df.copy()
        df_copy.loc[:, y_col] = np.convolve(
            df[y_col].to_numpy(),
            box,
            mode="same",
        )
        return df_copy

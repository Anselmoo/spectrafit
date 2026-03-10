"""Pre-processing utilities for SpectraFit.

This module provides pure preprocessing functions and the `preprocess`
entry point that applies them in sequence based on the fitting configuration.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from spectrafit.models.preprocess_result import PreprocessResult


if TYPE_CHECKING:
    from spectrafit.core.fitting_config import UnifiedFittingConfig


type StepFn = Callable[[pd.DataFrame, UnifiedFittingConfig], pd.DataFrame]
"""A single preprocessing step: ``(df, config) -> df``."""

type _StepGuard = Callable[[UnifiedFittingConfig], bool]
"""Predicate that decides whether a preprocessing step should run."""


def energy_range(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
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


def energy_shift(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
    """Shift the energy axis by a given value.

    Args:
        df: DataFrame containing the input data.
        config: Fitting configuration with ``column`` and ``shift`` fields.

    Returns:
        pd.DataFrame: DataFrame with energy axis shifted by ``config.shift``.

    """
    df_copy = df.copy()
    x_col = config.column.x
    df_copy.loc[:, x_col] = df[x_col].to_numpy() + config.shift
    return df_copy


def oversampling(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
    """Oversample the data to increase the resolution.

    !!! note "About Oversampling"
        In this implementation the data is oversampled by a factor of 5.
        For data with only a few points the increased resolution helps the
        optimiser converge. Interpolation uses simple linear regression.

    Args:
        df: DataFrame containing the input data.
        config: Fitting configuration with ``column`` field providing x and y
            column names.

    Returns:
        pd.DataFrame: DataFrame oversampled by a factor of 5.

    """
    x_col = config.column.x
    y_col = config.column.y
    x_values = np.linspace(df[x_col].min(), df[x_col].max(), 5 * df.shape[0])
    y_values = np.interp(x_values, df[x_col].to_numpy(), df[y_col].to_numpy())
    return pd.DataFrame({x_col: x_values, y_col: y_values})


def smooth_signal(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
    """Smooth the intensity values with a box-car filter.

    Args:
        df: DataFrame containing the input data.
        config: Fitting configuration with ``smooth`` and ``column`` fields.

    Returns:
        pd.DataFrame: DataFrame with intensity values smoothed by a
            box-car filter of width ``config.smooth``.

    """
    box = np.ones(config.smooth) / config.smooth
    y_col = config.column.y
    df_copy = df.copy()
    df_copy.loc[:, y_col] = np.convolve(df[y_col].to_numpy(), box, mode="same")
    return df_copy


_STEPS: list[tuple[_StepGuard, StepFn]] = [
    (lambda c: c.energy_start is not None or c.energy_stop is not None, energy_range),
    (lambda c: bool(c.shift), energy_shift),
    (lambda c: bool(c.oversampling), oversampling),
    (lambda c: bool(c.smooth), smooth_signal),
]
"""Ordered list of ``(guard, step)`` pairs for the preprocessing pipeline."""


def preprocess(df: pd.DataFrame, config: UnifiedFittingConfig) -> PreprocessResult:
    """Apply all configured preprocessing steps to *df*.

    Args:
        df: Raw input DataFrame with energy (x) and intensity (y) columns.
        config: Validated fitting configuration.

    Returns:
        PreprocessResult: Typed result containing the processed DataFrame and
            descriptive statistics of the *raw* input frame.

    """
    data_statistic = df.describe(
        percentiles=np.arange(0.1, 1.0, 0.1).tolist(),
    ).to_dict(orient="split")
    df_out = df.copy()
    for guard, step in _STEPS:
        if guard(config):
            df_out = step(df_out, config)
    return PreprocessResult(df=df_out, data_statistic=data_statistic)


# ---------------------------------------------------------------------------
# Backward-compat shim — scheduled for removal in v2.1.0.
# ---------------------------------------------------------------------------


class PreProcessing:
    """Deprecated wrapper around `preprocess`.

    Use `preprocess` directly instead.

    !!! warning "Deprecated"
        Will be removed in v2.1.0.  Replace ``PreProcessing(df, config)()``
        with ``preprocess(df, config)``.

    """

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Initialize the backward-compat shim.

        Args:
            df: DataFrame containing the input data (``x`` and ``data``).
            config: Validated fitting configuration providing column names,
                energy range, shift, oversampling, and smoothing settings.

        """
        self.df = df
        self.config = config

    def __call__(self) -> PreprocessResult:
        """Apply all pre-processing-filters.

        Returns:
            PreprocessResult: Typed result with the processed DataFrame and
                descriptive statistics of the raw input frame.

        """
        return preprocess(self.df, self.config)

    @staticmethod
    def energy_range(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
        """Delegate to module-level `energy_range`."""
        return energy_range(df, config)

    @staticmethod
    def energy_shift(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
        """Delegate to module-level `energy_shift`."""
        return energy_shift(df, config)

    @staticmethod
    def oversampling(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
        """Delegate to module-level `oversampling`."""
        return oversampling(df, config)

    @staticmethod
    def smooth_signal(df: pd.DataFrame, config: UnifiedFittingConfig) -> pd.DataFrame:
        """Delegate to module-level `smooth_signal`."""
        return smooth_signal(df, config)

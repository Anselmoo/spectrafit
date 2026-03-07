"""Data loading utilities for SpectraFit.

This module contains functions for loading data from various file formats.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from spectrafit.models.data_config import DataConfig


def load_data(args: DataConfig) -> pd.DataFrame:
    """Load the data from a text/CSV file.

    !!! note "About the data format"

        Load data from a txt file, which can be an ASCII file as txt, csv, or
        user-specific but rational file. The file can be separated by a delimiter.

        In case of 2d data, the columns has to be defined. In case of 3D data, all
        columns are considered as data.

    Args:
        args: Validated :class:`~spectrafit.models.data_config.DataConfig` specifying
            file path, column names, separator, and global fitting mode.

    Returns:
        pd.DataFrame: DataFrame containing the input data (``x`` and ``data``),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.

    Raises:
        ValueError: If the file cannot be loaded or the format is invalid.

    """
    usecols = None if args.global_ else [args.x_col, args.y_col]
    try:
        return pd.read_csv(
            args.infile,
            sep=args.separator,
            header=args.header,
            usecols=usecols,
            dtype=np.float64,
            decimal=args.decimal,
            comment=args.comment,
        )
    except ValueError as e:
        msg = f"Failed to load data from '{args.infile}': {e}"
        raise ValueError(msg) from e

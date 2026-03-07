"""Data loading utilities for SpectraFit.

This module contains functions for loading data from various file formats,
including automatic separator detection for CSV, TSV, and whitespace-delimited
spectral files (e.g. ``.txt``, ``.dat``, ``.out``).
"""

from __future__ import annotations

import csv

from pathlib import Path

import numpy as np
import pandas as pd

from spectrafit.models.data_config import DataConfig


_DEFAULT_SEPARATOR = r"\s+"
_SNIFF_BYTES = 4096


def sniff_separator(path: Path, default: str = _DEFAULT_SEPARATOR) -> str:
    r"""Detect the column separator of a delimited data file.

    Uses :class:`csv.Sniffer` to identify comma (``,``), tab (``\t``), or
    semicolon (``;``) separators.  Falls back to *default* (``\s+``) when
    the file uses whitespace or multiple spaces — which pandas handles
    natively with ``sep=r"\s+"``.

    The detection is intentionally **non-destructive**: the first
    :data:`_SNIFF_BYTES` bytes are read as text, leaving the actual file
    handle untouched.

    Args:
        path: Path to the data file.
        default: Separator string to return when auto-detection fails.
            Defaults to ``r"\s+"`` (whitespace-delimited).

    Returns:
        Detected separator string, or *default* if detection is inconclusive.

    Examples:
        >>> # For a comma-separated file
        >>> sniff_separator(Path("spectrum.csv"))
        ','
        >>> # For a whitespace-separated .dat file
        >>> sniff_separator(Path("spectrum.dat"))
        '\\s+'
    """
    try:
        raw_bytes = path.read_bytes()[:_SNIFF_BYTES]
        sample = raw_bytes.decode(errors="replace")
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except (csv.Error, OSError, UnicodeDecodeError):
        return default
    else:
        return dialect.delimiter


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
    # Auto-detect separator when the user left it as the default "\s+".
    # Explicit user-set separators are never overridden.
    separator = args.separator
    if separator == _DEFAULT_SEPARATOR and isinstance(args.infile, Path):
        separator = sniff_separator(args.infile, default=_DEFAULT_SEPARATOR)
    try:
        return pd.read_csv(
            args.infile,
            sep=separator,
            header=args.header,
            usecols=usecols,
            dtype=np.float64,
            decimal=args.decimal,
            comment=args.comment,
        )
    except ValueError as e:
        msg = f"Failed to load data from '{args.infile}': {e}"
        raise ValueError(msg) from e

"""Data loading utilities for SpectraFit.

This module contains functions for loading data from various file formats.
"""

from __future__ import annotations

import gzip
import pickle

from pathlib import Path  # noqa: TC003

import numpy as np
import pandas as pd

from spectrafit.models.data_config import DataConfig


def load_data(args: DataConfig) -> pd.DataFrame:
    """Load the data from a txt file.

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

    """
    try:
        if args.global_:
            return pd.read_csv(
                args.infile,
                sep=args.separator,
                header=args.header,
                dtype=np.float64,
                decimal=args.decimal,
                comment=args.comment,
            )
        return pd.read_csv(
            args.infile,
            sep=args.separator,
            header=args.header,
            usecols=[args.x_col, args.y_col],
            dtype=np.float64,
            decimal=args.decimal,
            comment=args.comment,
        )
    except ValueError as e:
        msg = f"Failed to load data from '{args.infile}': {e}"
        raise ValueError(msg) from e


def unicode_check(f: object, encoding: str = "latin1") -> object:
    """Check if the pkl file is encoded in unicode.

    Args:
        f: The pkl file to load.
        encoding: The encoding to use. Defaults to ``"latin1"``.

    Returns:
        object: The pkl file, which can be a nested dictionary containing raw data,
            metadata, and other information.

    """
    try:
        data_dict = pickle.load(f)  # type: ignore[arg-type]
    except UnicodeDecodeError:  # pragma: no cover
        data_dict = pickle.load(f, encoding=encoding)  # type: ignore[arg-type]
    return data_dict


def pkl2any(pkl_fname: Path, encoding: str = "latin1") -> object:
    """Load a pkl file and return the data as a any type of data or object.

    Args:
        pkl_fname: The pkl file to load.
        encoding: The encoding to use. Defaults to ``"latin1"``.

    Raises:
        ValueError: If the file format is not supported.

    Returns:
        object: Data or objects, which can contain various data types supported by pickle.

    """
    if pkl_fname.suffix == ".gz":
        with gzip.open(pkl_fname, "rb") as f:
            return unicode_check(f, encoding=encoding)
    elif pkl_fname.suffix == ".pkl":
        with pkl_fname.open("rb") as f:
            return unicode_check(f, encoding=encoding)
    else:
        choices = [".pkl", ".pkl.gz"]
        msg = (
            f"File format '{pkl_fname.suffix}' is not supported. "
            f"Supported file formats are: {choices}"
        )
        raise ValueError(msg)


def pure_fname(fname: Path) -> Path:
    """Return the filename without the suffix.

    Pure filename without the suffix is implemented to avoid the problem with
    multiple dots in the filename like ``test.pkl.gz`` or ``test.tar.gz``.
    The ``stem`` attribute of the ``Path`` class returns the filename without the
    suffix, but it also removes only the last suffix. Hence, ``test.pkl.gz``
    will be returned as ``test.pkl`` and not as ``test``. This function returns
    the filename without the suffix. It is implemented recursively to remove
    all suffixes.

    Args:
        fname: The filename to be processed.

    Returns:
        Path: The filename without the suffix.

    """
    _fname = fname.parent / fname.stem
    return pure_fname(_fname) if _fname.suffix else _fname

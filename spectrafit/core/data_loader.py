"""Data loading utilities for SpectraFit.

This module contains functions for loading data from various file formats.
"""

from __future__ import annotations

import gzip
import json
import pickle

from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any

import numpy as np
import pandas as pd
import tomli
import yaml


if TYPE_CHECKING:
    from collections.abc import MutableMapping


def read_input_file(fname: Path) -> MutableMapping[str, Any]:
    """Read the input file.

    Read the input file as `toml`, `json`, or `yaml` files and return as a dictionary.

    Args:
        fname (str): Name of the input file.

    Raises:
        OSError: If the input file is not supported.

    Returns:
        dict: Return the input file arguments as a dictionary with additional
             information beyond the command line arguments.

    """
    fname = Path(fname)

    if fname.suffix == ".toml":
        with fname.open("rb") as f:
            args = tomli.load(f)
    elif fname.suffix == ".json":
        with fname.open(encoding="utf-8") as f:
            args = json.load(f)
    elif fname.suffix in {".yaml", ".yml"}:
        with fname.open(encoding="utf-8") as f:
            args = yaml.load(f, Loader=yaml.FullLoader)
    else:
        msg = (
            f"ERROR: Input file {fname} has not supported file format.\n"
            "Supported fileformats are: '*.json', '*.yaml', and '*.toml'"
        )
        raise OSError(
            msg,
        )
    return args


def load_data(args: dict[str, str]) -> pd.DataFrame:
    """Load the data from a txt file.

    !!! note "About the data format"

        Load data from a txt file, which can be an ASCII file as txt, csv, or
        user-specific but rational file. The file can be separated by a delimiter.

        In case of 2d data, the columns has to be defined. In case of 3D data, all
        columns are considered as data.

    Args:
        args (Dict[str,str]): The input file arguments as a dictionary with additional
             information beyond the command line arguments.

    Returns:
        pd.DataFrame: DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.

    """
    try:
        if args["global_"]:
            return pd.read_csv(
                args["infile"],
                sep=args["separator"],
                header=args["header"],
                dtype=np.float64,
                decimal=args["decimal"],
                comment=args["comment"],
            )
        return pd.read_csv(
            args["infile"],
            sep=args["separator"],
            header=args["header"],
            usecols=args["column"],
            dtype=np.float64,
            decimal=args["decimal"],
            comment=args["comment"],
        )
    except ValueError as e:
        msg = f"Failed to load data from '{args.get('infile', 'unknown')}': {e}"
        raise ValueError(msg) from e


def check_keywords_consistency(
    check_args: MutableMapping[str, Any],
    ref_args: dict[str, Any],
) -> None:
    """Check if the keywords are consistent.

    Check if the keywords are consistent between two dictionaries. The two dictionaries
    are reference keywords of the `cmd_line_args` and the `args` of the `input_file`.

    Args:
        check_args (MutableMapping[str, Any]): First dictionary to be checked.
        ref_args (Dict[str,Any]): Second dictionary to be checked.

    Raises:
        KeyError: If the keywords are not consistent.

    """
    for key in check_args:
        if key not in ref_args:
            msg = f"ERROR: The {key} is not parameter of the `cmd-input`!"
            raise KeyError(msg)


def unicode_check(f: Any, encoding: str = "latin1") -> Any:
    """Check if the pkl file is encoded in unicode.

    Args:
        f (Any): The pkl file to load.
        encoding (str, optional): The encoding to use. Defaults to "latin1".

    Returns:
        Any: The pkl file, which can be a nested dictionary containing raw data,
            metadata, and other information.

    """
    try:
        data_dict = pickle.load(f)
    except UnicodeDecodeError:  # pragma: no cover
        data_dict = pickle.load(f, encoding=encoding)
    return data_dict


def pkl2any(pkl_fname: Path, encoding: str = "latin1") -> Any:
    """Load a pkl file and return the data as a any type of data or object.

    Args:
        pkl_fname (Path): The pkl file to load.
        encoding (str, optional): The encoding to use. Defaults to "latin1".

    Raises:
        ValueError: If the file format is not supported.

    Returns:
        Any: Data or objects, which can contain various data types supported by pickle.

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
    multiple dots in the filename like `test.pkl.gz` or `test.tar.gz`.
    The `stem` attribute of the `Path` class returns the filename without the
    suffix, but it also removes only the last suffix. Hence, the `test.pkl.gz`
    will be returned as `test.pkl` and not as `test`. This function returns
    the filename without the suffix. It is implemented recursively to remove
    all suffixes.

    Args:
        fname (Path): The filename to be processed.

    Returns:
        Path: The filename without the suffix.

    """
    _fname = fname.parent / fname.stem
    return pure_fname(_fname) if _fname.suffix else _fname

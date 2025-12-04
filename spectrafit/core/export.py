"""Export utilities for SpectraFit.

This module contains the SaveResult class and utility functions for exporting results.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


class SaveResult:
    """Saving the result of the fitting process."""

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize SaveResult class.

        !!! note "About SaveResult"

            The SaveResult class is responsible for saving the results of the
            optimization process. The results are saved in the following formats:

            1. JSON (default) for all results and meta data of the fitting process.
            2. CSV for the results of the optimization process.

        !!! note "About the output `CSV`-file"

            The output files are seperated into three classes:

                1. The `results` of the optimization process.
                2. The `correlation analysis` of the optimization process.
                3. The `error analysis` of the optimization process.

            The result outputfile contains the following information:

                1. The column names of the energy axis (`x`) and the intensity values
                (`data`)
                2. The name of the column containing the energy axis (`x`)
                3. The name of the column containing the intensity values (`data`)
                4. The name of the column containing the best fit (`best_fit`)
                5. The name of the column containing the residuum (`residuum`)
                6. The name of the column containing the model contribution (`model`)
                7. The name of the column containing the error of the model
                    contribution (`model_error`)
                8. The name of the column containing the error of the best fit
                    (`best_fit_error`)
                9. The name of the column containing the error of the residuum
                    (`residuum_error`)

            The `correlation analysis` file contains the following information about all
            attributes of the model:

                1. Energy
                2. Intensity or Intensities (global fitting)
                3. Residuum
                4. Best fit
                5. Model contribution(s)

            The `error analysis` file contains the following information about all model
            attributes vs:

                1. Initial model values
                2. Current model values
                3. Best model values
                4. Residuum / error relative to the best fit
                5. Residuum / error relative to the absolute fit

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
                 as well as the best fit and the corresponding residuum. Hence, it will
                 be extended by the single contribution of the model.
            args (dict[str,Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        self.df = df
        self.args = transform_nested_types(args)

    def __call__(self) -> None:
        """Call the SaveResult class."""
        self.save_as_json()
        self.save_as_csv()

    def save_as_csv(self) -> None:
        """Save the the fit results to csv files.

        !!! note "About saving the fit results"
            The fit results are saved to csv files and are divided into three different
            categories:

                1. The `results` of the optimization process.
                2. The `correlation analysis` of the optimization process.
                3. The `error analysis` of the optimization process.
        """
        _fname = Path(f"{self.args['outfile']}_fit.csv")
        self.df.to_csv(_fname, index=False)
        pd.DataFrame(**self.args["linear_correlation"]).to_csv(
            Path(f"{self.args['outfile']}_correlation.csv"),
            index=True,
            index_label="attributes",
        )
        pd.DataFrame.from_dict(self.args["fit_insights"]["variables"]).to_csv(
            Path(f"{self.args['outfile']}_components.csv"),
            index=True,
            index_label="attributes",
        )

    def save_as_json(self) -> None:
        """Save the fitting result as json file."""
        if self.args["outfile"]:
            with Path(f"{self.args['outfile']}_summary.json").open(
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(transform_nested_types(self.args), f, indent=4)
        else:
            msg = "No output file provided!"
            raise FileNotFoundError(msg)


def exclude_none_dictionary(value: dict[str, Any]) -> dict[str, Any]:
    """Exclude `None` values from the dictionary.

    Args:
        value (dict[str, Any]): Dictionary to be processed to
            exclude `None` values.

    Returns:
        dict[str, Any]: Dictionary without `None` values.

    """
    if isinstance(value, list):
        return [exclude_none_dictionary(v) for v in value if v is not None]
    if isinstance(value, dict):
        return {
            k: exclude_none_dictionary(v) for k, v in value.items() if v is not None
        }
    return value


def transform_nested_types(value: dict[str, Any]) -> dict[str, Any]:
    """Transform nested types numpy values to python values.

    Args:
        value (dict[str, Any]): Dictionary to be processed to
            transform numpy values to python values.

    Returns:
        dict[str, Any]: Dictionary with python values.

    """
    if isinstance(value, list):
        return [transform_nested_types(v) for v in value]
    if isinstance(value, tuple):
        return tuple(transform_nested_types(v) for v in value)
    if isinstance(value, dict):
        return {k: transform_nested_types(v) for k, v in value.items()}
    if isinstance(value, np.ndarray):
        return transform_nested_types(value.tolist())
    if isinstance(value, (np.int32, np.int64)):
        return int(value)
    if isinstance(value, np.bool_):
        return bool(value)
    return float(value) if isinstance(value, np.float64) else value

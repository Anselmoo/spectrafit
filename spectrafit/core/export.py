"""Export utilities for SpectraFit.

This module contains the SaveResult class and utility functions for exporting results.
"""

from __future__ import annotations

import json

from pathlib import Path
from typing import TYPE_CHECKING
from typing import cast

import numpy as np
import pandas as pd

from spectrafit.models.types import DataSplitDict


if TYPE_CHECKING:
    from spectrafit.core.postprocessing import PostProcessingResult


class SaveResult:
    """Saving the result of the fitting process."""

    def __init__(
        self,
        df: pd.DataFrame,
        post: PostProcessingResult,
        outfile: str,
    ) -> None:
        """Initialize SaveResult class.

        Args:
            df: DataFrame containing the fit results.
            post: Typed post-processing result.
            outfile: Output file path stem (without extension).

        """
        self.df = df
        self.post = post
        self.outfile = outfile

    def __call__(self) -> None:
        """Call the SaveResult class."""
        self.save_as_json()
        self.save_as_csv()

    def save_as_csv(self) -> None:
        """Save the fit results to csv files."""
        _fname = Path(f"{self.outfile}_fit.csv")
        self.df.to_csv(_fname, index=False)
        pd.DataFrame(**cast("DataSplitDict", self.post.linear_correlation)).to_csv(
            Path(f"{self.outfile}_correlation.csv"),
            index=True,
            index_label="attributes",
        )
        pd.DataFrame.from_dict(
            cast("dict[str, dict[str, object]]", self.post.fit_insights)["variables"],
        ).to_csv(
            Path(f"{self.outfile}_components.csv"),
            index=True,
            index_label="attributes",
        )

    def save_as_json(self) -> None:
        """Save the fitting result as json file."""
        if not self.outfile:
            msg = "No output file provided!"
            raise FileNotFoundError(msg)

        summary: dict[str, object] = {
            "fit_insights": transform_nested_types(self.post.fit_insights),
            "confidence_interval": transform_nested_types(
                self.post.confidence_interval
            ),
            "linear_correlation": transform_nested_types(self.post.linear_correlation),
            "fit_result": transform_nested_types(self.post.fit_result_data),
            "regression_metrics": transform_nested_types(self.post.regression_metrics),
            "descriptive_statistic": transform_nested_types(
                self.post.descriptive_statistic
            ),
        }
        with Path(f"{self.outfile}_summary.json").open(
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(summary, f, indent=4)


def exclude_none_dictionary(value: object) -> object:
    """Exclude `None` values from the dictionary.

    Recursively processes dicts, lists, and other values to remove ``None``
    entries. Non-dict/list values are returned unchanged.

    Args:
        value (object): Value to be processed. Typically a dict or list,
            but any type is accepted and returned as-is if not a container.

    Returns:
        object: Cleaned value without ``None`` entries.

    """
    if isinstance(value, list):
        return [exclude_none_dictionary(v) for v in value if v is not None]
    if isinstance(value, dict):
        return {
            k: exclude_none_dictionary(v) for k, v in value.items() if v is not None
        }
    return value


def transform_nested_types(value: object) -> object:
    """Transform nested numpy types to native Python values.

    Recursively converts numpy scalars and arrays within dicts, lists, and
    tuples to their native Python equivalents for JSON serialization.

    Args:
        value (object): Value to be processed. Supports dicts, lists,
            tuples, numpy arrays, and numpy scalar types.

    Returns:
        object: Value with all numpy types converted to native Python types.

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

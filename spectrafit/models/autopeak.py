"""Model parameter definition for curve fitting.

This module contains classes for parameter definition and model validation.
AutoPeak detection has been removed in v2.0.0 and will be redesigned.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar
from typing import TypeAlias

from lmfit import Parameters

from spectrafit.api.models_model import DistributionModelAPI


if TYPE_CHECKING:
    import numpy as np
    import pandas as pd

    from numpy.typing import NDArray

# Constants for global fitting modes
GLOBAL_NONE = 0  # No global fitting
GLOBAL_STANDARD = 1  # Standard global fitting
GLOBAL_WITH_PRE = 2  # Global fitting with pre-processing

# Type aliases for the nested peak parameter structure
ParameterConstraint: TypeAlias = dict[str, float | bool | str | None]
"""Single lmfit parameter constraint, e.g. ``{"min": 0, "max": 2, "vary": True, "value": 1}``."""

ModelParameterSpec: TypeAlias = dict[str, ParameterConstraint]
"""Maps parameter names to constraints, e.g. ``{"amplitude": {...}, "center": {...}}``."""

PeakModelSpec: TypeAlias = dict[str, ModelParameterSpec]
"""Maps model names to parameter specs, e.g. ``{"pseudovoigt": {...}}``."""

PeaksDict: TypeAlias = dict[str, PeakModelSpec]
"""All peaks for standard fitting: ``{"1": {"pseudovoigt": {...}}, "2": {...}}``."""

FittingArgs: TypeAlias = dict[str, Any]
"""Main fitting arguments dict with peaks, minimizer, optimizer, column, global_ keys."""


@dataclass(frozen=True)
class ReferenceKeys:
    """Reference keys for model fitting and peak detection."""

    __models__: ClassVar[list[str]] = list(
        DistributionModelAPI.model_json_schema()["properties"].keys(),
    )

    __automodels__: ClassVar[list[str]] = [
        "gaussian",
        "orcagaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
    ]

    def model_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Model name.

        Raises:
            NotImplementedError: If the model is not implemented.

        """
        model_prefix = model.split("_")[0]

        # Check in main models list
        if model_prefix not in self.__models__:
            msg = f"{model} is not supported!"
            raise NotImplementedError(msg)

    def automodel_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Auto Model name (gaussian, orcagaussian,
                lorentzian, voigt, or pseudovoigt).

        Raises:
            KeyError: If the model is not supported.

        """
        if model not in self.__automodels__:
            msg = f"{model} is not supported for auto detection! Use one of {self.__automodels__}"
            raise KeyError(msg)


class ModelParameters:
    """Class to define the model parameters."""

    def __init__(self, df: pd.DataFrame, args: FittingArgs) -> None:
        """Initialize the model parameters.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (FittingArgs):
                 Nested arguments dictionary for the model based on **one** or **two**
                 `int` keys depending if global fitting parameters, will explicit
                 defined or not.

        """
        self.col_len = df.shape[1] - 1
        self.args = args
        self.params = Parameters()
        self.x, self.data = self.df_to_numvalues(df=df, args=args)

    def df_to_numvalues(
        self,
        df: pd.DataFrame,
        args: FittingArgs,
    ) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Transform the dataframe to numeric values of `x` and `data`.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (FittingArgs): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            tuple[NDArray[np.float64], NDArray[np.float64]]: Tuple of `x` and
                 `data` as numpy arrays.

        """
        if args["global_"]:
            return (
                df[args["column"][0]].to_numpy(),
                df.loc[:, df.columns != args["column"][0]].to_numpy(),
            )
        return (df[args["column"][0]].to_numpy(), df[args["column"][1]].to_numpy())

    @property
    def return_params(self) -> Parameters:
        """Return the `class` representation of the model parameters.

        Returns:
            Parameters: Model parameters class.

        """
        self.__perform__()
        return self.params

    def __str__(self) -> str:
        """Return the `string` representation of the model parameters.

        Returns:
            str: String representation of the model parameters.

        """
        self.__perform__()
        return str(self.params)

    def __perform__(self) -> None:
        """Perform the model parameter definition."""
        if self.args["global_"] == GLOBAL_NONE:
            self.define_parameters()
        elif self.args["global_"] == GLOBAL_STANDARD:
            self.define_parameters_global()
        elif self.args["global_"] == GLOBAL_WITH_PRE:
            self.define_parameters_global_pre()

    def define_parameters(self) -> None:
        """Define the input parameters for a `params`-dictionary for classic fitting."""
        for key_1, value_1 in self.args["peaks"].items():
            self.define_parameters_loop(key_1=key_1, value_1=value_1)

    def define_parameters_loop(self, key_1: str, value_1: PeakModelSpec) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            value_1 (PeakModelSpec): The value of the first level of the input
                 dictionary.

        """
        for key_2, value_2 in value_1.items():
            self.define_parameters_loop_2(key_1=key_1, key_2=key_2, value_2=value_2)

    def define_parameters_loop_2(
        self,
        key_1: str,
        key_2: str,
        value_2: ModelParameterSpec,
    ) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            value_2 (ModelParameterSpec): The value of the first level of the input
                 dictionary.

        """
        for key_3, value_3 in value_2.items():
            self.define_parameters_loop_3(
                key_1=key_1,
                key_2=key_2,
                key_3=key_3,
                value_3=value_3,
            )

    def define_parameters_loop_3(
        self,
        key_1: str,
        key_2: str,
        key_3: str,
        value_3: ParameterConstraint,
    ) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            key_3 (str): The key of the third level of the input dictionary.
            value_3 (ParameterConstraint): The value of the third level of the input
                 dictionary.

        """
        self.params.add(f"{key_2}_{key_3}_{key_1}", **value_3)

    def define_parameters_global(self) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting."""
        for col_i in range(self.col_len):
            for key_1, value_1 in self.args["peaks"].items():
                for key_2, value_2 in value_1.items():
                    for key_3, value_3 in value_2.items():
                        self._define_parameter(
                            col_i=col_i,
                            key_1=key_1,
                            key_2=key_2,
                            key_3=key_3,
                            value_3=value_3,
                        )

    def _define_parameter(
        self,
        col_i: int,
        key_1: str,
        key_2: str,
        key_3: str,
        value_3: ParameterConstraint,
    ) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting.

        Args:
            col_i (int): The column index.
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            key_3 (str): The key of the third level of the input dictionary.
            value_3 (ParameterConstraint): The value of the third level of the input
                 dictionary.

        """
        if col_i:
            if key_3 != "amplitude":
                self.params.add(
                    f"{key_2}_{key_3}_{key_1}_{col_i + 1}",
                    expr=f"{key_2}_{key_3}_{key_1}_1",
                )
            else:
                self.params.add(
                    f"{key_2}_{key_3}_{key_1}_{col_i + 1}",
                    **value_3,
                )

        else:
            self.params.add(f"{key_2}_{key_3}_{key_1}_1", **value_3)

    def define_parameters_global_pre(self) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting.

        !!! warning "About `params` for global fitting"

            `define_parameters_global_pre` requires fully defined `params`-dictionary
            in the json, toml, or yaml file input. This means:

            1. Number of the spectra must be defined.
            2. Number of the peaks must be defined.
            3. Number of the parameters must be defined.
            4. The parameters must be defined.
        """
        for key_1, value_1 in self.args["peaks"].items():
            for key_2, value_2 in value_1.items():
                for key_3, value_3 in value_2.items():
                    for key_4, value_4 in value_3.items():
                        self.params.add(f"{key_3}_{key_4}_{key_2}_{key_1}", **value_4)

"""Solver models for curve fitting.

This module contains the SolverModels class and helper functions for solving
fitting problems using lmfit.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from math import log
from math import pi
from math import sqrt
from typing import TYPE_CHECKING
from typing import Any
from typing import ClassVar

import numpy as np

from lmfit import Minimizer
from lmfit import Parameters

from spectrafit.api.tools_model import GlobalFittingAPI
from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.models.autopeak import ModelParameters
from spectrafit.models.autopeak import ReferenceKeys
from spectrafit.models.distributions import DistributionModels


if TYPE_CHECKING:
    import pandas as pd

    from numpy.typing import NDArray


class SolverModels(ModelParameters):
    """Solving models for 2D and 3D data sets.

    !!! hint "Solver Modes"
        * `"2D"`: Solve 2D models via the classic `lmfit` function.
        * `"3D"`: Solve 3D models via global git. For the `global-fitting` procedure,
             the `lmfit` function is used to solve the models with an extended set of
             parameters.
          the `lmfit` function is used.
    """

    def __init__(self, df: pd.DataFrame, args: dict[str, Any]) -> None:
        """Initialize the solver modes.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        """
        super().__init__(df=df, args=args)
        self.args_solver = SolverModelsAPI(**args).model_dump()
        self.args_global = GlobalFittingAPI(**args).model_dump()
        self.params = self.return_params

    def __call__(self) -> tuple[Minimizer, Any]:
        """Solve the fitting model.

        Returns:
            Tuple[Minimizer, Any]: Minimizer class and the fitting results.

        """
        if self.args_global["global_"]:
            minimizer = Minimizer(
                self.solve_global_fitting,
                params=self.params,
                fcn_args=(self.x, self.data),
                **self.args_solver["minimizer"],
            )
        else:
            minimizer = Minimizer(
                self.solve_local_fitting,
                params=self.params,
                fcn_args=(self.x, self.data),
                **self.args_solver["minimizer"],
            )

        result = minimizer.minimize(
            **self.args_solver["optimizer"],
        )
        self.args_solver["optimizer"]["max_nfev"] = minimizer.max_nfev
        return minimizer, result

    @staticmethod
    def solve_local_fitting(
        params: dict[str, Parameters],
        x: NDArray[np.float64],
        data: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Solving the fitting problem.

        Args:
            params (Dict[str, Parameters]): The best optimized parameters of the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 1d-array.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.

        """
        val = np.zeros(x.shape)
        peak_kwargs: dict[tuple[str, str], Parameters] = defaultdict(dict)
        for model_name, param_value in params.items():
            _model = model_name.lower()
            ReferenceKeys().model_check(model=_model)
            c_name = _model.split("_")

            model_key = c_name[0]
            param_name = c_name[1]
            peak_id = c_name[2]
            peak_kwargs[(model_key, peak_id)][param_name] = param_value

        for key, _kwarg in peak_kwargs.items():
            val += getattr(DistributionModels(), key[0])(x, **_kwarg)
        return np.array(val - data, dtype=np.float64)

    @staticmethod
    def solve_global_fitting(
        params: dict[str, Parameters],
        x: NDArray[np.float64],
        data: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        r"""Solving the fitting for global problem.

        !!! note "About implemented models"
            `solve_global_fitting` is the global solution of `solve_local_fitting` a
            wrapper function for the calling the implemented moldels. For the kind of
            supported models see `solve_local_fitting`.

        !!! note "About the global solution"
            The global solution is a solution for the problem, where the `x`-values is
            the energy, but the y-values are the intensities, which has to be fitted as
            one unit. For this reason, the residual is calculated as the difference
            between all the y-values and the global proposed solution. Later the
            residual has to be flattened to a 1-dimensional array and minimized by the
            `lmfit`-optimizer.


        Args:
            params (Dict[str, Parameters]): The best optimized parameters of the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 2D-array.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.

        """
        val = np.zeros(data.shape)
        peak_kwargs: dict[tuple[str, str, str], Parameters] = defaultdict(dict)

        for model, value in params.items():
            model_lower = model.lower()
            ReferenceKeys().model_check(model=model_lower)
            c_name = model_lower.split("_")
            peak_kwargs[(c_name[0], c_name[2], c_name[3])][c_name[1]] = value
        for key, _kwarg in peak_kwargs.items():
            i = int(key[2]) - 1
            val[:, i] += getattr(DistributionModels(), key[0])(x, **_kwarg)

        val -= data
        return val.flatten()


def calculated_model(
    params: dict[str, Parameters],
    x: NDArray[np.float64],
    df: pd.DataFrame,
    global_fit: int,
) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

    !!! note "About calculated models"
        `calculated_model` are also wrapper functions similar to `solve_model`. The
        overall goal is to extract from the best parameters the single contributions in
        the model. Currently, `lmfit` provides only a single model, so the best-fit.

    Args:
        params (Dict[str, Parameters]): The best optimized parameters of the fit.
        x (NDArray[np.float64]): `x`-values of the data.
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        global_fit (int): If 1 or 2, the model is calculated for the global fit.

    Returns:
        pd.DataFrame: Extended dataframe containing the single contributions of the
            models.

    """
    peak_kwargs: dict[Any, Parameters] = defaultdict(dict)

    for model, value in params.items():
        model_lower = model.lower()
        ReferenceKeys().model_check(model=model_lower)
        p_name = model_lower.split("_")
        if global_fit:
            peak_kwargs[(p_name[0], p_name[2], p_name[3])][p_name[1]] = value
        else:
            peak_kwargs[(p_name[0], p_name[2])][p_name[1]] = value

    _df = df.copy()
    for key, _kwarg in peak_kwargs.items():
        c_name = f"{key[0]}_{key[1]}_{key[2]}" if global_fit else f"{key[0]}_{key[1]}"
        _df[c_name] = getattr(DistributionModels(), key[0])(x, **_kwarg)

    return _df


@dataclass(frozen=True)
class Constants:
    """Constants used for calculations.

    This class provides mathematical constants used across the package.
    It's implemented as a frozen dataclass with class variables
    to ensure they can't be modified.
    """

    ln2: ClassVar[float] = log(2.0)
    sq2pi: ClassVar[float] = sqrt(2.0 * pi)
    sqpi: ClassVar[float] = sqrt(pi)
    sq2: ClassVar[float] = sqrt(2.0)
    fwhmg2sig: ClassVar[float] = 1 / (2.0 * sqrt(2.0 * log(2.0)))
    fwhml2sig: ClassVar[float] = 1 / 2.0
    fwhmv2sig: ClassVar[float] = 1 / 3.60131

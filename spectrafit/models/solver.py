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
from typing import ClassVar
from typing import cast

import numpy as np

from lmfit import Minimizer
from lmfit import Parameters

from spectrafit.api.tools_model import SolverModelsAPI
from spectrafit.models.fitting_context import FittingMode
from spectrafit.models.model_parameters import ModelParameters
from spectrafit.models.model_parameters import ReferenceKeys
from spectrafit.models.registry import REGISTRY


if TYPE_CHECKING:
    import pandas as pd

    from lmfit import Parameter
    from lmfit.minimizer import MinimizerResult
    from numpy.typing import NDArray

    from spectrafit.core.fitting_config import UnifiedFittingConfig
    from spectrafit.models.bundle import CompositeModelBundle
    from spectrafit.models.global_fitting import GlobalFittingConfig


class SolverModels(ModelParameters):
    """Solving models for 2D and 3D data sets.

    !!! hint "Solver Modes"
        * `"2D"`: Solve 2D models via the classic `lmfit` function.
        * `"3D"`: Solve 3D models via global git. For the `global-fitting` procedure,
             the `lmfit` function is used to solve the models with an extended set of
             parameters.
          the `lmfit` function is used.
    """

    def __init__(self, df: pd.DataFrame, config: UnifiedFittingConfig) -> None:
        """Initialize the solver modes.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            config (UnifiedFittingConfig): Validated fitting configuration.

        """
        super().__init__(df=df, config=config)
        self._solver_config = SolverModelsAPI(
            minimizer=config.minimizer,
            optimizer=config.optimizer,
        )
        self._is_global = config.global_ == FittingMode.GLOBAL
        self.params = self.return_params

    def __call__(self) -> tuple[Minimizer, MinimizerResult]:
        """Solve the fitting model.

        Returns:
            tuple[Minimizer, MinimizerResult]: Minimizer class and the fitting results.

        """
        if self._is_global:
            cfg: GlobalFittingConfig | None = self.global_fitting_config
            minimizer = Minimizer(
                self.solve_global_fitting,
                params=self.params,
                fcn_args=(self.x, self.data, cfg),
                **self._solver_config.minimizer.model_dump(),
            )
        else:
            minimizer = Minimizer(
                self._local_residual,
                params=self.params,
                fcn_args=(self.x, self.data),
                **self._solver_config.minimizer.model_dump(),
            )

        result = minimizer.minimize(
            **self._solver_config.optimizer.model_dump(exclude_none=True),
        )
        return minimizer, result

    def _local_residual(
        self,
        params: Parameters,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        """Compute residual for local (single-dataset) fitting using the composite bundle.

        Args:
            params (Parameters): Current parameter values from the minimizer.
            x (NDArray[np.float64]): x-values of the data.
            data (NDArray[np.float64]): y-values of the data as 1d-array.

        Returns:
            NDArray[np.float64]: Residual (model - data).

        """
        if self._bundle is None:
            msg = "CompositeModelBundle not initialized"
            raise RuntimeError(msg)
        return np.array(
            self._bundle.composite.eval(params, x=x) - data,
            dtype=np.float64,
        )

    @staticmethod
    def solve_global_fitting(
        params: Parameters,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
        config: GlobalFittingConfig | None = None,
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
            params (Parameters): The best optimized parameters of the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 2D-array.
            config (GlobalFittingConfig | None): Optional global fitting
                configuration with per-dataset weights.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.

        """
        val = np.zeros(data.shape)
        peak_kwargs: dict[tuple[str, str, str], dict[str, Parameter]] = defaultdict(
            dict,
        )

        for model, value in params.items():
            model_lower = model.lower()
            ReferenceKeys().model_check(model=model_lower)
            c_name = model_lower.split("_")
            peak_kwargs[(c_name[0], c_name[2], c_name[3])][c_name[1]] = value
        for key, _kwarg in peak_kwargs.items():
            i = int(key[2]) - 1
            val[:, i] += cast(
                "np.ndarray[tuple[int], np.dtype[np.float64]]",
                REGISTRY.get(key[0]).function(x, **_kwarg),
            )

        residual = val - data

        if config is not None and config.weights is not None:
            weights_arr = np.array(config.weights, dtype=np.float64)
            residual = residual * weights_arr[np.newaxis, :]

        return residual.flatten()


def calculated_model(
    params: Parameters,
    x: NDArray[np.float64],
    df: pd.DataFrame,
    global_fit: bool,
    bundle: CompositeModelBundle | None = None,
) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

    !!! note "About calculated models"
        `calculated_model` are also wrapper functions similar to `solve_model`. The
        overall goal is to extract from the best parameters the single contributions in
        the model. Currently, `lmfit` provides only a single model, so the best-fit.

    Args:
        params (Parameters): The best optimized parameters of the fit.
        x (NDArray[np.float64]): `x`-values of the data.
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        global_fit (bool): ``True`` for global fitting mode.
        bundle (CompositeModelBundle | None): Optional composite model bundle for
            v2 local fits. When provided and ``global_fit`` is ``False``, decomposition uses
            ``bundle.decompose()`` instead of the legacy string-split approach.

    Returns:
        pd.DataFrame: Extended dataframe containing the single contributions of the
            models.

    """
    _df = df.copy()

    if bundle is not None and not global_fit:
        for comp_id, curve in bundle.decompose(params, x).items():
            _df[comp_id] = curve
        return _df

    peak_kwargs: dict[tuple[str, str] | tuple[str, str, str], dict[str, Parameter]] = (
        defaultdict(dict)
    )

    for model, value in params.items():
        model_lower = model.lower()
        ReferenceKeys().model_check(model=model_lower)
        p_name = model_lower.split("_")
        if global_fit:
            peak_kwargs[(p_name[0], p_name[2], p_name[3])][p_name[1]] = value
        else:
            peak_kwargs[(p_name[0], p_name[2])][p_name[1]] = value

    for key, _kwarg in peak_kwargs.items():
        c_name = "_".join(key)
        _df[c_name] = REGISTRY.get(key[0]).function(x, **_kwarg)

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

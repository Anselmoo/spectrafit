"""Minimization models for curve fitting."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
import pandas as pd

from lmfit import Minimizer
from lmfit import Parameters
from numpy.typing import NDArray
from scipy.signal import find_peaks
from scipy.special import erf
from scipy.special import wofz
from scipy.stats import hmean
from spectrafit.api.tools_model import AutopeakAPI
from spectrafit.api.tools_model import GlobalFittingAPI
from spectrafit.api.tools_model import SolverModelsAPI


@dataclass(frozen=True)
class ReferenceKeys:
    """Reference keys for model fitting and peak detection."""

    __models__ = [
        "gaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
        "exponential",
        "power",
        "linear",
        "constant",
        "erf",
        "atan",
        "log",
        "heaviside",
    ]

    __automodels__ = [
        "gaussian",
        "lorentzian",
        "voigt",
        "pseudovoigt",
    ]

    def model_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Model name.

        Raises:
            KeyError: If the model is not supported.
        """
        if model.split("_")[0] not in self.__models__:
            raise KeyError(f"{model} is not supported!")

    def automodel_check(self, model: str) -> None:
        """Check if model is available.

        Args:
            model (str): Auto Model name (gaussian, lorentzian, voigt, or pseudovoigt).

        Raises:
            KeyError: If the model is not supported.
        """
        if model not in self.__automodels__:
            raise KeyError(f"{model} is not supported!")

    def detection_check(self, args: Dict[str, Any]) -> None:
        """Check if detection is available.

        Args:
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Raises:
            KeyError: If the key is not parameter of the `scipy.signal.find_peaks`
                function. This will be checked via `pydantic` in `spectrafit.api`.
        """
        AutopeakAPI(**args)


@dataclass(frozen=True)
class Constants:
    r"""Mathematical constants for the curve models.

    !!! info "Constants"
        $$
        log2 = \log{2 }
        $$

        $$
        sq2pi = \sqrt{2 \pi}
        $$

        $$
        sqpi = \sqrt{ \pi}
        $$

        $$
        sq2 = \sqrt{2 }
        $$

        $$
        sig2fwhm = 2 \sqrt{2\log{2 }}
        $$


    """

    log2 = np.log(2.0)
    sq2pi = np.sqrt(2.0 * np.pi)
    sqpi = np.sqrt(np.pi)
    sq2 = np.sqrt(2.0)
    sig2fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0))


class AutoPeakDetection:
    """Automatic detection of peaks in a spectrum."""

    def __init__(
        self,
        x: NDArray[np.float64],
        data: NDArray[np.float64],
        args: Dict[str, Any],
    ) -> None:
        """Initialize the AutoPeakDetection class.

        Args:
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 1d-array.
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.
        """
        self.x = x
        self.data = data
        self._args = args["autopeak"]

    @staticmethod
    def check_key_exists(
        key: str, args: Dict[str, Any], value: Union[float, Tuple[Any, Any]]
    ) -> Any:
        """Check if a key exists in a dictionary.

        Please check for the reference key also [scipy.signal.find_peaks][1].

        [1]:
            https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html


        Args:
            key (str): Reference key of `scipy.signal.find_peaks`.
            args (Dict[str, Any]): Reference values of `scipy.signal.find_peaks`, if not
                 defined will be set to estimated default values.
            value (Union[float, Tuple[float,float]]): Default value for the reference
                 key.

        Returns:
            Any: The reference value for `scipy.signal.find_peaks`.
        """
        return args.get(key, value)

    @property
    def estimate_height(self) -> Tuple[float, float]:
        r"""Estimate the initial height based on an inverse noise ratio of a signal.

        !!! info "About the estimation of the height"

            The lower end of the height is the inverse noise ratio of the `data`, and
            upper limit is the maximum value of the `data`. The noise ratio of the
            `data` is based on the original implementation by `SciPy`:

            ```python
            def signaltonoise(a, axis=0, ddof=0):
                a = np.asanyarray(a)
                m = a.mean(axis)
                sd = a.std(axis=axis, ddof=ddof)
                return np.where(sd == 0, 0, m / sd)
            ```

        Returns:
            Tuple[float, float]: Tuple of the inverse signal to noise ratio and
                 the maximum value of the `data`.
        """
        return 1 - self.data.mean() / self.data.std(), self.data.max()

    @property
    def estimate_threshold(self) -> Tuple[float, float]:
        """Estimate the threshold value for the peak detection.

        Returns:
            Tuple[float, float]: Minimum and maximum value of the spectrum `data`,
                 respectively, `intensity`.
        """
        return self.data.min(), self.data.max()

    @property
    def estimate_distance(self) -> float:
        """Estimate the initial distance between peaks.

        Returns:
            float: Estimated distance between peaks.
        """
        min_step = np.diff(self.x).min()
        return max(min_step, 1.0)

    @property
    def estimate_prominence(self) -> Tuple[float, float]:
        """Estimate the prominence of a peak.

        !!! info "About the estimation of the prominence"

            The prominence is the difference between the height of the peak and the
            bottom. To get a estimate of the prominence, the height of the peak is
            calculated by maximum value of the `data` and the bottom is calculated by
            the harmonic mean of the `data`.

        Returns:
            Tuple[float, float]: Tuple of the harmonic-mean and maximum value of `data`.
        """
        try:
            return hmean(self.data), self.data.max()
        except ValueError as exc:
            print(f"{exc}: Using standard arithmetic mean of NumPy.\n")
        return self.data.mean(), self.data.max()

    @property
    def estimated_width(self) -> Tuple[float, float]:
        """Estimate the width of a peak.

        !!! info "About the estimation of the width"

            The width of a peak is estimated for a lower and an upper end. For the lower
            end, the minimum stepsize is used. For the upper end, the stepsize between
            the half maximum and the minimum value of the `data` is used as the width.

        Returns:
            Tuple[float, float]: Estimated width lower and uper end of the peaks.
        """
        return (
            np.diff(self.x).min(),
            np.abs(self.x[self.data.argmax()] - self.x[self.data.argmin()]) / 2,
        )

    @property
    def estimated_rel_height(self) -> float:
        """Estimate the relative height of a peak.

        !!! info "About the estimation of the relative height"

            The relative height of a peak is approximated by the difference of the
            harmonic mean value of the `data` and the minimum value of the `data`
            divided by the factor of `2`. In case of negative ratios, the value will be
            set to `Zero`.

        Returns:
            float: Estimated relative height of a peak.
        """
        try:
            rel_height = (hmean(self.data) - self.data.min()) / 4
        except ValueError as exc:
            rel_height = (self.data.mean() - self.data.min()) / 4
            print(f"{exc}: Using standard arithmetic mean of NumPy.\n")
        return rel_height if rel_height > 0 else 0.0

    @property
    def estimated_wlen(self) -> float:
        r"""Estimate the window length for the peak detection.

        !!! info "About the estimation of the window length"

            The window length is the length of the window for the peak detection is
            defined to be 1% of the length of the `data`, consequently the len of the
            `data` is divided by 100. In case of a window length smaller than 1, the
            window length will be set to numerical value of 1, which is defined by
            `1 + 1e-9`.

        Returns:
            float: Estimated window length is set to the numeric value of > 1.
        """
        wlen = self.data.size / 100
        return wlen if wlen > 1.0 else 1 + 1e-9

    @property
    def estimated_plateau_size(self) -> Tuple[float, float]:
        """Estimate the plateau size for the peak detection.

        Returns:
            Tuple[float, float]: Estimated plateau size is set to `zero` for the lower
                 end and the maximum value of the `x` for the upper end.
        """
        return 0.0, self.x.max()

    def initialize_peak_detection(self) -> None:
        """Initialize the peak detection.

        !!! note "Initialize the peak detection"

            This method is used to initialize the peak detection. The initialization can
            be activated by setting the `initialize` attribute to `True`, which will
            automatically estimate the default parameters for the peak detection. In
            case of the `initialize` attribute is defined as dictionary, the proposed
            values are taken from the dictionary if th

        Raise:
            TypeError: If the `initialize` attribute is not of type `bool` or `dict`.
        """
        if isinstance(self._args, bool):
            self.height = self.estimate_height
            self.threshold = self.estimate_threshold
            self.distance = self.estimate_distance
            self.prominence = self.estimate_prominence
            self.width = self.estimated_width
            self.wlen = self.estimated_wlen
            self.rel_height = self.estimated_rel_height
            self.plateau_size = 0
        elif isinstance(self._args, dict):
            ReferenceKeys().detection_check(self._args)
            self.height = self.check_key_exists(
                key="height", args=self._args, value=self.estimate_height
            )
            self.threshold = self.check_key_exists(
                key="threshold", args=self._args, value=self.estimate_threshold
            )
            self.distance = self.check_key_exists(
                key="distance", args=self._args, value=self.estimate_distance
            )
            self.prominence = self.check_key_exists(
                key="prominence", args=self._args, value=self.estimate_prominence
            )
            self.width = self.check_key_exists(
                key="width", args=self._args, value=self.estimated_width
            )
            self.wlen = self.check_key_exists(
                key="wlen", args=self._args, value=self.estimated_wlen
            )
            self.rel_height = self.check_key_exists(
                key="rel_height", args=self._args, value=self.estimated_rel_height
            )
            self.plateau_size = self.check_key_exists(
                key="plateau_size", args=self._args, value=0.0
            )
        else:
            raise TypeError(
                f"The type of the `args` is not supported: {type(self._args)}"
            )

    def __autodetect__(self) -> Any:
        """Return peak positions and properties."""
        return find_peaks(
            self.data,
            height=self.height,
            threshold=self.threshold,
            distance=self.distance,
            prominence=self.prominence,
            width=self.width,
            wlen=self.wlen,
            rel_height=self.rel_height,
            plateau_size=self.plateau_size,
        )


class ModelParameters(AutoPeakDetection):
    """Class to define the model parameters."""

    def __init__(self, df: pd.DataFrame, args: Dict[str, Any]) -> None:
        """Initialize the model parameters.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str, Any]):
                 Nested arguments dictionary for the model based on **one** or **two**
                 `int` keys depending if global fitting parameters, will explicit
                 defined or not.

        !!! note "About `args` for models"

            The `args` dictionary is used to define the model parameters. And the total
            nested dictionary structure is as follows:

            ```python
            args: Dict[str, Dict[int, Dict[str, Dict[str, Union[str, int, float]]]]]
            ```

        !!! info "About the fitting options"

            In general, there are two option for the fitting possible:

            1. `Classic fitting` or `local fitting`, where the parameters are defined
                for a 2D spectrum.
            2. `Global fitting`, where the parameters are defined for a 3D spectrum.
                Here, the parameters can be automatically defined for each column on the
                basis of the initial parameters or they can be completley defined by the
                user. The `global fitting` definition starts at `1` similiar to the
                peaks attributes notation.
        """
        self.col_len = df.shape[1] - 1
        self.args = args
        self.params = Parameters()
        self.x, self.data = self.df_to_numvalues(df=df, args=args)

        super().__init__(self.x, self.data, self.args)

    def df_to_numvalues(
        self, df: pd.DataFrame, args: Dict[str, Any]
    ) -> Tuple[NDArray[np.float64], NDArray[np.float64]]:
        """Transform the dataframe to numeric values of `x` and `data`.

        !!! note "About the dataframe to numeric values"

            The transformation is done by the `value` property of pandas. The dataframe
            is separated into the `x` and `data` columns and the `x` column is
            transformed to the energy values and the `data` column is transformed to
            the intensity values depending on the `args` dictionary. In terms of global
            fitting, the `data` contains the intensity values for each column.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.

        Returns:
            Tuple[NDArray[np.float64], NDArray[np.float64]]: Tuple of `x` and
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
        """Perform the model parameter definition.

        Raises:
            KeyError: Global fitting is combination with automatic peak detection is
                 not implemented yet.
        """
        if self.args["global_"] == 0 and not self.args["autopeak"]:
            self.define_parameters()
        elif self.args["global_"] == 1 and not self.args["autopeak"]:
            self.define_parameters_global()
        elif self.args["global_"] == 2 and not self.args["autopeak"]:
            self.define_parameters_global_pre()
        elif self.args["global_"] == 0:
            self.initialize_peak_detection()
            self.define_parameters_auto()
        elif self.args["global_"] in [1, 2]:
            raise KeyError(
                "Global fitting mode with automatic peak detection "
                "is not supported yet."
            )

    def define_parameters_auto(self) -> None:
        """Auto define the model parameters for local fitting."""
        positions, properties = self.__autodetect__()
        if (
            not isinstance(self.args["autopeak"], bool)
            and "model_type" in self.args["autopeak"]
        ):
            _model = self.args["autopeak"]["model_type"].lower()
            ReferenceKeys().automodel_check(model=_model)
            models = _model
        else:
            models = "gaussian"

        if models == "gaussian":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhmg_{i}",
                    value=_fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )
        elif models == "lorentzian":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhml_{i}",
                    value=_fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )
        elif models == "voigt":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhmv_{i}",
                    value=_fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )
        elif models == "pseudovoigt":
            for i, (_cent, _amp, _fhmw) in enumerate(
                zip(
                    self.x[positions],
                    properties["peak_heights"],
                    properties["widths"],
                ),
                start=1,
            ):
                self.params.add(
                    f"{models}_amplitude_{i}",
                    value=_amp,
                    min=-np.abs(1.25 * _amp),
                    max=np.abs(1.25 * _amp),
                    vary=True,
                )
                self.params.add(
                    f"{models}_center_{i}",
                    value=_cent,
                    min=0.5 * _cent,
                    max=2 * _cent,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhmg_{i}",
                    value=0.5 * _fhmw,
                    min=0,
                    max=_fhmw,
                    vary=True,
                )
                self.params.add(
                    f"{models}_fwhml_{i}",
                    value=0.5 * _fhmw,
                    min=0,
                    max=2 * _fhmw,
                    vary=True,
                )

        self.args["auto_generated_models"] = {
            "models": {
                key: {
                    "value": self.params[key].value,
                    "min": self.params[key].min,
                    "max": self.params[key].max,
                    "vary": self.params[key].vary,
                }
                for key in self.params
            },
            "positions": positions.tolist(),
            "properties": {key: value.tolist() for key, value in properties.items()},
        }

    def define_parameters(self) -> None:
        """Define the input parameters for a `params`-dictionary for classic fitting."""
        for key_1, value_1 in self.args["peaks"].items():
            for key_2, value_2 in value_1.items():
                for key_3, value_3 in value_2.items():
                    self.params.add(f"{key_2}_{key_3}_{key_1}", **value_3)

    def define_parameters_global(self) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting."""
        for col_i in range(self.col_len):
            for key_1, value_1 in self.args["peaks"].items():
                for key_2, value_2 in value_1.items():
                    for key_3, value_3 in value_2.items():
                        if col_i:
                            if key_3 != "amplitude":
                                self.params.add(
                                    f"{key_2}_{key_3}_{key_1}_{col_i+1}",
                                    expr=f"{key_2}_{key_3}_{key_1}_1",
                                )
                            else:
                                self.params.add(
                                    f"{key_2}_{key_3}_{key_1}_{col_i+1}",
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


class SolverModels(ModelParameters):
    """Solving models for 2D and 3D data sets.

    !!! hint "Solver Modes"
        * `"2D"`: Solve 2D models via the classic `lmfit` function.
        * `"3D"`: Solve 3D models via global git. For the `global-fitting` procedure,
             the `lmfit` function is used to solve the models with an extended set of
             parameters.
          the `lmfit` function is used.
    """

    def __init__(self, df: pd.DataFrame, args: Dict[str, Any]) -> None:
        """Initialize the solver modes.

        Args:
            df (pd.DataFrame): DataFrame containing the input data (`x` and `data`).
            args (Dict[str, Any]): The input file arguments as a dictionary with
                 additional information beyond the command line arguments.
        """
        super().__init__(df=df, args=args)
        self.args_solver = SolverModelsAPI(**args).dict()
        self.args_global = GlobalFittingAPI(**args).dict()
        self.params = self.return_params

    def __call__(self) -> Tuple[Minimizer, Any]:
        """Solve the fitting model.

        Returns:
            Tuple[Minimizer, Any]: Minimizer class and the fitting results.
        """
        if self.args_global["global_"]:
            minimizer = Minimizer(
                self.solve_global_fitting,
                params=self.params,
                fcn_args=(self.x, self.data),
                **self.args["minimizer"],
            )
        else:
            minimizer = Minimizer(
                self.solve_local_fitting,
                params=self.params,
                fcn_args=(self.x, self.data),
                **self.args_solver["minimizer"],
            )

        return (minimizer, minimizer.minimize(**self.args_solver["optimizer"]))

    @staticmethod
    def solve_local_fitting(
        params: Dict[str, Parameters],
        x: NDArray[np.float64],
        data: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        r"""Solving the fitting problem.

        Args:
            params (Dict[str, Parameters): The best-fit parameters resulting
                 from the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 1d-array.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.

        !!! note "About implemented models"
            `solve_local_fitting` is a wrapper function for the calling the implemented
            moldels. Based on the `params` dictionary, the function calls the
            corresponding models and merge them to the general model with will be
            optimized by the `lmfit`-optimizer.
            Currently the following models are supported:

            - [Gaussian](https://en.wikipedia.org/wiki/Gaussian_function)
            - [Lorentzian](https://en.wikipedia.org/wiki/Cauchy_distribution)
                also known as Cauchy distribution
            - [Voigt](https://en.wikipedia.org/wiki/Voigt_profile)
            - [Pseudo Voigt][1]
            - Exponential
            - [power][2] (also known as Log-parabola or just power)
            - Linear
            - Constant
            - [Error Function](https://en.wikipedia.org/wiki/Error_function)
            - [Arcus Tangens][3]
            - Logarithmic

            [1]: https://en.wikipedia.org/wiki/Voigt_profile#Pseudo-Voigt_approximation
            [2]: https://en.wikipedia.org/wiki/Power_law
            [3]: https://en.wikipedia.org/wiki/Inverse_trigonometric_functions
        """
        val = np.zeros(x.shape)
        peak_kwargs: Dict[Tuple[str, str], Parameters] = defaultdict(dict)

        for model in params:
            model = model.lower()
            ReferenceKeys().model_check(model=model)
            c_name = model.split("_")
            peak_kwargs[(c_name[0], c_name[2])][c_name[1]] = params[model]

        for key, _kwarg in peak_kwargs.items():
            if key[0] == "gaussian":
                val += gaussian(x, **_kwarg)
            elif key[0] == "lorentzian":
                val += lorentzian(x, **_kwarg)
            elif key[0] == "voigt":
                val += voigt(x, **_kwarg)
            elif key[0] == "pseudovoigt":
                val += pseudovoigt(x, **_kwarg)
            elif key[0] == "exponential":
                val += exponential(x, **_kwarg)
            elif key[0] == "power":
                val += power(x, **_kwarg)
            elif key[0] == "linear":
                val += linear(x, **_kwarg)
            elif key[0] == "constant":
                val += constant(x, **_kwarg)
            elif key[0] == "erf":
                val += step(x, kind="erf", **_kwarg)
            elif key[0] == "atan":
                val += step(x, kind="atan", **_kwarg)
            elif key[0] == "log":
                val += step(x, kind="log", **_kwarg)
            elif key[0] == "heaviside":
                val += step(x, kind="heaviside", **_kwarg)
        return val - data

    @staticmethod
    def solve_global_fitting(
        params: Dict[str, Parameters],
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
            params (Dict[str, Parameters): The best-fit parameters resulting
                 from the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 2D-array.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.
        """
        val = np.zeros(data.shape)
        peak_kwargs: Dict[Tuple[str, str, str], Parameters] = defaultdict(dict)

        for model in params:

            model = model.lower()
            ReferenceKeys().model_check(model=model)
            c_name = model.split("_")
            peak_kwargs[(c_name[0], c_name[2], c_name[3])][c_name[1]] = params[model]
        for key, _kwarg in peak_kwargs.items():
            i = int(key[2]) - 1
            if key[0] == "gaussian":
                val[:, i] += gaussian(x, **_kwarg)
            elif key[0] == "lorentzian":
                val[:, i] += lorentzian(x, **_kwarg)
            elif key[0] == "voigt":
                val[:, i] += voigt(x, **_kwarg)
            elif key[0] == "pseudovoigt":
                val[:, i] += pseudovoigt(x, **_kwarg)
            elif key[0] == "exponential":
                val[:, i] += exponential(x, **_kwarg)
            elif key[0] == "power":
                val[:, i] += power(x, **_kwarg)
            elif key[0] == "linear":
                val[:, i] += linear(x, **_kwarg)
            elif key[0] == "constant":
                val[:, i] += constant(x, **_kwarg)
            elif key[0] == "erf":
                val[:, i] += step(x, kind="erf", **_kwarg)
            elif key[0] == "atan":
                val[:, i] += step(x, kind="atan", **_kwarg)
            elif key[0] == "log":
                val[:, i] += step(x, kind="log", **_kwarg)
            elif key[0] == "heaviside":
                val[:, i] += step(x, kind="heaviside", **_kwarg)

        val -= data
        return val.flatten()


def calculated_model(
    params: Dict[str, Parameters],
    x: NDArray[np.float64],
    df: pd.DataFrame,
    global_fit: int,
) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

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

    !!! note "About calculated models"
        `calculated_model` are also wrapper functions similar to `solve_model`. The
        overall goal is to extract from the best parameters the single contributions in
        the model. Currently, `lmfit` provides only a single model, so the best-fit.
    """
    peak_kwargs: Dict[Any, Parameters] = defaultdict(dict)

    for model in params:
        model = model.lower()
        ReferenceKeys().model_check(model=model)
        p_name = model.split("_")
        if global_fit:
            peak_kwargs[(p_name[0], p_name[2], p_name[3])][p_name[1]] = params[model]
        else:
            peak_kwargs[(p_name[0], p_name[2])][p_name[1]] = params[model]

    _df = df.copy()
    for key, _kwarg in peak_kwargs.items():
        c_name = f"{key[0]}_{key[1]}_{key[2]}" if global_fit else f"{key[0]}_{key[1]}"
        if key[0] == "gaussian":
            _df[c_name] = gaussian(x, **_kwarg)
        elif key[0] == "lorentzian":
            _df[c_name] = lorentzian(x, **_kwarg)
        elif key[0] == "voigt":
            _df[c_name] = voigt(x, **_kwarg)
        elif key[0] == "pseudovoigt":
            _df[c_name] = pseudovoigt(x, **_kwarg)
        elif key[0] == "exponential":
            _df[c_name] = exponential(x, **_kwarg)
        elif key[0] == "power":
            _df[c_name] = power(x, **_kwarg)
        elif key[0] == "linear":
            _df[c_name] = linear(x, **_kwarg)
        elif key[0] == "constant":
            _df[c_name] = constant(x, **_kwarg)
        elif key[0] == "erf":
            _df[c_name] = step(x, kind="erf", **_kwarg)
        elif key[0] == "atan":
            _df[c_name] = step(x, kind="atan", **_kwarg)
        elif key[0] == "log":
            _df[c_name] = step(x, kind="log", **_kwarg)
        elif key[0] == "heaviside":
            _df[c_name] = step(x, kind="heaviside", **_kwarg)
    return _df


def gaussian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Gaussian distribution.

    $$
    {\displaystyle g(x)={\frac {1}{\sigma {\sqrt {2\pi }}}}\exp
    (  -{\frac {1}{2}}{\frac {(x-\mu )^{2}}{\sigma ^{2}}} ) }
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Gaussian distribution. Defaults
             to 1.0.
        center (float, optional): Center of the Gaussian distribution. Defaults to 0.0.
        fwhmg (float, optional): Full width at half maximum (FWHM) of the Gaussian
             distribution. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Gaussian distribution of `x` given.
    """
    sigma = fwhmg / Constants.sig2fwhm
    return np.array(amplitude / (Constants.sq2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma**2)
    )


def lorentzian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhml: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Lorentzian distribution.

    $$
    f(x;x_{0},\gamma )={\frac  {1}{\pi \gamma [ 1+ ( {\frac  {x-x_{0}}{\gamma }})^{2} ]
    }} ={1 \over \pi \gamma } [ {\gamma ^{2} \over (x-x_{0})^{2}+\gamma ^{2}} ]
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Lorentzian distribution. Defaults
             to 1.0.
        center (float, optional): Center of the Lorentzian distribution. Defaults to
             0.0.
        fwhml (float, optional): Full width at half maximum (FWHM) of the Lorentzian
             distribution. Defaults to 1.0.

    Returns:
        Union[NDArray[np.float64], float]: Lorentzian distribution of `x` given.
    """
    sigma = fwhml / 2.0
    return np.array(amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (
        np.pi * sigma
    )


def voigt(
    x: NDArray[np.float64],
    center: float = 0.0,
    fwhmv: float = 1.0,
    gamma: Optional[float] = None,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Voigt distribution.

    $$
    {\displaystyle V(x;\sigma ,\gamma )\equiv \int _{-\infty }^{\infty }G(x';\sigma )
    L(x-x';\gamma )\,dx'}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        center (float, optional): Center of the Voigt distribution. Defaults to 0.0.
        fwhmv (float, optional): Full width at half maximum (FWHM) of the Lorentzian
             distribution. Defaults to 1.0.
        gamma (float, optional): Scaling factor of the complex part of the
             [Faddeeva Function](https://en.wikipedia.org/wiki/Faddeeva_function).
             Defaults to None.

    Returns:
        NDArray[np.float64]: Voigt distribution of `x` given.
    """
    sigma = fwhmv / 3.60131
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * Constants.sq2)
    return np.array(wofz(z).real / (sigma * Constants.sq2pi))


def pseudovoigt(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 1.0,
    fwhml: float = 1.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional Pseudo-Voigt distribution.

    !!! note "See also:"

        J. Appl. Cryst. (2000). 33, 1311-1316
        https://doi.org/10.1107/S0021889800010219

    Args:
        x (NDArray[np.float64]):  `x`-values of the data.
        amplitude (float, optional): Amplitude of the Pseudo-Voigt distribution.
             Defaults to 1.0.
        center (float, optional): Center of the Pseudo-Voigt distribution.
             Defaults to 0.0.
        fwhmg (float, optional): Full width half maximum of the Gaussian distribution
            in the Pseudo-Voigt distribution. Defaults to 1.0.
        fwhml (float, optional): Full width half maximum of the Lorentzian distribution
            in the Pseudo-Voigt distribution. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Pseudo-Voigt distribution of `x` given.
    """
    f = np.power(
        fwhmg**5
        + 2.69269 * fwhmg**4 * fwhml
        + 2.42843 * fwhmg**3 * fwhml**2
        + 4.47163 * fwhmg**2 * fwhml**3
        + 0.07842 * fwhmg * fwhml**4
        + fwhml**5,
        0.2,
    )
    n = 1.36603 * (fwhml / f) - 0.47719 * (fwhml / f) ** 2 + 0.11116 * (fwhml / f) ** 3
    return np.array(
        n * lorentzian(x=x, amplitude=amplitude, center=center, fwhml=fwhml)
        + (1 - n) * gaussian(x=x, amplitude=amplitude, center=center, fwhmg=fwhmg)
    )


def exponential(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    decay: float = 1.0,
    intercept: float = 0.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional exponential decay.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the exponential function. Defaults to
             1.0.
        decay (float, optional): Decay of the exponential function. Defaults to 1.0.
        intercept (float, optional): Intercept of the exponential function. Defaults to
             0.0.

    Returns:
        NDArray[np.float64]: Exponential decay of `x` given.
    """
    return np.array(amplitude * np.exp(-x / decay) + intercept)


def power(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    exponent: float = 1.0,
    intercept: float = 0.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional power function.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the power function. Defaults to
             1.0.
        exponent (float, optional): Exponent of the power function. Defaults to 1.0.
        intercept (float, optional): Intercept of the power function. Defaults to
             0.0.

    Returns:
        NDArray[np.float64]: power function of `x` given.
    """
    return np.array(amplitude * np.power(x, exponent) + intercept)


def linear(
    x: NDArray[np.float64],
    slope: float = 1.0,
    intercept: float = 0.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional linear function.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        slope (float, optional): Slope of the linear function. Defaults to 1.0.
        intercept (float, optional): Intercept of the linear function. Defaults to 0.0.

    Returns:
        NDArray[np.float64]: Linear function of `x` given.
    """
    return np.array(slope * x + intercept)


def constant(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional constant value.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the constant. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Constant value of `x` given.
    """
    return np.array(np.linspace(amplitude, amplitude, len(x)))


def step(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    kind: str = "linear",
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional step function.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the step function. Defaults to 1.0.
        center (float, optional): Center of the step function. Defaults to 0.0.
        sigma (float, optional): Sigma of the step function. Defaults to 1.0.
        kind (str, optional): Kind of the step function; can be 'heaviside',
             'atan' or 'arctan', 'log' or 'logarithmic', 'erf'. Defaults to "heaviside".

    Returns:
        NDArray[np.float64]: Step function of `x` given.


    !!! note "Available step functions"
        ```python
        step_linear = amplitude * min(1, max(0, arg))
        step_atan = amplitude * (0.5 + atan(arg) / pi)
        step_erf = amplitude * (1 + erf(arg)) / 2.0
        step_log = amplitude * [1 - 1 / (1 + exp(arg))]
        # where arg = (x - center)/sigma
        ```
    """
    if abs(sigma) < 1.0e-13:
        sigma = 1.0e-13

    out: NDArray[np.float64] = np.subtract(x, center) / sigma
    if kind == "erf":
        out = 0.5 * (1 + erf(out))
    elif kind.startswith("log"):
        out = 1.0 - 1.0 / (1.0 + np.exp(out))
    elif kind in {"atan", "arctan"}:
        out = 0.5 + np.arctan(out) / np.pi
    elif kind == "heaviside":
        out[np.where(out < 0)] = 0.0
        out[np.where(out > 1)] = 1.0
    return np.array(amplitude * out)

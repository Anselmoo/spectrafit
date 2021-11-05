"""Minimization models for curve fitting."""
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from typing import Dict
from typing import Tuple

import numpy as np
import pandas as pd

from lmfit import Minimizer
from lmfit import Parameters
from numpy.typing import NDArray
from scipy.special import erf
from scipy.special import wofz


__implemented_models__ = [
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


class ModelParameters:
    """Class to define the model parameters."""

    def __init__(self, df: pd.DataFrame, args: Dict[str, Any]) -> None:
        """Initialize the model parameters.

        Args:
            df (pd.DataFrame): DataFrame with the data.
            args (Dict[str, Any]):
                 Nested arguments dictionary for the model based on **one** or **two**
                 `int` keys depending if global fitting parameters, will explicit
                 defined or not.
            params (Parameters): Parameters for the model.

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
        self.df = df
        self.col_len = df.shape[1] - 1
        self.args = args
        self.params = Parameters()

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
        if self.args["global"] == 1:
            self.define_parameters_global()
        elif self.args["global"] == 2:
            self.define_parameters_global_pre()
        else:
            self.define_parameters()

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
            df (pd.DataFrame): 2D or 3D data set as pandas DataFrame.
            args (Dict[str, Any]): [description]
        """
        super().__init__(df, args)
        self.args = args
        self.params = self.return_params
        self.x = df[self.args["column"][0]].values
        if self.args["global"]:
            self.data = df.loc[:, df.columns != self.args["column"][0]].values
        else:
            self.data = df[self.args["column"][1]].values

    def __call__(self) -> Tuple[Minimizer, Any]:
        """Solve the fitting model.

        Returns:
            Tuple[Minimizer, Any]: Minimizer class and the fitting results.
        """
        if self.args["global"]:
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
                **self.args["minimizer"],
            )

        return (minimizer, minimizer.minimize(**self.args["optimizer"]))

    @staticmethod
    def solve_local_fitting(
        params: Dict[str, Parameters],
        x: NDArray[np.float64],
        data: NDArray[np.float64],
    ) -> NDArray[np.float64]:
        r"""Solving the fitting problem.

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


        Args:
            params (Dict[str, Parameters): The best-fit parameters resulting
                 from the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 1d-array.

        Raises:
            SystemExit: If the model is not supported.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.
        """
        val = np.zeros(x.shape)
        peak_kwargs: dict = defaultdict(dict)

        for model in params:
            model = model.lower()
            if model.split("_")[0] not in __implemented_models__:
                raise SystemExit(f"{model} is not supported")
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

        Raises:
            SystemExit: If the model is not supported.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.
        """
        val = np.zeros(data.shape)
        peak_kwargs: dict = defaultdict(dict)

        for model in params:

            model = model.lower()
            if model.split("_")[0] not in __implemented_models__:
                raise SystemExit(f"{model} is not supported")
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
    params: dict, x: NDArray[np.float64], df: pd.DataFrame, global_fit: int
) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

    !!! note "About calculated models"
        `calculated_model` are also wrapper functions similar to `solve_model`. The
        overall goal is to extract from the best parameters the single contributions in
        the model. Currently, `lmfit` provides only a single model, so the best-fit.

    Args:
        params (dict): The best optimized parameters of the fit.
        x (NDArray[np.float64]): `x`-values of the data.
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.
        global_fit (int): If 1 or 2, the model is calculated for the global fit.

    Raises:
        SystemExit: If the model is not supported.

    Returns:
        pd.DataFrame: Extended dataframe containing the single contributions of the
            models.
    """
    peak_kwargs: dict = defaultdict(dict)

    for model in params:
        model = model.lower()
        if model.split("_")[0] not in __implemented_models__:
            raise SystemExit(f"{model} is not supported")
        c_name = model.split("_")
        if global_fit:
            peak_kwargs[(c_name[0], c_name[2], c_name[3])][c_name[1]] = params[model]
        else:
            peak_kwargs[(c_name[0], c_name[2])][c_name[1]] = params[model]

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
    return (amplitude / (Constants.sq2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma ** 2)
    )


def lorentzian(
    x, amplitude: float = 1.0, center: float = 0.0, fwhml: float = 1.0
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
        NDArray[np.float64]: Lorentzian distribution of `x` given.
    """
    sigma = fwhml / 2.0
    return (amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (np.pi * sigma)


def voigt(
    x: NDArray[np.float64], center: float = 0.0, fwhmv: float = 1.0, gamma: float = None
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Voigt distribution.

    $$
    {\displaystyle V(x;\sigma ,\gamma )\equiv \int _{-\infty }^{\infty }G(x';\sigma )
    L(x-x';\gamma )\,dx'}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Voigt distribution. Defaults to
             1.0.
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
    return wofz(z).real / (sigma * Constants.sq2pi)


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
        fwhmg ** 5
        + 2.69269 * fwhmg ** 4 * fwhml
        + 2.42843 * fwhmg ** 3 * fwhml ** 2
        + 4.47163 * fwhmg ** 2 * fwhml ** 3
        + 0.07842 * fwhmg * fwhml ** 4
        + fwhml ** 5,
        0.25,
    )
    # print(center, fwhmg, fwhml, f)
    n = 1.36603 * (fwhml / f) - 0.47719 * (fwhml / f) ** 2 + 0.11116 * (fwhml / f) ** 3
    return n * lorentzian(x, amplitude, center, fwhml) + (1 - n) * gaussian(
        x, amplitude, center, fwhmg
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
    return amplitude * np.exp(-x / decay) + intercept


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
    return amplitude * np.power(x, exponent) + intercept


def linear(
    x: NDArray[np.float64], slope: float = 1.0, intercept: float = 0.0
) -> NDArray[np.float64]:
    """Return a 1-dimensional linear function.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        slope (float, optional): Slope of the linear function. Defaults to 1.0.
        intercept (float, optional): Intercept of the linear function. Defaults to 0.0.

    Returns:
        NDArray[np.float64]: Linear function of `x` given.
    """
    return slope * x + intercept


def constant(x: NDArray[np.float64], amplitude: float = 1.0) -> NDArray[np.float64]:
    """Return a 1-dimensional constant value.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the constant. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Constant value of `x` given.
    """
    return np.linspace(amplitude, amplitude, len(x))


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

    out = (x - center) / sigma
    if kind == "erf":
        out = 0.5 * (1 + erf(out))
    elif kind.startswith("log"):
        out = 1.0 - 1.0 / (1.0 + np.exp(out))
    elif kind in {"atan", "arctan"}:
        out = 0.5 + np.arctan(out) / np.pi
    elif kind == "heaviside":
        out[np.where(out < 0)] = 0.0
        out[np.where(out > 1)] = 1.0
    return amplitude * out

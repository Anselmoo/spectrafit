"""Minimization models for curve fitting."""
from collections import defaultdict
from dataclasses import dataclass

import numpy as np
import pandas as pd

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


def solver_model(params: dict, x: np.array, data: np.array) -> np.array:
    r"""Solving the fitting problem.

    !!! note "About implemented models"
        `solver_model` is a wrapper function for the calling the implemented moldels.
        Based on the `params` dictionary, the function calls the corresponding models
        and merge them to the general model with will be optimized by the
        `lmfit`-optimizer.
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
        - [Arcus Tangens](https://en.wikipedia.org/wiki/Inverse_trigonometric_functions)
        - Logarithmic

        [1]: https://en.wikipedia.org/wiki/Voigt_profile#Pseudo-Voigt_approximation
        [2]: https://en.wikipedia.org/wiki/Power_law


    Args:
        params (dict): The best-fit parameters resulting from the fit.
        x (np.array): `x`-values of the data.
        data (np.array): `y`-values of the data, the data.

    Raises:
        SystemExit: If the model is not supported.

    Returns:
        np.array: The best-fitted data based on the proposed model.


    """
    val = 0.0
    peak_kwargs: dict = defaultdict(dict)

    for model in params:
        model = model.lower()
        if model.split("_")[0] not in __implemented_models__:
            raise SystemExit(f"{model} is not supported")
        peak_kwargs[(model.split("_")[-1], model.split("_")[0])][
            model.split("_")[1]
        ] = params[model]

    for key, _kwarg in peak_kwargs.items():
        if key[1] == "gaussian":
            val += gaussian(x, **_kwarg)
        elif key[1] == "lorentzian":
            val += lorentzian(x, **_kwarg)
        elif key[1] == "voigt":
            val += voigt(x, **_kwarg)
        elif key[1] == "pseudovoigt":
            val += pseudovoigt(x, **_kwarg)
        elif key[1] == "exponential":
            val += exponential(x, **_kwarg)
        elif key[1] == "power":
            val += power(x, **_kwarg)
        elif key[1] == "linear":
            val += linear(x, **_kwarg)
        elif key[1] == "constant":
            val += constant(x, **_kwarg)
        elif key[1] == "erf":
            val += step(x, kind="erf", **_kwarg)
        elif key[1] == "atan":
            val += step(x, kind="atan", **_kwarg)
        elif key[1] == "log":
            val += step(x, kind="log", **_kwarg)
        elif key[1] == "heaviside":
            val += step(x, kind="heaviside", **_kwarg)
    return val - data


def calculated_model(params: dict, x: np.array, df: pd.DataFrame) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

    !!! note "About calculated models"
        `calculated_model` are also wrapper functions similar to `solve_model`. The
         overall goal is to extract from the best parameters the single contributions in
         the model. Currently, `lmfit` provides only a single model, so the best-fit.

    Args:
        params (dict): The best optimized parameters of the fit.
        x (np.array): `x`-values of the data.
        df (pd.DataFrame): DataFrame containing the input data (`x` and `data`),
             as well as the best fit and the corresponding residuum. Hence, it will be
             extended by the single contribution of the model.

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
        peak_kwargs[(model.split("_")[-1], model.split("_")[0])][
            model.split("_")[1]
        ] = params[model]

    for key, _kwarg in peak_kwargs.items():
        if key[1] == "gaussian":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = gaussian(x, **_kwarg)
        elif key[1] == "lorentzian":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = lorentzian(
                x, **_kwarg
            )
        elif key[1] == "voigt":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = voigt(x, **_kwarg)
        elif key[1] == "pseudovoigt":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = pseudovoigt(
                x, **_kwarg
            )
        elif key[1] == "exponential":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = exponential(
                x, **_kwarg
            )
        elif key[1] == "power":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = power(x, **_kwarg)
        elif key[1] == "linear":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = linear(x, **_kwarg)
        elif key[1] == "constant":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = constant(x, **_kwarg)
        elif key[1] == "erf":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                x, kind="erf", **_kwarg
            )
        elif key[1] == "atan":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                x, kind="atan", **_kwarg
            )
        elif key[1] == "log":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                x, kind="log", **_kwarg
            )
        elif key[1] == "heaviside":
            df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                x, kind="heaviside", **_kwarg
            )
    return df


def gaussian(
    x: np.array, amplitude: float = 1.0, center: float = 0.0, fwhmg: float = 1.0
) -> np.array:
    r"""Return a 1-dimensional Gaussian distribution.

    $$
    {\displaystyle g(x)={\frac {1}{\sigma {\sqrt {2\pi }}}}\exp
    (  -{\frac {1}{2}}{\frac {(x-\mu )^{2}}{\sigma ^{2}}} ) }
    $$

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Gaussian distribution. Defaults
             to 1.0.
        center (float, optional): Center of the Gaussian distribution. Defaults to 0.0.
        fwhmg (float, optional): Full width at half maximum (FWHM) of the Gaussian
             distribution. Defaults to 1.0.

    Returns:
        np.array: Gaussian distribution of `x` given.
    """
    sigma = fwhmg / Constants.sig2fwhm
    return (amplitude / (Constants.sq2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma ** 2)
    )


def lorentzian(
    x, amplitude: float = 1.0, center: float = 0.0, fwhml: float = 1.0
) -> np.array:
    r"""Return a 1-dimensional Lorentzian distribution.

    $$
    f(x;x_{0},\gamma )={\frac  {1}{\pi \gamma [ 1+ ( {\frac  {x-x_{0}}{\gamma }})^{2} ]
    }} ={1 \over \pi \gamma } [ {\gamma ^{2} \over (x-x_{0})^{2}+\gamma ^{2}} ]
    $$

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Lorentzian distribution. Defaults
             to 1.0.
        center (float, optional): Center of the Lorentzian distribution. Defaults to
             0.0.
        fwhml (float, optional): Full width at half maximum (FWHM) of the Lorentzian
             distribution. Defaults to 1.0.

    Returns:
        np.array: Lorentzian distribution of `x` given.
    """
    sigma = fwhml / 2.0
    return (amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (np.pi * sigma)


def voigt(
    x: np.array, center: float = 0.0, fwhmv: float = 1.0, gamma: float = None
) -> np.array:
    r"""Return a 1-dimensional Voigt distribution.

    $$
    {\displaystyle V(x;\sigma ,\gamma )\equiv \int _{-\infty }^{\infty }G(x';\sigma )
    L(x-x';\gamma )\,dx'}
    $$

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Voigt distribution. Defaults to
             1.0.
        center (float, optional): Center of the Voigt distribution. Defaults to 0.0.
        fwhmv (float, optional): Full width at half maximum (FWHM) of the Lorentzian
             distribution. Defaults to 1.0.
        gamma (float, optional): Scaling factor of the complex part of the
             [Faddeeva Function](https://en.wikipedia.org/wiki/Faddeeva_function).
             Defaults to None.

    Returns:
        np.array: Voigt distribution of `x` given.
    """
    sigma = fwhmv / 3.60131
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * Constants.sq2)
    return wofz(z).real / (sigma * Constants.sq2pi)


def pseudovoigt(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 1.0,
    fwhml: float = 1.0,
) -> np.array:
    """Return a 1-dimensional Pseudo-Voigt distribution.

    !!! note "See also:"

        J. Appl. Cryst. (2000). 33, 1311-1316
        https://doi.org/10.1107/S0021889800010219

    Args:
        x (np.array):  `x`-values of the data.
        amplitude (float, optional): Amplitude of the Pseudo-Voigt distribution.
             Defaults to 1.0.
        center (float, optional): Center of the Pseudo-Voigt distribution.
             Defaults to 0.0.
        fwhmg (float, optional): Full width half maximum of the Gaussian distribution
            in the Pseudo-Voigt distribution. Defaults to 1.0.
        fwhml (float, optional): Full width half maximum of the Lorentzian distribution
            in the Pseudo-Voigt distribution. Defaults to 1.0.

    Returns:
        np.array: Pseudo-Voigt distribution of `x` given.
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
    n = 1.36603 * (fwhml / f) - 0.47719 * (fwhml / f) ** 2 + 0.11116 * (fwhml / f) ** 3
    return n * lorentzian(x, amplitude, center, fwhml) + (1 - n) * gaussian(
        x, amplitude, center, fwhmg
    )


def exponential(
    x: np.array, amplitude: float = 1.0, decay: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return a 1-dimensional exponential decay.

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the exponential function. Defaults to
             1.0.
        decay (float, optional): Decay of the exponential function. Defaults to 1.0.
        intercept (float, optional): Intercept of the exponential function. Defaults to
             0.0.

    Returns:
        np.array: Exponential decay of `x` given.
    """
    return amplitude * np.exp(-x / decay) + intercept


def power(
    x: np.array, amplitude: float = 1.0, exponent: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return a 1-dimensional power function.

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the power function. Defaults to
             1.0.
        exponent (float, optional): Exponent of the power function. Defaults to 1.0.
        intercept (float, optional): Intercept of the power function. Defaults to
             0.0.

    Returns:
        np.array: power function of `x` given.
    """
    return amplitude * np.power(x, exponent) + intercept


def linear(x: np.array, slope: float = 1.0, intercept: float = 0.0) -> np.array:
    """Return a 1-dimensional linear function.

    Args:
        x (np.array): `x`-values of the data.
        slope (float, optional): Slope of the linear function. Defaults to 1.0.
        intercept (float, optional): Intercept of the linear function. Defaults to 0.0.

    Returns:
        np.array: Linear function of `x` given.
    """
    return slope * x + intercept


def constant(x: np.array, amplitude: float = 1.0) -> np.array:
    """Returns a 1-dimensional constant value.

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the constant. Defaults to 1.0.

    Returns:
        np.array: Constant value of `x` given.
    """
    return np.linspace(amplitude, amplitude, len(x))


def step(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    kind: str = "linear",
) -> np.array:
    r"""Returns a 1-dimensional step function.

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the step function. Defaults to 1.0.
        center (float, optional): Cener of the step function. Defaults to 0.0.
        sigma (float, optional): Sigma of the step function. Defaults to 1.0.
        kind (str, optional): Kind of the step function; can be 'heaviside',
             'atan' or 'arctan', 'log' or 'logarithmic', 'erf'. Defaults to "heaviside".

    Returns:
        np.array: Step function of `x` given.


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

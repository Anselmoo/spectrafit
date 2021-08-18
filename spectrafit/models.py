"""Minimization models for curve fitting."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from scipy.special import erf
from scipy.special import wofz


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
        - [Powerlaw][2] (also known as Log-parabola)
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
    for model in params:
        model = model.lower()
        if model.split("_")[0] in [
            "gaussian",
            "lorentzian",
            "voigt",
            "pseudovoigt",
            "exponential",
            "powerlaw",
            "linear",
            "constant",
            "erf",
            "atan",
            "log",
        ]:
            pass
        else:
            raise SystemExit(f"{model} is not supported")
    for model in params:
        model = model.lower()
        if "gaussian" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_g" in model:
                fwhm_g = params[model]
                val += gaussian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_g,
                )
        if "lorentzian" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_l" in model:
                fwhm_l = params[model]
                val += lorentzian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_l,
                )
        if "voigt" in model and "pseudovoigt" not in model:
            if "center" in model:
                center = params[model]
            if "fwhm" in model:
                fwhm = params[model]
            if "gamma" in model:
                gamma = params[model]
                val += voigt(
                    x=x,
                    center=center,
                    fwhm=fwhm,
                    gamma=gamma,
                )
        if "pseudovoigt" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_g" in model:
                fwhm_g = params[model]
            if "fwhm_l" in model:
                fwhm_l = params[model]
                val += pseudovoigt(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm_g=fwhm_g,
                    fwhm_l=fwhm_l,
                )
        if "exponential" in model:
            if "amplitude" in model:
                amplitude = params[model]
            if "decay" in model:
                decay = params[model]
            if "intercept" in model:
                intercept = params[model]
                val += exponential(
                    x=x,
                    amplitude=amplitude,
                    decay=decay,
                    intercept=intercept,
                )
        if "power" in model:
            if "amplitude" in model:
                amplitude = params[model]
            if "exponent" in model:
                exponent = params[model]
            if "intercept" in model:
                intercept = params[model]
                val += powerlaw(
                    x=x,
                    amplitude=amplitude,
                    exponent=exponent,
                    intercept=intercept,
                )
        if "linear" in model:
            if "slope" in model:
                slope = params[model]
            if "intercept" in model:
                intercept = params[model]
                val += linear(x=x, slope=slope, intercept=intercept)
        if "constant" in model and "amplitude" in model:
            if "amplitude" in model:
                amplitude = params[model]
                val += constant(x=x, amplitude=amplitude)
        if "erf" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                val += step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    kind="erf",
                )
        if "atan" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                val += step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    kind="atan",
                )
        if "log" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                val += step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    kind="logistic",
                )
    return val - data


def calculated_models(params: dict, x: np.array, df: pd.DataFrame) -> pd.DataFrame:
    r"""Calculate the single contributions of the models and add them to the dataframe.

    !!! note "About calculated models"
        `calculated_models` are also wrapper functions similar to `solve_model`. The
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
    for model in params:
        model = model.lower()
        if model.split("_")[0] in [
            "gaussian",
            "lorentzian",
            "voigt",
            "pseudovoigt",
            "exponential",
            "powerlaw",
            "linear",
            "constant",
            "erf",
            "atan",
            "log",
        ]:
            pass
        else:
            raise SystemExit(f"{model} is not supported")
    for model in params:
        model = model.lower()
        if "gaussian" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_g" in model:
                fwhm_g = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = gaussian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_g,
                )
        if "lorentzian" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_l" in model:
                fwhm_l = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = lorentzian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_l,
                )
        if "voigt" in model and "pseudovoigt" not in model:
            if "center" in model:
                center = params[model]
            if "fwhm" in model:
                fwhm = params[model]
            if "gamma" in model:
                gamma = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = voigt(
                    x=x,
                    center=center,
                    fwhm=fwhm,
                    gamma=gamma,
                )
        if "pseudovoigt" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_g" in model:
                fwhm_g = params[model]
            if "fwhm_l" in model:
                fwhm_l = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = pseudovoigt(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm_g=fwhm_g,
                    fwhm_l=fwhm_l,
                )
        if "exponential" in model:
            if "amplitude" in model:
                amplitude = params[model]
            if "decay" in model:
                decay = params[model]
            if "intercept" in model:
                intercept = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = exponential(
                    x=x,
                    amplitude=amplitude,
                    decay=decay,
                    intercept=intercept,
                )
        if "power" in model:
            if "amplitude" in model:
                amplitude = params[model]
            if "exponent" in model:
                exponent = params[model]
            if "intercept" in model:
                intercept = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = powerlaw(
                    x=x,
                    amplitude=amplitude,
                    exponent=exponent,
                    intercept=intercept,
                )
        if "linear" in model:
            if "slope" in model:
                slope = params[model]
            if "intercept" in model:
                intercept = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = linear(
                    x=x, slope=slope, intercept=intercept
                )
        if "constant" in model and "amplitude" in model:
            if "amplitude" in model:
                amplitude = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = constant(
                    x=x, amplitude=amplitude
                )
        if "erf" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    kind="erf",
                )
        if "atan" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    kind="atan",
                )
        if "log" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                df[f"{model.split('_')[0]}_{model.split('_')[-1]}"] = step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    kind="logistic",
                )
    return df


def gaussian(
    x: np.array, amplitude: float = 1.0, center: float = 0.0, fwhm: float = 1.0
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
        fwhm (float, optional): Full width at half maximum (FWHM) of the Gaussian
             distribution. Defaults to 1.0.

    Returns:
        np.array: Gaussian distribution of `x` given.
    """
    sigma = fwhm / Constants.sig2fwhm
    return (amplitude / (Constants.sq2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma ** 2)
    )


def lorentzian(
    x, amplitude: float = 1.0, center: float = 0.0, fwhm: float = 1.0
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
        fwhm (float, optional): Full width at half maximum (FWHM) of the Lorentzian
             distribution. Defaults to 1.0.

    Returns:
        np.array: Lorentzian distribution of `x` given.
    """
    sigma = fwhm / 2.0
    return (amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (np.pi * sigma)


def voigt(
    x: np.array, center: float = 0.0, fwhm: float = 1.0, gamma: float = None
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
        fwhm (float, optional): Full width at half maximum (FWHM) of the Lorentzian
             distribution. Defaults to 1.0.
        gamma (float, optional): Scaling factor of the complex part of the
             [Faddeeva Function](https://en.wikipedia.org/wiki/Faddeeva_function).
             Defaults to None.

    Returns:
        np.array: Voigt distribution of `x` given.
    """
    sigma = fwhm / 3.60131
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * Constants.sq2)
    return wofz(z).real / (sigma * Constants.sq2pi)


def pseudovoigt(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhm_g: float = 1.0,
    fwhm_l: float = 1.0,
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
        fwhm_g (float, optional): Full width half maximum of the Gaussian distribution
            in the Pseudo-Voigt distribution. Defaults to 1.0.
        fwhm_l (float, optional): Full width half maximum of the Lorentzian distribution
            in the Pseudo-Voigt distribution. Defaults to 1.0.

    Returns:
        np.array: Pseudo-Voigt distribution of `x` given.
    """
    f = np.power(
        fwhm_g ** 5
        + 2.69269 * fwhm_g ** 4 * fwhm_l
        + 2.42843 * fwhm_g ** 3 * fwhm_l ** 2
        + 4.47163 * fwhm_g ** 2 * fwhm_l ** 3
        + 0.07842 * fwhm_g * fwhm_l ** 4
        + fwhm_l ** 5,
        0.25,
    )
    n = (
        1.36603 * (fwhm_l / f)
        - 0.47719 * (fwhm_l / f) ** 2
        + 0.11116 * (fwhm_l / f) ** 3
    )
    return n * lorentzian(x, amplitude, center, fwhm_l) + (1 - n) * gaussian(
        x, amplitude, center, fwhm_g
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


def powerlaw(
    x: np.array, amplitude: float = 1.0, exponent: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return a 1-dimensional powerlaw function.

    Args:
        x (np.array): `x`-values of the data.
        amplitude (float, optional): Amplitude of the powerlaw function. Defaults to
             1.0.
        exponent (float, optional): Exponent of the powerlaw function. Defaults to 1.0.
        intercept (float, optional): Intercept of the powerlaw function. Defaults to
             0.0.

    Returns:
        np.array: Powerlaw function of `x` given.
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
        kind (str, optional): Kind of the step function; can be 'linear',
             'atan' or 'arctan', 'log' or 'logistic', 'erf'. Defaults to "linear".

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
    else:
        out[np.where(out < 0)] = 0.0
        out[np.where(out > 1)] = 1.0
    return amplitude * out

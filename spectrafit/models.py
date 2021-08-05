from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd

from scipy.special import erf
from scipy.special import wofz


@dataclass(frozen=True)
class Constants:
    log2 = np.log(2.0)
    sq2pi = np.sqrt(2.0 * np.pi)
    sqpi = np.sqrt(np.pi)
    sq2 = np.sqrt(2.0)
    sig2fwhm = 2.0 * np.sqrt(2.0 * np.log(2.0))


def solver_model(params: dict, x: np.array, data) -> np.array:
    """[summary]

    Args:
        params (dict): [description]
        x (np.array): [description]
        data ([type]): [description]

    Returns:
        [type]: [description]
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
            if "fwhm_gaussian" in model:
                fwhm_gaussian = params[model]
                val += gaussian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_gaussian,
                )
        if "lorentzian" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_lorentzian" in model:
                fwhm_lorentzian = params[model]
                val += lorentzian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_lorentzian,
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
            if "fwhm_gaussian" in model:
                fwhm_gaussian = params[model]
            if "fwhm_lorentzian" in model:
                fwhm_lorentzian = params[model]
                val += pseudovoigt(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm_g=fwhm_gaussian,
                    fwhm_l=fwhm_lorentzian,
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
                    form="erf",
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
                    form="atan",
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
                    form="logistic",
                )
    return val - data


def calculated_models(params: dict, x: np.array, df: pd.DataFrame) -> pd.DataFrame:
    """[summary]

    Args:
        params (dict): [description]
        x (np.array): [description]
        data ([type]): [description]

    Returns:
        [type]: [description]
    """
    for model in params:
        model = model.lower()
        if model.split("_")[0] in [
            "gaussian",
            "lorentzian",
            "voigt",
            "pseudovoigt",
            "exponential",
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
            if "fwhm_gaussian" in model:
                fwhm_gaussian = params[model]
                df[model] = gaussian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_gaussian,
                )
        if "lorentzian" in model:
            if "center" in model:
                center = params[model]
            if "amplitude" in model:
                amplitude = params[model]
            if "fwhm_lorentzian" in model:
                fwhm_lorentzian = params[model]
                df[model] = lorentzian(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm=fwhm_lorentzian,
                )
        if "voigt" in model and "pseudovoigt" not in model:
            if "center" in model:
                center = params[model]
            if "fwhm" in model:
                fwhm = params[model]
            if "gamma" in model:
                gamma = params[model]
                df[model] = voigt(
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
            if "fwhm_gaussian" in model:
                fwhm_gaussian = params[model]
            if "fwhm_lorentzian" in model:
                fwhm_lorentzian = params[model]
                df[model] = pseudovoigt(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    fwhm_g=fwhm_gaussian,
                    fwhm_l=fwhm_lorentzian,
                )
        if "exponential" in model:
            if "amplitude" in model:
                amplitude = params[model]
            if "decay" in model:
                decay = params[model]
            if "intercept" in model:
                intercept = params[model]
                df[model] = exponential(
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
                df[model] = powerlaw(
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
                df[model] = linear(x=x, slope=slope, intercept=intercept)
        if "constant" in model and "amplitude" in model:
            if "amplitude" in model:
                amplitude = params[model]
                df[model] = constant(x=x, amplitude=amplitude)
        if "erf" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                df[model] = step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    form="erf",
                )
        if "atan" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                df[model] = step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    form="atan",
                )
        if "log" in model:
            if "center" in model:
                center = params[model]
            if "sigma" in model:
                sigma = params[model]
            if "amplitude" in model:
                amplitude = params[model]
                df[model] = step(
                    x=x,
                    amplitude=amplitude,
                    center=center,
                    sigma=sigma,
                    form="logistic",
                )
    return df


def pv_cof(fwhm_g: float, fwhm_l: float) -> Tuple[float, float]:
    """
    Calculating the effectiv fwhm of the pseudo voigt profile and the fraction coefficient for n
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
    return (f, n)


def gaussian(
    x: np.array, amplitude: float = 1.0, center: float = 0.0, fwhm: float = 1.0
) -> np.array:
    """Return a 1-dimensional Gaussian function.

    gaussian(x, amplitude, center, sigma) =
        (amplitude/(sq2pi*sigma)) * exp(-(1.0*x-center)**2 / (2*sigma**2))

    """
    sigma = fwhm / Constants.sig2fwhm
    return (amplitude / (Constants.sq2pi * sigma)) * np.exp(
        -((1.0 * x - center) ** 2) / (2 * sigma ** 2)
    )


def lorentzian(
    x, amplitude: float = 1.0, center: float = 0.0, fwhm: float = 1.0
) -> np.array:
    """Return a 1-dimensional Lorentzian function.

    lorentzian(x, amplitude, center, sigma) =
        (amplitude/(1 + ((1.0*x-center)/sigma)**2)) / (pi*sigma)

    """
    sigma = fwhm / 2.0
    return (amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (np.pi * sigma)


def voigt(
    x: np.array, center: float = 0.0, fwhm: float = 1.0, gamma: float = None
) -> np.array:
    """Return a 1-dimensional Voigt function.

    voigt(x, amplitude, center, sigma, gamma) =
        amplitude*wofz(z).real / (sigma*sq2pi)

    see http://en.wikipedia.org/wiki/Voigt_profile

    """
    sigma = fwhm / 3.60131
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * Constants.s2)
    return wofz(z).real / (sigma * Constants.sq2pi)


# def pseudovoigt(x, amplitude=1.0, center=0.0, sigma=1.0, fraction=0.5):
#    """Return a 1-dimensional pseudo-Voigt function.
#
#    pseudovoigt(x, amplitude, center, sigma, fraction) =
#       amplitude*(1-fraction)*gaussion(x, center, sigma_g) +
#       amplitude*fraction*lorentzian(x, center, sigma)
#
#    where sigma_g (the sigma for the Gaussian component) is
#
#        sigma_g = sigma / sqrt(2*log(2)) ~= sigma / 1.17741
#
#    so that the Gaussian and Lorentzian components have the
#    same FWHM of 2*sigma.
#
#    """
#    sigma_g = sigma / np.sqrt(2*log2)
#    return ((1-fraction)*gaussian(x, amplitude, center, sigma_g) +
#            fraction*lorentzian(x, amplitude, center, sigma))


def pseudovoigt(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhm_g: float = 1.0,
    fwhm_l: float = 1.0,
) -> np.array:

    # PSVOIGT This is a psuedo voigt function
    #   This is programmed according to wikipidia and they cite:
    #   Ida, T and Ando, M and Toraya, H (2000).
    # "Extended pseudo-Voigt function for approximating the Voigt profile".
    # Journal of Applied Crystallography 33 (6): 1311-1316.

    # sigma_g = sigma / np.sqrt(2*log2)
    f, n = pv_cof(fwhm_g, fwhm_l)

    # f = np.power(fwhm_g**5 +2.69269*fwhm_g**4*fwhm_l+2.42843*fwhm_g**3*fwhm_l**2+
    #             4.47163*fwhm_g**2*fwhm_l**3+0.07842*fwhm_g*fwhm_l**4+fwhm_l**5,0.25)
    # n = 1.36603*(fwhm_l/f) - 0.47719*(fwhm_l/f)**2 +0.11116*(fwhm_l/f)**3
    return n * lorentzian(x, amplitude, center, fwhm_l) + (1 - n) * gaussian(
        x, amplitude, center, fwhm_g
    )


def exponential(
    x: np.array, amplitude: float = 1.0, decay: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return an exponential function.

    x -> amplitude * exp(-x/decay)

    """
    return amplitude * np.exp(-x / decay) + intercept


def powerlaw(
    x: np.array, amplitude: float = 1.0, exponent: float = 1.0, intercept: float = 0.0
) -> np.array:
    """Return the powerlaw function.

    x -> amplitude * x**exponent

    """

    return amplitude * np.power(x, exponent) + intercept


def linear(x: np.array, slope: float = 1.0, intercept: float = 0.0) -> np.array:
    """Return a linear function.

    x -> slope * x + intercept

    """
    return slope * x + intercept


def constant(x: np.array, amplitude: float = 1.0) -> np.array:
    """Return a cosntant function.

    x -> constant

    """
    return np.linspace(amplitude, amplitude, len(x))


def step(
    x: np.array,
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    form: str = "linear",
) -> np.array:
    """Return a step function.

    starts at 0.0, ends at amplitude, with half-max at center, and
    rising with form:
      'linear' (default) = amplitude * min(1, max(0, arg))
      'atan', 'arctan'   = amplitude * (0.5 + atan(arg)/pi)
      'erf'              = amplitude * (1 + erf(arg))/2.0
      'logistic'         = amplitude * [1 - 1/(1 + exp(arg))]

    where arg = (x - center)/sigma

    """
    if abs(sigma) < 1.0e-13:
        sigma = 1.0e-13

    out = (x - center) / sigma
    if form == "erf":
        out = 0.5 * (1 + erf(out))
    elif form.startswith("logi"):
        out = 1.0 - 1.0 / (1.0 + np.exp(out))
    elif form in {"atan", "arctan"}:
        out = 0.5 + np.arctan(out) / np.pi
    else:
        out[np.where(out < 0)] = 0.0
        out[np.where(out > 1)] = 1.0
    return amplitude * out

"""Common distribution models for curve fitting.

This module contains mathematical functions for peak and distribution modeling.
All functions take x values and different parameters to return a model calculation.
"""

from __future__ import annotations

from math import log
from math import pi
from math import sqrt
from typing import TYPE_CHECKING

import numpy as np

from scipy.special import erf
from scipy.special import wofz


if TYPE_CHECKING:
    from numpy.typing import NDArray


# Constants used across multiple functions
# Extracted as module-level constants for performance and clarity
LN2 = log(2.0)
MIN_SIGMA = 1.0e-13  # Minimum sigma value to prevent division by zero
SQ2PI = sqrt(2.0 * pi)
SQPI = sqrt(pi)
SQ2 = sqrt(2.0)
FWHMG2SIG = 1 / (2.0 * sqrt(2.0 * log(2.0)))
FWHML2SIG = 1 / 2.0
FWHMV2SIG = 1 / (2 * 0.5346 + 2 * sqrt(0.2166 + log(2) * 2))


def _gaussian_core(
    x: NDArray[np.float64],
    amplitude: float,
    center: float,
    scale: float,
) -> NDArray[np.float64]:
    r"""Core Gaussian calculation used by multiple models.

    !!! note "About the core Gaussian calculation"
        The core Gaussian calculation is used by the `gaussian`, `orca_gaussian`
        for avoiding code duplication. The core Gaussian calculation is not normalized and
        therefore the amplitude of the Gaussian is not directly comparable to the
        amplitude of the classical definition of the
        [Gaussian](https://en.wikipedia.org/wiki/Gaussian_function) function.

        Consequently, the core Gaussian calculation is defined as:

        $$
        {\displaystyle g(x)={A \exp
        (  -{\frac {1}{2}}{\frac {(x-\mu )^{2}}{\sigma ^{2}}} ) }
        $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float): Amplitude of the Gaussian distribution.
        center (float): Center of the Gaussian distribution.
        scale (float): Scale of the Gaussian distribution.

    Returns:
        NDArray[np.float64]: Gaussian distribution of `x` given.
    """
    return np.array(amplitude * np.exp(-((1.0 * x - center) ** 2) / (2 * scale**2)))


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
        amplitude (float, optional): Amplitude of the Gaussian distribution.
             Defaults to 1.0.
        center (float, optional): Center of the Gaussian distribution.
             Defaults to 0.0.
        fwhmg (float, optional): Full width at half maximum (FWHM) of the Gaussian
            distribution. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Gaussian distribution of `x` given.
    """
    sigma = fwhmg * FWHMG2SIG
    norm_factor = amplitude / (SQ2PI * sigma)
    return norm_factor * _gaussian_core(
        x=x,
        amplitude=1.0,
        center=center,
        scale=sigma,
    )


def orcagaussian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    width: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Gaussian distribution as implemented in the ORCA program.

    $$
    {\displaystyle g(x)= A \cdot \exp
    (  -{\frac {(x-x_0)^{2}}{2 \cdot width^{2}}} ) }
    $$

    Unlike the standard gaussian function, this implementation uses the width parameter
    directly without conversion to sigma, which is consistent with the ORCA quantum
    chemistry program's approach[^1].

    [^1]: https://www.faccts.de/docs/orca/6.0/manual/contents/detailed/utilities.html

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Gaussian distribution.
             Defaults to 1.0.
        center (float, optional): Center of the Gaussian distribution.
             Defaults to 0.0.
        width (float, optional): Width parameter of the Gaussian distribution as used
             in the ORCA program. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Gaussian distribution of `x` given.
    """
    return _gaussian_core(
        x=x,
        amplitude=amplitude,
        center=center,
        scale=width,
    )


def lorentzian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhml: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Lorentzian distribution.

    $$
    f(x;x_{0},\gamma )={\frac  {1}{\pi \gamma
    [ 1+ ( {\frac  {x-x_{0}}{\gamma }})^{2} ]
    }} ={1 \over \pi \gamma } [ {\gamma ^{2} \over (x-x_{0})^{2}+\gamma ^{2}} ]
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Lorentzian distribution.
            Defaults to 1.0.
        center (float, optional): Center of the Lorentzian distribution. Defaults to
            0.0.
        fwhml (float, optional): Full width at half maximum (FWHM) of the Lorentzian
            distribution. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Lorentzian distribution of `x` given.
    """
    sigma = fwhml * FWHML2SIG
    return np.array(
        amplitude / (1 + ((1.0 * x - center) / sigma) ** 2) / (pi * sigma),
        dtype=np.float64,
    )


def voigt(
    x: NDArray[np.float64],
    center: float = 0.0,
    fwhmv: float = 1.0,
    gamma: float | None = None,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Voigt distribution.

    $$
    {\displaystyle V(x;\sigma ,\gamma )\equiv
    \int_{-\infty }^{\infty }G(x';\sigma )
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
    sigma = fwhmv * FWHMV2SIG
    if gamma is None:
        gamma = sigma
    z = (x - center + 1j * gamma) / (sigma * SQ2)
    return np.array(wofz(z).real / (sigma * SQ2PI))


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
        fwhmg (float, optional): Full width half maximum of the Gaussian
            distribution in the Pseudo-Voigt distribution. Defaults to 1.0.
        fwhml (float, optional): Full width half maximum of the Lorentzian
            distribution in the Pseudo-Voigt distribution. Defaults to 1.0.

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
        + (1 - n) * gaussian(x=x, amplitude=amplitude, center=center, fwhmg=fwhmg),
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
        amplitude (float, optional): Amplitude of the exponential function.
             Defaults to 1.0.
        decay (float, optional): Decay of the exponential function. Defaults to 1.0.
        intercept (float, optional): Intercept of the exponential function.
             Defaults to 0.0.

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
        intercept (float, optional): Intercept of the linear function.
             Defaults to 0.0.

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


def _norm(
    x: NDArray[np.float64],
    center: float,
    sigma: float,
) -> NDArray[np.float64]:
    """Normalize the data for step functions.

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        center (float): Center of the step function.
        sigma (float): Sigma of the step function.

    Returns:
        NDArray[np.float64]: Normalized data.
    """
    if abs(sigma) < MIN_SIGMA:
        sigma = MIN_SIGMA
    return np.array(np.subtract(x, center) / sigma, dtype=np.float64)


def erf_step(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional error function.

    $$
    f(x) = \frac{2}{\sqrt{\pi}} \int_{0}^{x} e^{-t^2} dt
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the error function.
                Defaults to 1.0.
        center (float, optional): Center of the error function. Defaults to 0.0.
        sigma (float, optional): Sigma of the error function. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Error function of `x` given.
    """
    return np.array(
        amplitude * 0.5 * (1 + erf(_norm(x, center, sigma))),
    )


def heaviside(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Heaviside step function.

    $$
    f(x) = \begin{cases}
    0 & x < 0 \\
    0.5 & x = 0 \\
    1 & x > 0
    \end{cases}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Heaviside step function.
                Defaults to 1.0.
        center (float, optional): Center of the Heaviside step function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the Heaviside step function.
             Defaults to 1.0.


    Returns:
        NDArray[np.float64]: Heaviside step function of `x` given.
    """
    return np.array(
        amplitude * 0.5 * (1 + np.sign(_norm(x, center, sigma))),
    )


def atan_step(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional arctan step function.

    $$
    f(x) = \frac{1}{\pi} \arctan(\frac{x - c}{s})
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the arctan step function.
                Defaults to 1.0.
        center (float, optional): Center of the arctan step function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the arctan step function.
             Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Arctan step function of `x` given.
    """
    return np.array(
        amplitude * 0.5 * (1 + np.arctan(_norm(x, center, sigma)) / pi),
    )


def log_step(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional logarithmic step function.

    $$
    f(x) = \frac{1}{1 + e^{-\frac{x - c}{s}}}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the logarithmic step function.
                Defaults to 1.0.
        center (float, optional): Center of the logarithmic step function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the logarithmic step function.
             Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Logarithmic step function of `x` given.
    """
    return np.array(
        amplitude * 0.5 * (1 + np.log(_norm(x, center, sigma)) / pi),
    )


def cgaussian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmg: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional cumulative Gaussian function.

    $$
    f(x) = \frac{1}{2} \left[1 + erf\left(\frac{x - c}{s \sqrt{2}}\right)\right]
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Gaussian function. Defaults to
            1.0.
        center (float, optional): Center of the Gaussian function. Defaults to 0.0.
        fwhmg (float, optional): Full width at half maximum of the Gaussian
             function. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Cumulative Gaussian function of `x` given.
    """
    sigma = fwhmg * FWHMG2SIG
    return np.array(
        amplitude * 0.5 * (1 + erf((x - center) / (sigma * np.sqrt(2.0)))),
    )


def clorentzian(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhml: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional cumulative Lorentzian function.

    $$
    f(x) = \frac{1}{\pi} \arctan\left(\frac{x - c}{s}\right) + \frac{1}{2}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Lorentzian function.
                Defaults to 1.0.
        center (float, optional): Center of the Lorentzian function.
             Defaults to 0.0.
        fwhml (float, optional): Full width at half maximum of the Lorentzian
            function. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Cumulative Lorentzian function of `x` given.
    """
    sigma = fwhml * FWHML2SIG
    return np.array(amplitude * (np.arctan((x - center) / sigma) / pi) + 0.5)


def cvoigt(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    fwhmv: float = 1.0,
    gamma: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional cumulative Voigt function.

    $$
    f(x) = \frac{1}{2} \left[1 + erf\left(\frac{x - c}{s \sqrt{2}}\right)\right]
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Voigt function. Defaults to
            1.0.
        center (float, optional): Center of the Voigt function. Defaults to 0.0.
        fwhmv (float, optional): Full width at half maximum of the Voigt function.
            Defaults to 1.0.
        gamma (float, optional): Gamma of the Voigt function. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Cumulative Voigt function of `x` given.
    """
    sigma = fwhmv * FWHMV2SIG
    return np.array(
        amplitude
        * 0.5
        * (1 + erf((x - center) / (sigma * np.sqrt(2.0))))
        * np.exp(-(((x - center) / gamma) ** 2)),
    )


def polynom2(
    x: NDArray[np.float64],
    coefficient0: float = 1.0,
    coefficient1: float = 1.0,
    coefficient2: float = 1.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional second order polynomial function.

    $$
    f(x) = c_2 x^2 + c_1 x + c_0
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data
        coefficient0 (float, optional): Zeroth coefficient of the
             polynomial function. Defaults to 1.0.
        coefficient1 (float, optional): First coefficient of the
             polynomial function. Defaults to 1.0.
        coefficient2 (float, optional): Second coefficient of the
             polynomial function. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Third order polynomial function of `x`
    """
    return np.array(coefficient0 + coefficient1 * x + coefficient2 * x**2)


def polynom3(
    x: NDArray[np.float64],
    coefficient0: float = 1.0,
    coefficient1: float = 1.0,
    coefficient2: float = 1.0,
    coefficient3: float = 1.0,
) -> NDArray[np.float64]:
    """Return a 1-dimensional third order polynomial function.

    $$
    f(x) = c_3 x^3 + c_2 x^2 + c_1 x + c_0
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data
        coefficient0 (float, optional): Zeroth coefficient of the
             polynomial function. Defaults to 1.0.
        coefficient1 (float, optional): First coefficient of the
             polynomial function. Defaults to 1.0.
        coefficient2 (float, optional): Second coefficient of the
             polynomial function. Defaults to 1.0.
        coefficient3 (float, optional): Third coefficient of the
             polynomial function. Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Third order polynomial function of `x`
    """
    return np.array(
        coefficient0 + coefficient1 * x + coefficient2 * x**2 + coefficient3 * x**3,
    )


def pearson1(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    exponent: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Pearson type I distribution.

    $$
    f(x) = \frac{A}{\sigma \sqrt{2 \pi}} \left[1 + \frac{(x - c)^2}{\sigma^2}
    \right]^{-\frac{1}{\nu}}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Pearson type I function.
                Defaults to 1.0.
        center (float, optional): Center of the Pearson type I function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the Pearson type I function.
             Defaults to 1.0.
        exponent (float, optional): Exponent of the Pearson type I function.
             Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Pearson type I function of `x` given.
    """
    return np.array(
        amplitude
        / (sigma * np.sqrt(2 * np.pi))
        * np.power(1 + ((x - center) / sigma) ** 2, -1 / exponent),
    )


def pearson2(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    exponent: float = 1.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Pearson type II distribution.

    $$
    f(x) = \frac{A}{\sigma \sqrt{2 \pi}} \left[1 + \frac{(x - c)^2}{2 \sigma^2}
    \right]^{-\nu}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Pearson type II function.
                Defaults to 1.0.
        center (float, optional): Center of the Pearson type II function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the Pearson type II function.
             Defaults to 1.0.
        exponent (float, optional): Exponent of the Pearson type II function.
             Defaults to 1.0.

    Returns:
        NDArray[np.float64]: Pearson type II function of `x` given.
    """
    return np.array(
        amplitude
        / (sigma * np.sqrt(2 * pi))
        * np.power(1 + ((x - center) / (2 * sigma)) ** 2, -exponent),
    )


def pearson3(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    exponent: float = 1.0,
    skewness: float = 0.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Pearson type III distribution.

    $$
    f(x) = \frac{A}{\sigma \sqrt{2 \pi}} \left[1 + \frac{(x - c)^2}{2 \sigma^2}
    \right]^{-\nu} \left[1 + \frac{\gamma}{\nu}
    \frac{x - c}{\sigma} \right]^{-\nu - 1}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Pearson type III function.
                Defaults to 1.0.
        center (float, optional): Center of the Pearson type III function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the Pearson type III function.
             Defaults to 1.0.
        exponent (float, optional): Exponent of the Pearson type III function.
             Defaults to 1.0.
        skewness (float, optional): Skewness of the Pearson type III function.
             Defaults to 0.0.

    Returns:
        NDArray[np.float64]: Pearson type III function of `x` given.
    """
    return np.array(
        amplitude
        / (sigma * np.sqrt(2 * pi))
        * np.power(1 + ((x - center) / (2 * sigma)) ** 2, -exponent)
        * np.power(
            1 + (skewness / exponent) * ((x - center) / sigma),
            -exponent - 1,
        ),
    )


def pearson4(
    x: NDArray[np.float64],
    amplitude: float = 1.0,
    center: float = 0.0,
    sigma: float = 1.0,
    exponent: float = 1.0,
    skewness: float = 0.0,
    kurtosis: float = 0.0,
) -> NDArray[np.float64]:
    r"""Return a 1-dimensional Pearson type IV distribution.

    $$
    f(x) = \frac{A}{\sigma \sqrt{2 \pi}} \left[1 + \frac{(x - c)^2}{2 \sigma^2}
    \right]^{-\nu} \left[1 + \frac{\gamma}{\nu}
    \frac{x - c}{\sigma} \right]^{-\nu - 1}
    \left[1 + \frac{\delta}{\nu}
    \left(\frac{x - c}{\sigma}\right)^2 \right]^{-\nu - 1/2}
    $$

    Args:
        x (NDArray[np.float64]): `x`-values of the data.
        amplitude (float, optional): Amplitude of the Pearson type IV function.
                Defaults to 1.0.
        center (float, optional): Center of the Pearson type IV function.
             Defaults to 0.0.
        sigma (float, optional): Sigma of the Pearson type IV function.
             Defaults to 1.0.
        exponent (float, optional): Exponent of the Pearson type IV function.
             Defaults to 1.0.
        skewness (float, optional): Skewness of the Pearson type IV function.
             Defaults to 0.0.
        kurtosis (float, optional): Kurtosis of the Pearson type IV function.
             Defaults to 0.0.

    Returns:
        NDArray[np.float64]: Pearson type IV function of `x` given.
    """
    return np.array(
        amplitude
        / (sigma * np.sqrt(2 * pi))
        * np.power(1 + ((x - center) / (2 * sigma)) ** 2, -exponent)
        * np.power(
            1 + (skewness / exponent) * ((x - center) / sigma),
            -exponent - 1,
        )
        * np.power(
            1 + (kurtosis / exponent) * ((x - center) / sigma) ** 2,
            -exponent - 1 / 2,
        ),
    )

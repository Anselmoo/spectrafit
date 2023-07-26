"""Minimization models for curve fitting."""
from collections import defaultdict
from dataclasses import dataclass
from math import log
from math import pi
from math import sqrt
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
from spectrafit.api.models_model import DistributionModelAPI
from spectrafit.api.tools_model import AutopeakAPI
from spectrafit.api.tools_model import GlobalFittingAPI
from spectrafit.api.tools_model import SolverModelsAPI


class DistributionModels:
    """Distribution models for the fit.

    !!! note "About distribution models"

        `DistributionModels` are wrapper functions for the distribution models. The
        overall goal is to extract from the best parameters the single contributions in
        the model. The superposition of the single contributions is the final model.

    !!! note "About the cumulative distribution"

        The cumulative distribution is the sum of the single contributions. The
        cumulative distribution is the model that is fitted to the data. In contrast to
        the single contributions, the cumulative distribution is not normalized and
        therefore the amplitude of the single contributions is not directly comparable
        to the amplitude of the cumulative distribution. Also, the cumulative
        distributions are consquently using the `fwhm` parameter instead of the
        `sigma` parameter.
    """

    @staticmethod
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
        sigma = fwhmg * Constants.fwhmg2sig
        return np.array(amplitude / (Constants.sq2pi * sigma)) * np.exp(
            -((1.0 * x - center) ** 2) / (2 * sigma**2)
        )

    @staticmethod
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
            Union[NDArray[np.float64], float]: Lorentzian distribution of `x` given.
        """
        sigma = fwhml * Constants.fwhml2sig
        return np.array(amplitude / (1 + ((1.0 * x - center) / sigma) ** 2)) / (
            pi * sigma
        )

    @staticmethod
    def voigt(
        x: NDArray[np.float64],
        center: float = 0.0,
        fwhmv: float = 1.0,
        gamma: Optional[float] = None,
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
        sigma = fwhmv * Constants.fwhmv2sig
        if gamma is None:
            gamma = sigma
        z = (x - center + 1j * gamma) / (sigma * Constants.sq2)
        return np.array(wofz(z).real / (sigma * Constants.sq2pi))

    @staticmethod
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
        n = (
            1.36603 * (fwhml / f)
            - 0.47719 * (fwhml / f) ** 2
            + 0.11116 * (fwhml / f) ** 3
        )
        return np.array(
            n
            * DistributionModels.lorentzian(
                x=x, amplitude=amplitude, center=center, fwhml=fwhml
            )
            + (1 - n)
            * DistributionModels.gaussian(
                x=x, amplitude=amplitude, center=center, fwhmg=fwhmg
            )
        )

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def _norm(
        x: NDArray[np.float64], center: float, sigma: float
    ) -> NDArray[np.float64]:
        """Normalize the data for step functions.

        Args:
            x (NDArray[np.float64]): `x`-values of the data.
            center (float): Center of the step function.
            sigma (float): Sigma of the step function.

        Returns:
            NDArray[np.float64]: Normalized data.
        """
        if abs(sigma) < 1.0e-13:
            sigma = 1.0e-13
        return np.subtract(x, center) / sigma

    @staticmethod
    def erf(
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
            amplitude * 0.5 * (1 + erf(DistributionModels._norm(x, center, sigma)))
        )

    @staticmethod
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
            amplitude * 0.5 * (1 + np.sign(DistributionModels._norm(x, center, sigma)))
        )

    @staticmethod
    def atan(
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
            amplitude
            * 0.5
            * (1 + np.arctan(DistributionModels._norm(x, center, sigma)) / pi)
        )

    @staticmethod
    def log(
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
            amplitude
            * 0.5
            * (1 + np.log(DistributionModels._norm(x, center, sigma)) / pi)
        )

    @staticmethod
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
        sigma = fwhmg * Constants.fwhmg2sig
        return np.array(
            amplitude * 0.5 * (1 + erf((x - center) / (sigma * np.sqrt(2.0))))
        )

    @staticmethod
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
        sigma = fwhml * Constants.fwhml2sig
        return np.array(amplitude * (np.arctan((x - center) / sigma) / pi) + 0.5)

    @staticmethod
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
        sigma = fwhmv * Constants.fwhmv2sig
        return np.array(
            amplitude
            * 0.5
            * (1 + erf((x - center) / (sigma * np.sqrt(2.0))))
            * np.exp(-(((x - center) / gamma) ** 2))
        )

    @staticmethod
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

    @staticmethod
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
            coefficient0
            + coefficient1 * x
            + coefficient2 * x**2
            + coefficient3 * x**3
        )

    @staticmethod
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
            * np.power(1 + ((x - center) / sigma) ** 2, -1 / exponent)
        )

    @staticmethod
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
            * np.power(1 + ((x - center) / (2 * sigma)) ** 2, -exponent)
        )

    @staticmethod
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
                1 + (skewness / exponent) * ((x - center) / sigma), -exponent - 1
            )
        )

    @staticmethod
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
                1 + (skewness / exponent) * ((x - center) / sigma), -exponent - 1
            )
            * np.power(
                1 + (kurtosis / exponent) * ((x - center) / sigma) ** 2,
                -exponent - 1 / 2,
            )
        )


@dataclass(frozen=True)
class ReferenceKeys:
    """Reference keys for model fitting and peak detection."""

    __models__ = list(DistributionModelAPI.schema()["properties"].keys())

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
            raise NotImplementedError(f"{model} is not supported!")

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

        1. Natural logarithm of 2

            $$
            ln2 = \log{2}
            $$

        2. Square root of 2 times pi

            $$
            sq2pi = \sqrt{2 \pi}
            $$

        3. Square root of pi

            $$
            sqpi = \sqrt{ \pi}
            $$

        4. Square root of 2

            $$
            sq2 = \sqrt{2}
            $$

        5. Full width at half maximum to sigma for Gaussian

            $$
            fwhmg2sig = \frac{1}{ 2 \sqrt{2\log{2}}}
            $$

        6. Full width at half maximum to sigma for Lorentzian

            $$
            fwhml2sig = \frac{1}{2}
            $$

        7. Full width at half maximum to sigma for Voigt according to the article by
            Olivero and Longbothum[^1], check also
            [XPSLibary website](https://xpslibrary.com/voigt-peak-shape/).

            $$
            fwhm_{\text{Voigt}} \approx 0.5346 \cdot fwhm_{\text{Gaussian}} +
              \sqrt{ 0.2166 fwhm_{\text{Lorentzian}}^2  + fwhm_{\text{Gaussian}}^2 }

            $$

            In case of equal FWHM for Gaussian and Lorentzian, the Voigt FWHM can be
            defined as:

            $$
            fwhm_{\text{Voigt}} \approx 1.0692 + 2 \sqrt{0.2166 + 2 \ln{2}} \cdot \sigma
            $$

            $$
            fwhmv2sig = \frac{1}{fwhm_{\text{Voigt}}}
            $$

        [^1]:
            J.J. Olivero, R.L. Longbothum,
            _Empirical fits to the Voigt line width: A brief review_,
            **Journal of Quantitative Spectroscopy and Radiative Transfer**,
            Volume 17, Issue 2, 1977, Pages 233-236, ISSN 0022-4073,
            https://doi.org/10.1016/0022-4073(77)90161-3.
    """

    ln2 = log(2.0)
    sq2pi = sqrt(2.0 * pi)
    sqpi = sqrt(pi)
    sq2 = sqrt(2.0)
    fwhmg2sig = 1 / (2.0 * sqrt(2.0 * log(2.0)))
    fwhml2sig = 1 / 2.0
    fwhmv2sig = 1 / (2 * 0.5346 + 2 * sqrt(0.2166 + log(2) * 2))


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
            divided by the factor of `4`. In case of negative ratios, the value will be
            set to `Zero`.

        Returns:
            float: Estimated relative height of a peak.
        """
        try:
            rel_height = (hmean(self.data) - self.data.min()) / 4
        except ValueError as exc:
            print(f"{exc}: Using standard arithmetic mean of NumPy.\n")
            rel_height = (self.data.mean() - self.data.min()) / 4
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
            self.default_values()
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

    def default_values(self) -> None:
        """Set the default values for the peak detection."""
        self.height = self.estimate_height
        self.threshold = self.estimate_threshold
        self.distance = self.estimate_distance
        self.prominence = self.estimate_prominence
        self.width = self.estimated_width
        self.wlen = self.estimated_wlen
        self.rel_height = self.estimated_rel_height
        self.plateau_size = 0

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
            and "modeltype" in self.args["autopeak"]
        ):
            _model = self.args["autopeak"]["modeltype"].lower()
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
            self.define_parameters_loop(key_1=key_1, value_1=value_1)

    def define_parameters_loop(self, key_1: str, value_1: Dict[str, Any]) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            value_1 (Dict[str, Any]): The value of the first level of the input
                 dictionary.
        """
        for key_2, value_2 in value_1.items():
            self.define_parameters_loop_2(key_1=key_1, key_2=key_2, value_2=value_2)

    def define_parameters_loop_2(
        self, key_1: str, key_2: str, value_2: Dict[str, Any]
    ) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            value_2 (Dict[str, Any]): The value of the second level of the input
                 dictionary.
        """
        for key_3, value_3 in value_2.items():
            self.define_parameters_loop_3(
                key_1=key_1, key_2=key_2, key_3=key_3, value_3=value_3
            )

    def define_parameters_loop_3(
        self, key_1: str, key_2: str, key_3: str, value_3: Dict[str, Any]
    ) -> None:
        """Loop through the input parameters for a `params`-dictionary.

        Args:
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            key_3 (str): The key of the third level of the input dictionary.
            value_3 (Dict[str, Any]): The value of the third level of the input
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
        self, col_i: int, key_1: str, key_2: str, key_3: str, value_3: Dict[str, Any]
    ) -> None:
        """Define the input parameters for a `params`-dictionary for global fitting.

        Args:
            col_i (int): The column index.
            key_1 (str): The key of the first level of the input dictionary.
            key_2 (str): The key of the second level of the input dictionary.
            key_3 (str): The key of the third level of the input dictionary.
            value_3 (Dict[str, Any]): The value of the third level of the input
                 dictionary.
        """
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
                **self.args_solver["minimizer"],
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
            params (Dict[str, Parameters]): The best optimized parameters of the fit.
            x (NDArray[np.float64]): `x`-values of the data.
            data (NDArray[np.float64]): `y`-values of the data as 1d-array.

        Returns:
            NDArray[np.float64]: The best-fitted data based on the proposed model.
        """
        val = np.zeros(x.shape)
        peak_kwargs: Dict[Tuple[str, str], Parameters] = defaultdict(dict)

        for model in params:
            model = model.lower()
            ReferenceKeys().model_check(model=model)
            c_name = model.split("_")
            peak_kwargs[(c_name[0], c_name[2])][c_name[1]] = params[model]

        for key, _kwarg in peak_kwargs.items():
            val += getattr(DistributionModels(), key[0])(x, **_kwarg)
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
            params (Dict[str, Parameters]): The best optimized parameters of the fit.
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
            val[:, i] += getattr(DistributionModels(), key[0])(x, **_kwarg)

        val -= data
        return val.flatten()


def calculated_model(
    params: Dict[str, Parameters],
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
        _df[c_name] = getattr(DistributionModels(), key[0])(x, **_kwarg)

    return _df

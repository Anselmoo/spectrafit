"""Distribution models for curve fitting.

This module contains wrapper functions for distribution models including
Gaussian, Lorentzian, Voigt, PseudoVoigt, and Mössbauer spectroscopy models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from spectrafit.models.moessbauer import moessbauer_doublet as _moessbauer_doublet
from spectrafit.models.moessbauer import moessbauer_octet as _moessbauer_octet
from spectrafit.models.moessbauer import moessbauer_sextet as _moessbauer_sextet
from spectrafit.models.moessbauer import moessbauer_singlet as _moessbauer_singlet
from spectrafit.models.regular import atan_step as _atan
from spectrafit.models.regular import cgaussian as _cgaussian
from spectrafit.models.regular import clorentzian as _clorentzian
from spectrafit.models.regular import constant as _constant
from spectrafit.models.regular import cvoigt as _cvoigt
from spectrafit.models.regular import erf_step as _erf
from spectrafit.models.regular import exponential as _exponential
from spectrafit.models.regular import gaussian as _gaussian
from spectrafit.models.regular import heaviside as _heaviside
from spectrafit.models.regular import linear as _linear
from spectrafit.models.regular import log_step as _log
from spectrafit.models.regular import lorentzian as _lorentzian
from spectrafit.models.regular import orcagaussian as _orcagaussian
from spectrafit.models.regular import pearson1 as _pearson1
from spectrafit.models.regular import pearson2 as _pearson2
from spectrafit.models.regular import pearson3 as _pearson3
from spectrafit.models.regular import pearson4 as _pearson4
from spectrafit.models.regular import polynom2 as _polynom2
from spectrafit.models.regular import polynom3 as _polynom3
from spectrafit.models.regular import power as _power
from spectrafit.models.regular import pseudovoigt as _pseudovoigt
from spectrafit.models.regular import voigt as _voigt


if TYPE_CHECKING:
    import numpy as np

    from numpy.typing import NDArray


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
        distributions are consequently using the `fwhm` parameter instead of the
        `sigma` parameter.
    """

    @staticmethod
    def gaussian(
        x: NDArray[np.float64],
        amplitude: float = 1.0,
        center: float = 0.0,
        fwhmg: float = 1.0,
    ) -> NDArray[np.float64]:
        """Return the wrapper function for the Gaussian model from regular_models."""
        return _gaussian(x=x, amplitude=amplitude, center=center, fwhmg=fwhmg)

    @staticmethod
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
        return _orcagaussian(x=x, amplitude=amplitude, center=center, width=width)

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
        return _lorentzian(x=x, amplitude=amplitude, center=center, fwhml=fwhml)

    @staticmethod
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
        return _voigt(x=x, center=center, fwhmv=fwhmv, gamma=gamma)

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
        return _pseudovoigt(
            x=x,
            amplitude=amplitude,
            center=center,
            fwhmg=fwhmg,
            fwhml=fwhml,
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
        return _exponential(x=x, amplitude=amplitude, decay=decay, intercept=intercept)

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
        return _power(x=x, amplitude=amplitude, exponent=exponent, intercept=intercept)

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
        return _linear(x=x, slope=slope, intercept=intercept)

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
        return _constant(x=x, amplitude=amplitude)

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
        return _erf(x=x, amplitude=amplitude, center=center, sigma=sigma)

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
        return _heaviside(x=x, amplitude=amplitude, center=center, sigma=sigma)

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
        return _atan(x=x, amplitude=amplitude, center=center, sigma=sigma)

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
        return _log(x=x, amplitude=amplitude, center=center, sigma=sigma)

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
        return _cgaussian(x=x, amplitude=amplitude, center=center, fwhmg=fwhmg)

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
        return _clorentzian(x=x, amplitude=amplitude, center=center, fwhml=fwhml)

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
        return _cvoigt(
            x=x,
            amplitude=amplitude,
            center=center,
            fwhmv=fwhmv,
            gamma=gamma,
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
        return _polynom2(
            x=x,
            coefficient0=coefficient0,
            coefficient1=coefficient1,
            coefficient2=coefficient2,
        )

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
        return _polynom3(
            x=x,
            coefficient0=coefficient0,
            coefficient1=coefficient1,
            coefficient2=coefficient2,
            coefficient3=coefficient3,
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
        return _pearson1(
            x=x,
            amplitude=amplitude,
            center=center,
            sigma=sigma,
            exponent=exponent,
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
        return _pearson2(
            x=x,
            amplitude=amplitude,
            center=center,
            sigma=sigma,
            exponent=exponent,
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
        return _pearson3(
            x=x,
            amplitude=amplitude,
            center=center,
            sigma=sigma,
            exponent=exponent,
            skewness=skewness,
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
        return _pearson4(
            x=x,
            amplitude=amplitude,
            center=center,
            sigma=sigma,
            exponent=exponent,
            skewness=skewness,
            kurtosis=kurtosis,
        )

    @staticmethod
    def moessbauersinglet(
        x: NDArray[np.float64],
        amplitude: float = 1.0,
        isomershift: float = 0.0,
        fwhml: float = 0.25,
        center: float = 0.0,
        background: float = 0.0,
    ) -> NDArray[np.float64]:
        """Compute a Mössbauer singlet via Lorentzian plus background.

        Args:
            x (NDArray[np.float64]): Velocity array (mm/s).
            amplitude (float, optional): Peak amplitude. Defaults to 1.0.
            isomershift (float, optional): Isomer shift (mm/s). Defaults to 0.0.
            fwhml (float, optional): Lorentzian full-width at half-maximum. Defaults to 0.25.
            center (float, optional): Global spectrum offset in mm/s. Defaults to 0.0.
            background (float, optional): Constant background level. Defaults to 0.0.

        Returns:
            NDArray[np.float64]: Computed transmission intensity array.

        """
        # Call the implementation from moessbauer_models.py
        return _moessbauer_singlet(
            x=x,
            amplitude=amplitude,
            isomer_shift=isomershift,
            fwhml=fwhml,
            center=center,
            background=background,
        )

    @staticmethod
    def moessbauerdoublet(
        x: NDArray[np.float64],
        amplitude: float = 1.0,
        isomershift: float = 0.4,
        fwhml: float = 0.25,
        quadrupolesplitting: float = 0.8,
        center: float = 0.0,
        background: float = 0.0,
    ) -> NDArray[np.float64]:
        """Compute a Mössbauer doublet via two Lorentzians plus background.

        Args:
            x (NDArray[np.float64]): Velocity or energy array (mm/s).
            amplitude (float, optional): Peak amplitude. Defaults to 1.0.
            isomershift (float, optional): Isomer shift (mm/s). Defaults to 0.4.
            fwhml (float, optional): Lorentzian full-width at half-maximum. Defaults to 0.25.
            quadrupolesplitting (float, optional): Quadrupole splitting (mm/s). Defaults to 0.8.
            center (float, optional): Global spectrum offset in mm/s. Defaults to 0.0.
            background (float, optional): Constant background level. Defaults to 0.0.

        Returns:
            NDArray[np.float64]: Computed intensity array.

        """
        # Call the implementation from moessbauer_models.py
        return _moessbauer_doublet(
            x=x,
            amplitude=amplitude,
            isomer_shift=isomershift,
            fwhml=fwhml,
            quadrupole_splitting=quadrupolesplitting,
            center=center,
            background=background,
        )

    @staticmethod
    def moessbauersextet(
        x: NDArray[np.float64],
        amplitude: float = 1.0,
        isomershift: float = 0.0,
        fwhml: float = 0.25,
        magneticfield: float = 33.0,
        quadrupoleshift: float = 0.0,
        center: float = 0.0,
        background: float = 0.0,
        anglethetaphi: dict[str, float] | None = None,
    ) -> NDArray[np.float64]:
        """Compute a Mössbauer sextet via six Lorentzians plus background.

        Args:
            x (NDArray[np.float64]): Velocity or energy array (mm/s).
            amplitude (float, optional): Peak amplitude. Defaults to 1.0.
            isomershift (float, optional): Isomer shift (mm/s). Defaults to 0.0.
            fwhml (float, optional): Lorentzian full-width at half-maximum. Defaults to 0.25.
            magneticfield (float, optional): Hyperfine field in Tesla. Defaults to 33.0.
            quadrupoleshift (float, optional): First-order quadrupole shift in mm/s.
                Defaults to 0.0.
            center (float, optional): Global spectrum offset in mm/s. Defaults to 0.0.
            background (float, optional): Constant background level. Defaults to 0.0.
            anglethetaphi (dict[str, float], optional): Orientation angles. Defaults to None.

        Returns:
            NDArray[np.float64]: Computed intensity array.
        """
        return _moessbauer_sextet(
            x=x,
            amplitude=amplitude,
            isomer_shift=isomershift,
            fwhml=fwhml,
            magnetic_field=magneticfield,
            quadrupole_shift=quadrupoleshift,
            center=center,
            angle_theta_phi=anglethetaphi,
            background=background,
        )

    @staticmethod
    def moessbaueroctet(
        x: NDArray[np.float64],
        amplitude: float = 1.0,
        isomershift: float = 0.0,
        fwhml: float = 0.25,
        magneticfield: float = 33.0,
        quadrupoleshift: float = 0.0,
        center: float = 0.0,
        efg_vzz: float = 1e21,
        efg_eta: float = 0.0,
        anglethetaphi: dict[str, float] | None = None,
        temperature: float = 300.0,
        sodshift: float = 0.0,
        sitefraction: float = 1.0,
        background: float = 0.0,
    ) -> NDArray[np.float64]:
        """Compute a Mössbauer octet via eight Lorentzians plus background.

        Used for materials with a mixture of magnetic and quadrupole interactions.

        Args:
            x (NDArray[np.float64]): Velocity or energy array (mm/s).
            amplitude (float, optional): Peak amplitude. Defaults to 1.0.
            isomershift (float, optional): Isomer shift (mm/s). Defaults to 0.0.
            fwhml (float, optional): Lorentzian full-width at half-maximum. Defaults to 0.25.
            magneticfield (float, optional): Hyperfine field in Tesla. Defaults to 33.0.
            quadrupoleshift (float, optional): First-order quadrupole shift in mm/s.
                Defaults to 0.0.
            center (float, optional): Global spectrum offset in mm/s. Defaults to 0.0.
            efg_vzz (float, optional): Principal component of EFG tensor. Defaults to 1e21.
            efg_eta (float, optional): EFG asymmetry parameter. Defaults to 0.0.
            anglethetaphi (dict[str, float], optional): Orientation angles. Defaults to None.
            temperature (float, optional): Temperature in K. Defaults to 300.0.
            sodshift (float, optional): Second-order Doppler shift in mm/s. Defaults to 0.0.
            sitefraction (float, optional): Site fraction. Defaults to 1.0.
            background (float, optional): Constant background level. Defaults to 0.0.

        Returns:
            NDArray[np.float64]: Computed intensity array.
        """
        # Call the implementation from moessbauer_models.py
        return _moessbauer_octet(
            x=x,
            amplitude=amplitude,
            isomer_shift=isomershift,
            fwhml=fwhml,
            magnetic_field=magneticfield,
            quadrupole_shift=quadrupoleshift,
            center=center,
            efg_vzz=efg_vzz,
            efg_eta=efg_eta,
            angle_theta_phi=anglethetaphi,
            temperature=temperature,
            sod_shift=sodshift,
            site_fraction=sitefraction,
            background=background,
        )

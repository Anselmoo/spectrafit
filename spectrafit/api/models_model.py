"""Reference model for the API of the models distributions."""

from __future__ import annotations

from typing import Callable

from pydantic import BaseModel
from pydantic import Field

from spectrafit.api.moessbauer_model import MoessbauerDoubletAPI
from spectrafit.api.moessbauer_model import MoessbauerOctetAPI
from spectrafit.api.moessbauer_model import MoessbauerSextetAPI
from spectrafit.api.moessbauer_model import MoessbauerSingletAPI


__description__ = "Lmfit expression for explicit dependencies."


class AmplitudeAPI(BaseModel):
    """Definition of the amplitude of the models distributions."""

    max: float | None = Field(default=None, description="Maximum amplitude.")
    min: int | None = Field(default=None, description="Minimum amplitude.")
    vary: bool = Field(default=True, description="Vary the amplitude.")
    value: float | None = Field(default=None, description="Initial Amplitude value.")
    expr: str | None = Field(default=None, description=__description__)


class CenterAPI(BaseModel):
    """Definition of the center of the models distributions."""

    max: float | None = Field(default=None, description="Maximum center.")
    min: int | None = Field(default=None, description="Minimum center.")
    vary: bool = Field(default=True, description="Vary the center.")
    value: float | None = Field(default=None, description="Initial Center value.")
    expr: str | None = Field(default=None, description=__description__)


class FwhmgAPI(BaseModel):
    """Definition of the FWHM Gaussian of the models distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Full Width Half Maximum of the Gaussian Distribution.",
    )
    min: int | None = Field(
        default=None,
        description="Minimum Full Width Half Maximum of the Gaussian Distribution.",
    )
    vary: bool = Field(
        default=True,
        description="Vary the Full Width Half Maximum of the Gaussian Distribution.",
    )
    value: float | None = Field(
        default=None,
        description="Initial Full Width Half Maximum of "
        "the Gaussian Distribution value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class FwhmlAPI(BaseModel):
    """Definition of the FWHM Lorentzian of the models distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Full Width Half Maximum of the Lorentzian Distribution.",
    )
    min: int | None = Field(
        default=None,
        description="Minimum Full Width Half Maximum of the Lorentzian Distribution.",
    )
    vary: bool = Field(
        default=True,
        description="Vary the Full Width Half Maximum of the Lorentzian Distribution.",
    )
    value: float | None = Field(
        default=None,
        description="Initial Full Width Half Maximum of "
        "the Lorentzian Distribution value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class FwhmvAPI(BaseModel):
    """Definition of the FWHM Voigt of the models distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Full Width Half Maximum of the Voigt Distribution.",
    )
    min: int | None = Field(
        default=None,
        description="Minimum Full Width Half Maximum of the Voigt Distribution.",
    )
    vary: bool = Field(
        default=True,
        description="Vary the Full Width Half Maximum of the Voigt Distribution.",
    )
    value: float | None = Field(
        default=None,
        description="Initial Full Width Half Maximum of the Voigt Distribution value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class WidthAPI(BaseModel):
    """Definition of the Width of the ORCA Gaussian of the models distributions."""

    max: float | None = Field(default=None, description="Maximum width.")
    min: int | None = Field(default=None, description="Minimum width.")
    vary: bool = Field(default=True, description="Vary the width.")
    value: float | None = Field(default=None, description="Initial width value.")
    expr: str | None = Field(default=None, description=__description__)


class GammaAPI(BaseModel):
    """Definition of the Gamma of the Voigt of the models distributions."""

    max: float | None = Field(default=None, description="Maximum gamma.")
    min: int | None = Field(default=None, description="Minimum gamma.")
    vary: bool = Field(default=True, description="Vary the gamma.")
    value: float | None = Field(default=None, description="Initial Gamma value.")
    expr: str | None = Field(default=None, description=__description__)


class DecayAPI(BaseModel):
    """Definition of the Decay of the Exponential of the models distributions."""

    max: float | None = Field(default=None, description="Maximum decay rate.")
    min: int | None = Field(default=None, description="Minimum decay rate.")
    vary: bool = Field(default=True, description="Vary the decay rate.")
    value: float | None = Field(
        default=None,
        description="Initial decay rate value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class InterceptAPI(BaseModel):
    """Definition of the Intercept of the Linear of the models distributions."""

    max: float | None = Field(default=None, description="Maximum intercept.")
    min: int | None = Field(default=None, description="Minimum intercept.")
    vary: bool = Field(default=True, description="Vary the intercept.")
    value: float | None = Field(default=None, description="Initial intercept value.")
    expr: str | None = Field(default=None, description=__description__)


class ExponentAPI(BaseModel):
    """Definition of the Exponent of the Linear of the models distributions."""

    max: float | None = Field(default=None, description="Maximum exponent.")
    min: int | None = Field(default=None, description="Minimum exponent.")
    vary: bool = Field(default=True, description="Vary the exponent.")
    value: float | None = Field(default=None, description="Initial exponent value.")
    expr: str | None = Field(default=None, description=__description__)


class SlopeAPI(BaseModel):
    """Definition of the Slope of the Linear of the models distributions."""

    max: float | None = Field(default=None, description="Maximum slope.")
    min: int | None = Field(default=None, description="Minimum slope.")
    vary: bool = Field(default=True, description="Vary the slope.")
    value: float | None = Field(default=None, description="Inital slope value.")
    expr: str | None = Field(default=None, description=__description__)


class SigmaAPI(BaseModel):
    """Definition of the Sigma of the models distributions."""

    max: float | None = Field(default=None, description="Maximum sigma.")
    min: int | None = Field(default=None, description="Minimum sigma.")
    vary: bool = Field(default=True, description="Vary the sigma.")
    value: float | None = Field(default=None, description="Initial sigma value.")
    expr: str | None = Field(default=None, description=__description__)


class CoefficientAPI(BaseModel):
    """Definition of the Coefficient of the models distributions."""

    max: float | None = Field(default=None, description="Maximum coefficient.")
    min: int | None = Field(default=None, description="Minimum coefficient.")
    vary: bool = Field(default=True, description="Vary the coefficient.")
    value: float | None = Field(
        default=None,
        description="Initial coefficient value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class PseudovoigtAPI(BaseModel):
    """Definition of the Pseudovoigt of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    fwhmg: FwhmgAPI = FwhmgAPI()
    fwhml: FwhmlAPI = FwhmlAPI()


class GaussianAPI(BaseModel):
    """Definition of the Gaussian of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    fwhmg: FwhmgAPI = FwhmgAPI()


class OrcaGaussianAPI(BaseModel):
    """Definition of the ORCA Gaussian of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    width: WidthAPI = WidthAPI()


class LorentzianAPI(BaseModel):
    """Definition of the Lorentzian of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    fwhml: FwhmlAPI = FwhmlAPI()


class VoigtAPI(BaseModel):
    """Definition of the Voigt of the models distributions."""

    center: CenterAPI = CenterAPI()
    fwhmv: FwhmvAPI = FwhmvAPI()
    gamma: GammaAPI = GammaAPI()


class ExponentialAPI(BaseModel):
    """Definition of the Exponential of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    decay: DecayAPI = DecayAPI()
    intercept: InterceptAPI = InterceptAPI()


class PowerAPI(BaseModel):
    """Definition of the Power of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    exponent: ExponentAPI = ExponentAPI()
    intercept: InterceptAPI = InterceptAPI()


class LinearAPI(BaseModel):
    """Definition of the Linear of the models distributions."""

    slope: SlopeAPI = SlopeAPI()
    intercept: InterceptAPI = InterceptAPI()


class ConstantAPI(BaseModel):
    """Definition of the Constant of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()


class ErfAPI(BaseModel):
    """Definition of the Step of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()


class HeavisideAPI(BaseModel):
    """Definition of the Step of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()


class AtanAPI(BaseModel):
    """Definition of the Step of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()


class LogAPI(BaseModel):
    """Definition of the Step of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()


class CGaussianAPI(BaseModel):
    """Definition of the cumulative Gaussian of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    fwhmg: FwhmgAPI = FwhmgAPI()


class CLorentzianAPI(BaseModel):
    """Definition of the cumulative Lorentzian of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    fwhml: FwhmlAPI = FwhmlAPI()


class CVoigtAPI(BaseModel):
    """Definition of the cumulative Voigt of the models distributions."""

    center: CenterAPI = CenterAPI()
    fwhmv: FwhmvAPI = FwhmvAPI()
    gamma: GammaAPI = GammaAPI()


class Polynomia2API(BaseModel):
    """Definition of the second order polynomial of the models distributions."""

    coefficient0: CoefficientAPI = CoefficientAPI()
    coefficient1: CoefficientAPI = CoefficientAPI()
    coefficient2: CoefficientAPI = CoefficientAPI()


class Polynomia3API(BaseModel):
    """Definition of the third order polynomial of the models distributions."""

    coefficient0: CoefficientAPI = CoefficientAPI()
    coefficient1: CoefficientAPI = CoefficientAPI()
    coefficient2: CoefficientAPI = CoefficientAPI()
    coefficient3: CoefficientAPI = CoefficientAPI()


class SkewnessAPI(BaseModel):
    """Definition of the skewness of the models distributions."""

    max: float | None = Field(default=None, description="Maximum skewness.")
    min: int | None = Field(default=None, description="Minimum skewness.")
    vary: bool = Field(default=True, description="Vary the skewness.")
    value: float | None = Field(default=None, description="Initial skewness value.")
    expr: str | None = Field(default=None, description=__description__)


class KurtosisAPI(BaseModel):
    """Definition of the kurtosis of the models distributions."""

    max: float | None = Field(default=None, description="Maximum kurtosis.")
    min: int | None = Field(default=None, description="Minimum kurtosis.")
    vary: bool = Field(default=True, description="Vary the kurtosis.")
    value: float | None = Field(default=None, description="Initial kurtosis value.")
    expr: str | None = Field(default=None, description=__description__)


class Pearson1API(BaseModel):
    """Definition of the pearson type I of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()
    exponent: ExponentAPI = ExponentAPI()


class Pearson2API(BaseModel):
    """Definition of the pearson type II of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()
    exponent: ExponentAPI = ExponentAPI()


class Pearson3API(BaseModel):
    """Definition of the pearson type III of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()
    exponent: ExponentAPI = ExponentAPI()
    skewness: SkewnessAPI = SkewnessAPI()


class Pearson4API(BaseModel):
    """Definition of the pearson type IV of the models distributions."""

    amplitude: AmplitudeAPI = AmplitudeAPI()
    center: CenterAPI = CenterAPI()
    sigma: SigmaAPI = SigmaAPI()
    exponent: ExponentAPI = ExponentAPI()
    skewness: SkewnessAPI = SkewnessAPI()
    kurtosis: KurtosisAPI = KurtosisAPI()


class DistributionModelAPI(BaseModel):
    """Definition of the models distributions."""

    gaussian: GaussianAPI = GaussianAPI()
    orcagaussian: OrcaGaussianAPI = OrcaGaussianAPI()
    lorentzian: LorentzianAPI = LorentzianAPI()
    voigt: VoigtAPI = VoigtAPI()
    pseudovoigt: PseudovoigtAPI = PseudovoigtAPI()
    exponential: ExponentialAPI = ExponentialAPI()
    power: PowerAPI = PowerAPI()
    linear: LinearAPI = LinearAPI()
    constant: ConstantAPI = ConstantAPI()
    erf: ErfAPI = ErfAPI()
    heaviside: HeavisideAPI = HeavisideAPI()
    atan: AtanAPI = AtanAPI()
    log: LogAPI = LogAPI()
    cgaussian: CGaussianAPI = CGaussianAPI()
    clorentzian: CLorentzianAPI = CLorentzianAPI()
    cvoigt: CVoigtAPI = CVoigtAPI()
    polynom2: Polynomia2API = Polynomia2API()
    polynom3: Polynomia3API = Polynomia3API()
    pearson1: Pearson1API = Pearson1API()
    pearson2: Pearson2API = Pearson2API()
    pearson3: Pearson3API = Pearson3API()
    pearson4: Pearson4API = Pearson4API()
    # Add Mössbauer models
    moessbauersinglet: MoessbauerSingletAPI = MoessbauerSingletAPI()
    moessbauerdoublet: MoessbauerDoubletAPI = MoessbauerDoubletAPI()
    moessbauersextet: MoessbauerSextetAPI = MoessbauerSextetAPI()
    moessbaueroctet: MoessbauerOctetAPI = MoessbauerOctetAPI()


class ConfIntervalAPI(BaseModel):
    """Definition of Confidence Interval Function."""

    p_names: list[str] | None = Field(
        default=None,
        description="List of parameters names.",
    )
    trace: bool = Field(
        default=True,
        description="Trace of the confidence interval matrix.",
    )
    maxiter: int = Field(
        default=200,
        gt=1,
        le=2000,
        description="Maximum number of iteration",
    )
    verbose: bool = Field(
        default=False,
        description="Print information about the fit process.",
    )
    prob_func: Callable[[float], float] | None = Field(
        default=None,
        description="Probing function.",
    )

"""Reference model for the API of the Mössbauer models distributions."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


__description__ = "Lmfit expression for explicit dependencies."


# Define base parameter classes locally to avoid circular imports
class AmplitudeAPI(BaseModel):
    """Definition of the amplitude of the models distributions."""

    max: float | None = Field(default=None, description="Maximum amplitude.")
    min: float | None = Field(default=None, description="Minimum amplitude.")
    vary: bool = Field(default=True, description="Vary the amplitude.")
    value: float | None = Field(default=None, description="Initial Amplitude value.")
    expr: str | None = Field(default=None, description=__description__)


class CenterAPI(BaseModel):
    """Definition of the center of the models distributions."""

    max: float | None = Field(default=None, description="Maximum center.")
    min: float | None = Field(default=None, description="Minimum center.")
    vary: bool = Field(default=True, description="Vary the center.")
    value: float | None = Field(default=None, description="Initial Center value.")
    expr: str | None = Field(default=None, description=__description__)


class IsomerShiftAPI(BaseModel):
    """Definition of the isomer shift (δ) parameter for Mössbauer spectra.

    The isomer shift is a measure of the electron density at the nucleus.
    Typically reported in mm/s.
    """

    max: float | None = Field(
        default=None,
        description="Maximum isomer shift value (mm/s).",
    )
    min: float | None = Field(
        default=None,
        description="Minimum isomer shift value (mm/s).",
    )
    vary: bool = Field(
        default=True,
        description="Vary the isomer shift parameter during fitting.",
    )
    value: float | None = Field(
        default=None,
        description="Initial isomer shift value (mm/s).",
    )
    expr: str | None = Field(default=None, description=__description__)


class FwhmlAPI(BaseModel):
    """Definition of the FWHM Lorentzian of the models distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Full Width Half Maximum of the Lorentzian Distribution.",
    )
    min: float | None = Field(
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


class QuadrupoleSplittingAPI(BaseModel):
    """Definition of the Quadrupole Splitting parameter for Mössbauer distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Quadrupole Splitting value.",
    )
    min: float | None = Field(
        default=None,
        description="Minimum Quadrupole Splitting value.",
    )
    vary: bool = Field(
        default=True,
        description="Vary the Quadrupole Splitting parameter during fitting.",
    )
    value: float | None = Field(
        default=None,
        description="Initial Quadrupole Splitting value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class HyperfineFieldAPI(BaseModel):
    """Definition of the Hyperfine Field parameter for Mössbauer distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Hyperfine Field value.",
    )
    min: float | None = Field(
        default=None,
        description="Minimum Hyperfine Field value.",
    )
    vary: bool = Field(
        default=True,
        description="Vary the Hyperfine Field parameter during fitting.",
    )
    value: float | None = Field(
        default=None,
        description="Initial Hyperfine Field value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class BackgroundAPI(BaseModel):
    """Definition of the Background parameter for Mössbauer distributions."""

    max: float | None = Field(
        default=None,
        description="Maximum Background value.",
    )
    min: float | None = Field(
        default=None,
        description="Minimum Background value.",
    )
    vary: bool = Field(
        default=True,
        description="Vary the Background parameter during fitting.",
    )
    value: float | None = Field(
        default=None,
        description="Initial Background value.",
    )
    expr: str | None = Field(default=None, description=__description__)


class MoessbauerSingletAPI(BaseModel):
    r"""Definition of the Mössbauer Singlet distribution.

    A singlet is observed when the nucleus experiences no electric field gradient
    and no magnetic hyperfine field. It is characterized by a single absorption line
    at the isomer shift position.

    The mathematical expression for a Mössbauer singlet is:

    $$I(v) = I_0 - A \\cdot L(v-\\delta; \\Gamma)$$

    where:
    - $I(v)$ is the measured intensity at velocity $v$
    - $I_0$ is the background level
    - $A$ is the amplitude
    - $\\delta$ is the isomer shift
    - $\\Gamma$ is the linewidth (FWHM)
    - $L$ is the Lorentzian function
    """

    amplitude: AmplitudeAPI = AmplitudeAPI()
    isomershift: IsomerShiftAPI = IsomerShiftAPI()
    fwhml: FwhmlAPI = FwhmlAPI()
    background: BackgroundAPI = BackgroundAPI()


class MoessbauerDoubletAPI(BaseModel):
    r"""Definition of the Mössbauer Doublet distribution.

    A doublet is observed when the nucleus experiences an electric field gradient
    but no magnetic field. It is characterized by two absorption lines
    symmetrically positioned around the isomer shift position.

    The mathematical expression for a Mössbauer doublet is:

    $$
    I(v) = I_0 - \frac{A}{2} \cdot L(v-\delta-\frac{\Delta E_Q}{2}; \Gamma)
      - \frac{A}{2} \cdot L(v-\delta+\frac{\Delta E_Q}{2}; \Gamma)
    $$

    where:
    - $I(v)$ is the measured intensity at velocity $v$
    - $I_0$ is the background level
    - $A$ is the amplitude
    - $\delta$ is the isomer shift
    - $\Delta E_Q$ is the quadrupole splitting
    - $\Gamma$ is the linewidth (FWHM)
    - $L$ is the Lorentzian function
    """

    amplitude: AmplitudeAPI = AmplitudeAPI()
    isomershift: IsomerShiftAPI = IsomerShiftAPI()
    fwhml: FwhmlAPI = FwhmlAPI()
    quadrupolesplitting: QuadrupoleSplittingAPI = QuadrupoleSplittingAPI()
    background: BackgroundAPI = BackgroundAPI()


class MoessbauerSextetAPI(BaseModel):
    r"""Definition of the Mössbauer Sextet distribution.

    A sextet is observed when the nucleus experiences a magnetic field.
    It is characterized by six absorption lines due to magnetic splitting
    of the nuclear energy levels.

    The mathematical expression for a simplified Mössbauer sextet is:

    $$
    I(v) = I_0 - \sum_{i=1}^{6} \frac{A}{6} \cdot
    L(v-\delta-p_i \cdot B_{hf} + \frac{\Delta E_Q}{2}; \Gamma)
    $$

    where:
    - $I(v)$ is the measured intensity at velocity $v$
    - $I_0$ is the background level
    - $A$ is the amplitude
    - $\delta$ is the isomer shift
    - $B_{hf}$ is the hyperfine field
    - $\Delta E_Q$ is the quadrupole splitting
    - $p_i$ are the relative positions of the six lines
    - $\Gamma$ is the linewidth (FWHM)
    - $L$ is the Lorentzian function
    """

    amplitude: AmplitudeAPI = AmplitudeAPI()
    isomershift: IsomerShiftAPI = IsomerShiftAPI()
    fwhml: FwhmlAPI = FwhmlAPI()
    hyperfinefield: HyperfineFieldAPI = HyperfineFieldAPI()
    quadrupolesplitting: QuadrupoleSplittingAPI = QuadrupoleSplittingAPI()
    background: BackgroundAPI = BackgroundAPI()


class MoessbauerOctetAPI(BaseModel):
    r"""Definition of the Mössbauer Octet distribution.

    An octet is observed for magnetic materials with higher nuclear spin states,
    resulting in eight absorption lines due to complex hyperfine interactions.

    The mathematical expression for a simplified Mössbauer octet is:

    $$
    I(v) = I_0 - \sum_{i=1}^{8} \frac{A}{8} \cdot L(v-\delta-p_i \cdot B_{hf} +
    \frac{\Delta E_Q}{2}; \Gamma)
    $$

    where:
    - $I(v)$ is the measured intensity at velocity $v$
    - $I_0$ is the background level
    - $A$ is the amplitude
    - $\delta$ is the isomer shift
    - $B_{hf}$ is the hyperfine field
    - $\Delta E_Q$ is the quadrupole splitting
    - $p_i$ are the relative positions of the eight lines
    - $\Gamma$ is the linewidth (FWHM)
    - $L$ is the Lorentzian function
    """

    amplitude: AmplitudeAPI = AmplitudeAPI()
    isomershift: IsomerShiftAPI = IsomerShiftAPI()
    fwhml: FwhmlAPI = FwhmlAPI()
    hyperfinefield: HyperfineFieldAPI = HyperfineFieldAPI()
    quadrupolesplitting: QuadrupoleSplittingAPI = QuadrupoleSplittingAPI()
    background: BackgroundAPI = BackgroundAPI()


class MagneticAngles(BaseModel):
    """Parameters for magnetic field orientation."""

    theta: float = Field(default=0.0, description="Angle in radians")
    phi: float = Field(default=0.0, description="Angle in radians")


class EfgParameters(BaseModel):
    """Parameters for electric field gradient (EFG)."""

    vzz: float = Field(
        default=1e21,
        description="Principal component of EFG tensor (V/m²)",
    )
    eta: float = Field(default=0.0, description="Asymmetry parameter (dimensionless)")
    vary_vzz: bool = Field(default=False, description="Whether to vary vzz in fitting")
    vary_eta: bool = Field(default=False, description="Whether to vary eta in fitting")


class TemperatureParameters(BaseModel):
    """Parameters for temperature-dependent effects."""

    value: float = Field(default=300.0, description="Temperature in K")
    sod_shift: float = Field(
        default=0.0,
        description="Second-order Doppler shift (mm/s)",
    )
    vary_temp: bool = Field(
        default=False,
        description="Whether to vary temperature in fitting",
    )
    vary_sod: bool = Field(
        default=False,
        description="Whether to vary SOD shift in fitting",
    )


class DynamicParameter(BaseModel):
    """Parameter with bounds and variability for fitting."""

    value: float
    vary: bool = Field(
        default=False,
        description="Whether to vary this parameter in fitting",
    )
    min: float | None = Field(default=None, description="Minimum allowed value")
    max: float | None = Field(default=None, description="Maximum allowed value")

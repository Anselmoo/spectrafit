"""Physical constants for use across spectrafit models."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import Field


class MoessbauerConstants(BaseModel):
    """Physical constants specific to Mössbauer spectroscopy."""

    # General nuclear physics constants
    nuclear_magneton: float = Field(
        default=5.0508e-27,
        description="Nuclear magneton in J/T",
    )

    # 57Fe specific constants
    gamma_57fe: float = Field(
        default=8.67e-9,
        description="Natural linewidth of 57Fe in eV",
    )
    g_factor_57fe: float = Field(
        default=0.18,
        description="g-factor for 57Fe excited state",
    )
    quadrupole_moment_57fe: float = Field(
        default=0.16e-28,
        description="Quadrupole moment for 57Fe in m²",
    )
    conversion_mm_s_to_ev: float = Field(
        default=4.8e-8,
        description="Conversion from mm/s to eV for 57Fe (approx)",
    )
    ev_to_mm_s: float = Field(
        default=1 / 4.8e-8,
        description="Convert energy in eV to velocity in mm/s",
    )

    # Thresholds for model calculations
    min_efg_threshold: float = Field(
        default=1e20,
        description="Minimum EFG value for octet splitting in V/m²",
    )
    min_field_threshold: float = Field(
        default=1.0,
        description="Minimum magnetic field value for octet splitting in T",
    )
    min_variance_threshold: float = Field(
        default=1e-6,
        description="Minimum variance for fitting in eV²",
    )


# Create a singleton instance for easy import
moessbauer_constants = MoessbauerConstants()

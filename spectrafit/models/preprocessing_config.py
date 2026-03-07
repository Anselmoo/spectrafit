"""PreprocessingConfig — data pre-processing configuration.

Maps to the ``[preprocessing]`` section of the v2 input TOML.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class PreprocessingConfig(BaseModel):
    r"""Validated configuration for the data pre-processing step.

    Maps to the ``[preprocessing]`` section in the v2 input TOML::

        [preprocessing]
        energy_start = 280.0
        energy_stop  = 295.0
        smooth       = 0
        shift        = 0.0
        oversampling = false

    All fields have safe no-op defaults so the section can be omitted entirely.

    Attributes:
        energy_start: Lower bound of the energy range to fit (``None`` = no crop).
        energy_stop: Upper bound of the energy range to fit (``None`` = no crop).
        smooth: Box-car smoothing window size (0 = disabled).
        shift: Constant energy shift applied before fitting (0.0 = none).
        oversampling: Whether to 5x oversample the data before fitting.
    """

    model_config = ConfigDict(extra="forbid")

    energy_start: float | None = Field(
        default=None,
        description="Lower bound of the energy range to fit; None disables cropping",
    )
    energy_stop: float | None = Field(
        default=None,
        description="Upper bound of the energy range to fit; None disables cropping",
    )
    smooth: int = Field(
        default=0,
        ge=0,
        description="Box-car smoothing window size; 0 disables smoothing",
    )
    shift: float = Field(
        default=0.0,
        description="Constant energy shift applied before fitting",
    )
    oversampling: bool = Field(
        default=False,
        description="When True, 5x oversample the spectrum before fitting",
    )

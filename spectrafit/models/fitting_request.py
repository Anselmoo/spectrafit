"""Typed request model for pipeline execution."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from spectrafit.core.fitting_config import UnifiedFittingConfig  # noqa: TC001
from spectrafit.models.output_config import OutputConfig


class FittingRequest(BaseModel):
    """Canonical pipeline request carrying fit config plus runtime output options.

    Attributes:
        config: Validated fitting configuration consumed by the fitting engine.
        output: Runtime output settings for reporting/export side effects.
    """

    model_config = ConfigDict(extra="forbid")

    config: UnifiedFittingConfig = Field(
        description="Validated fitting configuration for one pipeline execution",
    )
    output: OutputConfig = Field(
        default_factory=OutputConfig,
        description="Runtime output settings for reporting and export behavior",
    )

    @classmethod
    def from_config(
        cls,
        config: UnifiedFittingConfig,
        *,
        output: OutputConfig | None = None,
    ) -> FittingRequest:
        """Build a request from validated config plus optional output overrides."""
        return cls(
            config=config,
            output=output if output is not None else OutputConfig(),
        )

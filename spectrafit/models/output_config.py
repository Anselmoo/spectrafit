"""OutputConfig — CLI/notebook runtime output configuration.

This model is *never* passed to the fitting engine.  It holds the three
output-related knobs that users control via CLI flags or notebook parameters.
"""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class OutputConfig(BaseModel):
    """Runtime output configuration for CLI and notebook interfaces.

    !!! note "Not a fitting parameter"
        ``OutputConfig`` controls how results are saved and displayed.
        It is intentionally separate from ``UnifiedFittingConfig``
        and is **never** forwarded to the fitting engine.

    Attributes:
        outfile: Base filename (without extension) for exported results.
        noplot: When ``True``, suppress all plot output.
        verbose: Verbosity level — 0 = silent, 1 = table, 2 = dict.
    """

    model_config = ConfigDict(extra="forbid")

    outfile: str = Field(
        default="spectrafit_results",
        description="Base filename (no extension) for exported results",
    )
    noplot: bool = Field(
        default=False,
        description="Suppress plot output when True",
    )
    verbose: int = Field(
        default=1,
        ge=0,
        le=2,
        description="Verbosity level: 0=silent, 1=table, 2=dict",
    )

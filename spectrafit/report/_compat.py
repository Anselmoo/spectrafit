"""Runtime compatibility helpers for the frozen legacy report package."""

from __future__ import annotations

import warnings


LEGACY_REPORT_DEPRECATION_MESSAGE = (
    "spectrafit.report is a frozen legacy compatibility layer in v2.x and "
    "will be removed in v3.0.0; migrate runtime report rendering to "
    "spectrafit.reporting."
)


def warn_legacy_report_import() -> None:
    """Emit the runtime deprecation signal for legacy report imports."""
    warnings.warn(
        LEGACY_REPORT_DEPRECATION_MESSAGE,
        FutureWarning,
        stacklevel=2,
    )


__all__ = [
    "LEGACY_REPORT_DEPRECATION_MESSAGE",
    "warn_legacy_report_import",
]

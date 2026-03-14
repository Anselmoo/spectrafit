"""CLI-owned status helpers for version and fit lifecycle messages."""

from __future__ import annotations

from spectrafit import __version__


class CliStatus:
    """Own lightweight CLI status text without depending on legacy report code."""

    def version(self) -> str:
        """Return the current SpectraFit version string shown by the CLI."""
        return f"Currently used version is: {__version__}"

    def start(self) -> None:
        """Placeholding before a fit run starts.

        Intentionally a no-op to preserve current user-visible behavior.
        """

    def end(self) -> None:
        """Placeholding after a fit run completes.

        Intentionally a no-op to preserve current user-visible behavior.
        """


cli_status = CliStatus()

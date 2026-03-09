"""Jupyter launcher for SpectraFit.

Provides the ``launch()`` function for starting Jupyter Lab with
SpectraFit integration. Called by both the ``spectrafit jupyter`` CLI
command and the ``spectrafit-jupyter`` entry-point script.
"""

from __future__ import annotations


def launch() -> None:
    """Launch Jupyter Lab with SpectraFit integration.

    Raises:
        ImportError: If the ``[jupyter]`` optional dependencies are not installed.

    """
    try:
        from spectrafit.app.app import jupyter as jupyter_app  # noqa: PLC0415

        jupyter_app()
    except ImportError as exc:
        msg = (
            "Jupyter dependencies are not installed. "
            "Install with: pip install spectrafit[jupyter]"
        )
        raise ImportError(msg) from exc

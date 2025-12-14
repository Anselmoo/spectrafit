"""SpectraFit main entry point.

This module provides backward compatibility with legacy code while delegating
to the modern CLI implementation in spectrafit.cli.main.

For the full CLI with subcommands, use: from spectrafit.cli.main import app
"""

from __future__ import annotations

from typing import Any

# Import modern CLI app
from spectrafit.cli.main import app


def main() -> None:
    """Entry point for spectrafit command.

    Delegates to the modern CLI implementation in spectrafit.cli.main.
    """
    app()


def command_line_runner(args: dict[str, Any] | None = None) -> None:
    """Legacy entry point for backward compatibility.

    This function maintains backward compatibility with code that used the old
    command_line_runner interface. New code should use the CLI directly.

    Args:
        args: Optional dictionary of arguments. If provided, runs in programmatic
            mode. If None, runs the CLI normally.

    Note:
        Programmatic mode (args != None) is deprecated. Use the API classes
        directly or the pipeline functions in spectrafit.core.pipeline instead.
    """
    if args is not None:
        # Programmatic mode: delegate to fitting workflow
        # Import here to avoid circular dependencies
        from spectrafit.core import SaveResult  # noqa: PLC0415
        from spectrafit.core.pipeline import fitting_routine_pipeline  # noqa: PLC0415
        from spectrafit.plotting import PlotSpectra  # noqa: PLC0415
        from spectrafit.report import PrintingStatus  # noqa: PLC0415

        status = PrintingStatus()
        status.welcome()
        status.start()

        # Run fitting
        df_result, processed_args = fitting_routine_pipeline(args)
        PlotSpectra(df=df_result, args=processed_args)()
        SaveResult(df=df_result, args=processed_args)()

        status.end()
        status.thanks()
        status.credits()
    else:
        # CLI mode: delegate to modern CLI
        app()


# Legacy app export for backward compatibility
# Deprecated: Use spectrafit.cli.main.app instead
__all__ = ["app", "command_line_runner", "main"]


if __name__ == "__main__":
    main()

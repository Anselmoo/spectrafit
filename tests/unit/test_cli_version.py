"""Unit tests for CLI-owned version output."""

from __future__ import annotations

import pytest

from spectrafit import __version__
from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.unit
def test_version_option_uses_cli_owned_version_output() -> None:
    """CLI version flag should render the current package version text."""
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output == f"Currently used version is: {__version__}\n"


@pytest.mark.unit
def test_short_version_option_uses_cli_owned_version_output() -> None:
    """Short CLI version flag should render the current package version text."""
    result = runner.invoke(app, ["-v"])

    assert result.exit_code == 0
    assert result.output == f"Currently used version is: {__version__}\n"

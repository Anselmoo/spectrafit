"""Unit tests for CLI callback banner scope behavior."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.unit
class TestCliMainBannerScope:
    """Validate where the startup banner is rendered by the CLI callback."""

    def test_banner_shows_on_bare_invocation(self) -> None:
        with patch("spectrafit.cli.banner.render_startup_panel") as render_banner:
            result = runner.invoke(app, [])
        assert result.exit_code == 0
        render_banner.assert_called_once()

    def test_root_short_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["-h"])
        assert result.exit_code == 0

    @pytest.mark.parametrize("command", ["fit", "init", "jupyter", "plugins"])
    def test_banner_shows_for_interactive_commands(self, command: str) -> None:
        with patch("spectrafit.cli.banner.render_startup_panel") as render_banner:
            result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0
        render_banner.assert_called_once()

    @pytest.mark.parametrize("command", ["report", "validate", "convert", "new-config"])
    def test_banner_suppressed_for_noninteractive_commands(self, command: str) -> None:
        with patch("spectrafit.cli.banner.render_startup_panel") as render_banner:
            result = runner.invoke(app, [command, "--help"])
        assert result.exit_code == 0
        render_banner.assert_not_called()

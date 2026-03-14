"""Unit tests for the Rich startup banner (Phase 4)."""

from __future__ import annotations

from io import StringIO

import pytest

from rich.console import Console
from spectrafit.cli.banner import _env_label
from spectrafit.cli.banner import render_startup_panel
from spectrafit.models.fitting_context import EnvironmentMode


class TestEnvLabel:
    """Tests for _env_label colour helper."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "env",
        [EnvironmentMode.CLI, EnvironmentMode.NOTEBOOK, EnvironmentMode.API],
    )
    def test_returns_valid_colour_string(self, env: EnvironmentMode) -> None:
        """_env_label returns a plain Rich colour name, not a markup string."""
        label = _env_label(env)
        # Must be a non-empty string usable as a Rich style (no angle-bracket markup)
        assert isinstance(label, str)
        assert len(label) > 0
        assert "<" not in label
        assert "[" not in label

    @pytest.mark.unit
    def test_cli_is_green(self) -> None:
        label = _env_label(EnvironmentMode.CLI)
        assert "green" in label

    @pytest.mark.unit
    def test_notebook_is_magenta(self) -> None:
        label = _env_label(EnvironmentMode.NOTEBOOK)
        assert "magenta" in label

    @pytest.mark.unit
    def test_api_is_yellow(self) -> None:
        label = _env_label(EnvironmentMode.API)
        assert "yellow" in label


class TestRenderStartupPanel:
    """Tests for render_startup_panel TTY-gate logic and content."""

    @pytest.mark.unit
    def test_no_output_on_non_tty(self) -> None:
        """Panel should be suppressed when stdout is not a terminal."""
        buf = StringIO()
        console = Console(file=buf, force_terminal=False)
        render_startup_panel(console, EnvironmentMode.CLI)
        assert buf.getvalue() == ""

    @pytest.mark.unit
    def test_renders_on_forced_terminal(self) -> None:
        """Panel renders when console.is_terminal is True."""
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=100)
        render_startup_panel(console, EnvironmentMode.CLI)
        output = buf.getvalue()
        assert len(output) > 0

    @pytest.mark.unit
    def test_output_contains_spectrafit(self) -> None:
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=100)
        render_startup_panel(console, EnvironmentMode.CLI)
        output = buf.getvalue()
        assert "SpectraFit" in output

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "env",
        [EnvironmentMode.CLI, EnvironmentMode.NOTEBOOK, EnvironmentMode.API],
    )
    def test_renders_for_each_env(self, env: EnvironmentMode) -> None:
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=100)
        render_startup_panel(console, env)
        assert len(buf.getvalue()) > 0

    @pytest.mark.unit
    def test_auto_detect_env_when_none(self) -> None:
        """Passing env=None triggers auto-detection without error."""
        buf = StringIO()
        console = Console(file=buf, force_terminal=True, width=100)
        render_startup_panel(console, None)
        assert "SpectraFit" in buf.getvalue()

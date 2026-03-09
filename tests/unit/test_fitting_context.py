"""Unit tests for FittingContext, FittingMode, EnvironmentMode and detect_environment."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from spectrafit.models.fitting_context import EnvironmentMode
from spectrafit.models.fitting_context import FittingContext
from spectrafit.models.fitting_context import detect_environment


class TestEnvironmentMode:
    """Tests for EnvironmentMode enum."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("cli", EnvironmentMode.CLI),
            ("notebook", EnvironmentMode.NOTEBOOK),
            ("api", EnvironmentMode.API),
        ],
    )
    def test_from_string(self, value: str, expected: EnvironmentMode) -> None:
        assert EnvironmentMode(value) == expected

    @pytest.mark.unit
    def test_is_str_subclass(self) -> None:
        assert isinstance(EnvironmentMode.CLI, str)
        assert EnvironmentMode.CLI == "cli"

    @pytest.mark.unit
    def test_all_values_unique(self) -> None:
        values = [m.value for m in EnvironmentMode]
        assert len(values) == len(set(values))


class TestDetectEnvironment:
    """Tests for detect_environment()."""

    @pytest.mark.unit
    def test_returns_environment_mode_instance(self) -> None:
        result = detect_environment()
        assert isinstance(result, EnvironmentMode)

    @pytest.mark.unit
    def test_detects_notebook_when_ipython_kernel_active(self) -> None:
        mock_ipython = MagicMock()
        mock_get_ipython = MagicMock(return_value=mock_ipython)
        mock_ipython_module = MagicMock()
        mock_ipython_module.get_ipython = mock_get_ipython

        with patch.dict("sys.modules", {"IPython": mock_ipython_module}):
            result = detect_environment()

        assert result == EnvironmentMode.NOTEBOOK

    @pytest.mark.unit
    def test_detects_api_when_stdin_not_tty(self) -> None:
        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = False
            with patch.dict("sys.modules", {"IPython": None}, clear=False):
                # Remove IPython to force CLI/API path
                import builtins
                original_import = builtins.__import__

                def import_without_ipython(name: str, *args: object, **kwargs: object) -> object:
                    if name == "IPython":
                        raise ImportError("no IPython")
                    return original_import(name, *args, **kwargs)

                builtins.__import__ = import_without_ipython
                try:
                    result = detect_environment()
                    assert result == EnvironmentMode.API
                finally:
                    builtins.__import__ = original_import

    @pytest.mark.unit
    def test_detects_cli_when_stdin_is_tty(self) -> None:
        import builtins

        original_import = builtins.__import__

        def import_without_ipython(name: str, *args: object, **kwargs: object) -> object:
            if name == "IPython":
                raise ImportError("no IPython")
            return original_import(name, *args, **kwargs)

        with patch("sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            builtins.__import__ = import_without_ipython
            try:
                result = detect_environment()
                assert result == EnvironmentMode.CLI
            finally:
                builtins.__import__ = original_import


class TestFittingContextEnvironmentField:
    """Test that FittingContext carries the environment field."""

    @pytest.mark.unit
    def test_default_environment_is_set(self) -> None:
        ctx = FittingContext()
        assert isinstance(ctx.environment, EnvironmentMode)

    @pytest.mark.unit
    def test_explicit_environment(self) -> None:
        ctx = FittingContext(environment=EnvironmentMode.NOTEBOOK)
        assert ctx.environment == EnvironmentMode.NOTEBOOK

    @pytest.mark.unit
    def test_frozen_context_raises_on_mutation(self) -> None:
        ctx = FittingContext(environment=EnvironmentMode.CLI)
        with pytest.raises(Exception):
            ctx.environment = EnvironmentMode.API  # type: ignore[misc]

    @pytest.mark.unit
    def test_serialises_environment(self) -> None:
        ctx = FittingContext(environment=EnvironmentMode.API)
        data = ctx.model_dump()
        assert data["environment"] == "api"

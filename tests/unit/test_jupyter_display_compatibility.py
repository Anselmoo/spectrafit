"""Compatibility tests for notebook-facing Jupyter display surfaces."""

from __future__ import annotations

import builtins
import importlib
import sys

from types import ModuleType

import pandas as pd
import pytest


DISPLAY_MODULE = "spectrafit.jupyter.display"


def _import_display_module_without_optional_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> ModuleType:
    """Import the display module while simulating missing optional extras."""
    original_import = builtins.__import__
    sys.modules.pop(DISPLAY_MODULE, None)

    def _fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name in {"dtale", "itables"}:
            msg = f"missing optional dependency: {name}"
            raise ImportError(msg)
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    return importlib.import_module(DISPLAY_MODULE)


@pytest.mark.unit
def test_display_module_imports_without_optional_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Importing the notebook display surface should not require optional extras."""
    display_module = _import_display_module_without_optional_backends(monkeypatch)

    assert display_module.DataFrameDisplay is not None


@pytest.mark.unit
def test_regular_and_markdown_display_do_not_touch_optional_backends(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-interactive display modes should not attempt optional imports."""
    display_module = importlib.import_module(DISPLAY_MODULE)
    frame = pd.DataFrame({"energy": [1.0], "signal": [2.0]})
    calls: list[tuple[str, object]] = []
    original_import_module = display_module.importlib.import_module

    monkeypatch.setattr(
        display_module,
        "display",
        lambda df: calls.append(("regular", df.copy())),
    )
    monkeypatch.setattr(
        display_module,
        "display_markdown",
        lambda markdown, raw=True: calls.append(("markdown", (markdown, raw))),
    )

    def _guard_optional_imports(name: str) -> ModuleType:
        if name in {"dtale", "itables"}:
            msg = f"unexpected optional import: {name}"
            raise AssertionError(msg)
        return original_import_module(name)

    monkeypatch.setattr(
        display_module.importlib,
        "import_module",
        _guard_optional_imports,
    )

    display_module.DataFrameDisplay().df_display(frame, mode="regular")
    display_module.DataFrameDisplay().df_display(frame, mode="markdown")

    assert calls[0][0] == "regular"
    pd.testing.assert_frame_equal(calls[0][1], frame)
    assert calls[1] == ("markdown", (frame.to_markdown(), True))


@pytest.mark.unit
def test_interactive_display_reports_missing_itables_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Interactive display should fail with a helpful optional dependency error."""
    display_module = importlib.import_module(DISPLAY_MODULE)
    frame = pd.DataFrame({"energy": [1.0], "signal": [2.0]})
    original_import_module = display_module.importlib.import_module

    def _fake_import_module(name: str) -> ModuleType:
        if name == "itables":
            msg = "no module named 'itables'"
            raise ImportError(msg)
        return original_import_module(name)

    monkeypatch.setattr(
        display_module.importlib,
        "import_module",
        _fake_import_module,
    )

    with pytest.raises(
        ImportError,
        match="interactive display requires optional dependency 'itables'",
    ):
        display_module.DataFrameDisplay.interactive_display(frame)


@pytest.mark.unit
def test_dtale_display_reports_missing_dtale_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dtale display should fail with a helpful optional dependency error."""
    display_module = importlib.import_module(DISPLAY_MODULE)
    frame = pd.DataFrame({"energy": [1.0], "signal": [2.0]})
    original_import_module = display_module.importlib.import_module

    def _fake_import_module(name: str) -> ModuleType:
        if name == "dtale":
            msg = "no module named 'dtale'"
            raise ImportError(msg)
        return original_import_module(name)

    monkeypatch.setattr(
        display_module.importlib,
        "import_module",
        _fake_import_module,
    )

    with pytest.raises(
        ImportError,
        match="dtale display requires optional dependency 'dtale'",
    ):
        display_module.DataFrameDisplay.dtale_display(frame)


@pytest.mark.unit
def test_plugins_notebook_reexports_notebook_surface() -> None:
    """Legacy notebook import path should still resolve to the live notebook class."""
    import warnings

    from spectrafit.jupyter.core import SpectraFitNotebook
    from spectrafit.plugins import notebook as notebook_module

    with pytest.warns(FutureWarning, match=r"spectrafit\.plugins\.notebook"):
        compat_notebook = notebook_module.SpectraFitNotebook

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from spectrafit.plugins.notebook import SpectraFitNotebook as CompatNotebook

    assert compat_notebook is SpectraFitNotebook
    assert CompatNotebook is SpectraFitNotebook
    future_warnings = [
        warning for warning in caught if issubclass(warning.category, FutureWarning)
    ]
    assert future_warnings

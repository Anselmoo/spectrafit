"""Unit tests for the top-level jupyter CLI command."""

from __future__ import annotations

import builtins
import sys

from pathlib import Path
from types import ModuleType
from types import SimpleNamespace

import pytest

from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.unit
def test_jupyter_command_reports_missing_notebook_before_launch(tmp_path: Path) -> None:
    missing_notebook = tmp_path / "missing.ipynb"

    result = runner.invoke(app, ["jupyter", str(missing_notebook)])

    assert result.exit_code == 1
    assert "Notebook not found" in result.output


def _install_fake_jupyter_module(
    monkeypatch: pytest.MonkeyPatch,
    callback: object,
) -> None:
    module = ModuleType("spectrafit.app.app")
    module.jupyter = callback
    monkeypatch.setitem(sys.modules, "spectrafit.app.app", module)


@pytest.mark.unit
def test_jupyter_command_uses_project_default_notebook_when_omitted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    opened: dict[str, Path | None] = {"path": None}
    notebook = tmp_path / "configured.ipynb"
    notebook.write_text("{}", encoding="utf-8")
    (tmp_path / "spectrafit.toml").write_text("", encoding="utf-8")

    def _launch(*, notebook_file: Path | None) -> None:
        opened["path"] = notebook_file

    project_module = ModuleType("spectrafit.models.project_config")

    class FakeProjectConfig:
        @staticmethod
        def from_toml(_path: Path) -> object:
            return SimpleNamespace(
                project=SimpleNamespace(
                    files=SimpleNamespace(default_notebook="configured.ipynb")
                )
            )

    project_module.ProjectConfig = FakeProjectConfig
    monkeypatch.setitem(sys.modules, "spectrafit.models.project_config", project_module)
    _install_fake_jupyter_module(monkeypatch, _launch)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["jupyter"])

    assert result.exit_code == 0, result.output
    assert opened["path"] == Path("configured.ipynb")
    assert "Opening notebook" in result.output


@pytest.mark.unit
def test_jupyter_command_uses_getting_started_fallback_when_present(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    opened: dict[str, Path | None] = {"path": None}
    fallback = tmp_path / "spectrafit_getting_started.ipynb"
    fallback.write_text("{}", encoding="utf-8")

    def _launch(*, notebook_file: Path | None) -> None:
        opened["path"] = notebook_file

    _install_fake_jupyter_module(monkeypatch, _launch)
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["jupyter"])

    assert result.exit_code == 0, result.output
    assert opened["path"] == Path("spectrafit_getting_started.ipynb")
    assert "Launching Jupyter Lab" in result.output


@pytest.mark.unit
def test_jupyter_command_reports_missing_jupyter_dependency(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    notebook = tmp_path / "analysis.ipynb"
    notebook.write_text("{}", encoding="utf-8")
    original_import = builtins.__import__

    def _fake_import(
        name: str,
        globals_: dict[str, object] | None = None,
        locals_: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "spectrafit.app.app":
            msg = "no jupyter support"
            raise ImportError(msg)
        return original_import(name, globals_, locals_, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", _fake_import)

    result = runner.invoke(app, ["jupyter", str(notebook)])

    assert result.exit_code == 1
    assert "Jupyter dependencies are not installed" in result.output


@pytest.mark.unit
def test_jupyter_command_reports_unexpected_launch_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    notebook = tmp_path / "analysis.ipynb"
    notebook.write_text("{}", encoding="utf-8")

    def _launch(*, notebook_file: Path | None) -> None:
        msg = f"boom: {notebook_file}"
        raise RuntimeError(msg)

    _install_fake_jupyter_module(monkeypatch, _launch)

    result = runner.invoke(app, ["jupyter", str(notebook)])

    assert result.exit_code == 1
    assert "Unexpected error launching Jupyter" in result.output

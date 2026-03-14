"""Unit tests for the validate CLI command."""

from __future__ import annotations

import importlib

from pathlib import Path
from types import SimpleNamespace

import pytest

from spectrafit.cli.main import app
from typer.testing import CliRunner


runner = CliRunner()
validate_module = importlib.import_module("spectrafit.cli.commands.validate")


def _runtime_with_result(config: object) -> object:
    return SimpleNamespace(
        resolve_config_path=lambda input_file: input_file,
        load_fitting_config=lambda _path: config,
    )


@pytest.mark.unit
def test_validate_verbose_reports_configuration_details(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.toml"
    config_path.write_text("", encoding="utf-8")
    cfg = SimpleNamespace(
        components=["p1", "bg"],
        data=SimpleNamespace(infile=tmp_path / "data.csv"),
        preprocessing=SimpleNamespace(energy_start=-1.0, energy_stop=2.0),
    )
    monkeypatch.setattr(
        validate_module,
        "get_cli_runtime",
        lambda _ctx: _runtime_with_result(cfg),
    )
    monkeypatch.setattr(validate_module, "_validate_referenced_input_data", lambda _cfg: None)

    result = runner.invoke(app, ["validate", str(config_path), "--verbose"])

    assert result.exit_code == 0, result.output
    assert "Components: 2" in result.output
    assert "Data file" in result.output
    assert "Energy range: -1.0 - 2.0" in result.output


@pytest.mark.unit
def test_validate_reports_oserror_from_runtime(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.toml"
    config_path.write_text("", encoding="utf-8")
    runtime = SimpleNamespace(
        resolve_config_path=lambda input_file: input_file,
        load_fitting_config=lambda _path: (_ for _ in ()).throw(OSError("permission denied")),
    )
    monkeypatch.setattr(validate_module, "get_cli_runtime", lambda _ctx: runtime)

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 1
    assert "Cannot read file" in result.output


@pytest.mark.unit
def test_validate_reports_generic_validation_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.toml"
    config_path.write_text("", encoding="utf-8")
    runtime = SimpleNamespace(
        resolve_config_path=lambda input_file: input_file,
        load_fitting_config=lambda _path: (_ for _ in ()).throw(ValueError("bad config")),
    )
    monkeypatch.setattr(validate_module, "get_cli_runtime", lambda _ctx: runtime)

    result = runner.invoke(app, ["validate", str(config_path)])

    assert result.exit_code == 1
    assert "Validation error: bad config" in result.output

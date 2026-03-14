"""Unit tests for the fit CLI command."""

from __future__ import annotations

import importlib

from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from spectrafit.cli.main import app
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.models.fitting_request import FittingRequest
from spectrafit.models.split_frame import SplitFrame
from typer.testing import CliRunner


runner = CliRunner()
fit_module = importlib.import_module("spectrafit.cli.commands.fit")


class _StatusPrinter:
    def start(self) -> None:
        return None

    def end(self) -> None:
        return None


class _FakeFitResult:
    def __init__(
        self,
        *,
        is_global: bool = False,
        data_statistic: object | None = None,
    ) -> None:
        self.df = pd.DataFrame({"energy": [0.0], "intensity": [1.0]})
        self.config = SimpleNamespace(context=SimpleNamespace(is_global=is_global))
        self.data_statistic = data_statistic or SplitFrame.empty()
        self.fit_result = {"ok": True}

    def to_fit_result(self) -> dict[str, bool]:
        return self.fit_result


def _runtime_with_config(config: object) -> object:
    def _resolve_config_path(input_file: object) -> Path:
        return Path(str(input_file))

    def _load_fitting_config(_path: object) -> object:
        return config

    return SimpleNamespace(
        status_printer=_StatusPrinter(),
        resolve_config_path=_resolve_config_path,
        load_fitting_config=_load_fitting_config,
    )


def _build_fit_config() -> UnifiedFittingConfig:
    return UnifiedFittingConfig.from_dict(
        {
            "components": [
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "vary": True},
                        "center": {"value": 0.0, "vary": True},
                        "fwhmg": {"value": 0.7, "vary": True},
                    },
                }
            ],
            "column": {"x": "energy", "y": "intensity"},
            "context": {"mode": "standard"},
        }
    )


def _fake_fitting_routine_pipeline(*_args: object, **_kwargs: object) -> _FakeFitResult:
    return _FakeFitResult()


def _fake_plot_spectra(**_kwargs: object) -> object:
    def _render() -> None:
        return None

    return _render


def _fake_write_cli_outputs(**_kwargs: object) -> None:
    return None


def _fail_if_confirm_called(*_args: object, **_kwargs: object) -> bool:
    msg = "confirm should not be called"
    raise AssertionError(msg)


@pytest.mark.unit
def test_fit_is_non_interactive_by_default(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.json"
    config_path.write_text("{}", encoding="utf-8")
    fake_config = _build_fit_config()

    monkeypatch.setattr(
        fit_module,
        "get_cli_runtime",
        lambda _ctx: _runtime_with_config(fake_config),
    )
    monkeypatch.setattr(
        fit_module,
        "fitting_routine_pipeline",
        _fake_fitting_routine_pipeline,
    )
    monkeypatch.setattr(fit_module, "PlotSpectra", _fake_plot_spectra)
    monkeypatch.setattr(
        fit_module,
        "write_cli_outputs",
        _fake_write_cli_outputs,
    )
    monkeypatch.setattr(fit_module.typer, "confirm", _fail_if_confirm_called)

    result = runner.invoke(app, ["fit", str(config_path)])

    assert result.exit_code == 0, result.output
    assert "fit again" not in result.output.lower()


@pytest.mark.unit
def test_fit_interactive_mode_requires_explicit_opt_in(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.json"
    config_path.write_text("{}", encoding="utf-8")
    fake_config = _build_fit_config()
    confirm_calls: list[str] = []

    monkeypatch.setattr(
        fit_module,
        "get_cli_runtime",
        lambda _ctx: _runtime_with_config(fake_config),
    )
    monkeypatch.setattr(
        fit_module,
        "fitting_routine_pipeline",
        _fake_fitting_routine_pipeline,
    )
    monkeypatch.setattr(fit_module, "PlotSpectra", _fake_plot_spectra)
    monkeypatch.setattr(
        fit_module,
        "write_cli_outputs",
        _fake_write_cli_outputs,
    )

    def _confirm(prompt: str, *, default: bool) -> bool:
        confirm_calls.append(prompt)
        return False

    monkeypatch.setattr(fit_module.typer, "confirm", _confirm)

    result = runner.invoke(app, ["fit", str(config_path), "--interactive"])

    assert result.exit_code == 0, result.output
    assert confirm_calls == ["Would you like to fit again?"]


@pytest.mark.unit
def test_fit_plots_with_context_and_writes_outputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.json"
    config_path.write_text("{}", encoding="utf-8")
    fake_config = _build_fit_config()
    fake_statistic = SplitFrame.empty()
    plot_calls: list[dict[str, object]] = []
    write_calls: list[dict[str, object]] = []

    monkeypatch.setattr(
        fit_module,
        "get_cli_runtime",
        lambda _ctx: _runtime_with_config(fake_config),
    )

    def _pipeline(*_args: object, **_kwargs: object) -> _FakeFitResult:
        return _FakeFitResult(is_global=True, data_statistic=fake_statistic)

    def _plot_spectra(**kwargs: object) -> object:
        def _render() -> None:
            plot_calls.append(kwargs)

        return _render

    def _write_outputs(**kwargs: object) -> None:
        write_calls.append(kwargs)

    monkeypatch.setattr(fit_module, "fitting_routine_pipeline", _pipeline)
    monkeypatch.setattr(fit_module, "PlotSpectra", _plot_spectra)
    monkeypatch.setattr(fit_module, "write_cli_outputs", _write_outputs)
    monkeypatch.setattr(fit_module.typer, "confirm", _fail_if_confirm_called)

    result = runner.invoke(app, ["fit", str(config_path), "--outfile", "exported"])

    assert result.exit_code == 0, result.output
    assert len(plot_calls) == 1
    plot_config = plot_calls[0]["config"]
    assert plot_config.noplot is False
    assert plot_config.global_fitting is fit_module.FittingMode.GLOBAL
    assert plot_config.data_statistic is fake_statistic
    assert len(write_calls) == 1
    assert write_calls[0]["fit_result"] == {"ok": True}
    assert write_calls[0]["outfile"] == "exported"
    pd.testing.assert_frame_equal(
        write_calls[0]["fit_df"],
        pd.DataFrame({"energy": [0.0], "intensity": [1.0]}),
    )


@pytest.mark.unit
def test_fit_builds_typed_pipeline_request(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.json"
    config_path.write_text("{}", encoding="utf-8")
    fake_config = _build_fit_config()
    captured: dict[str, object] = {}

    monkeypatch.setattr(
        fit_module,
        "get_cli_runtime",
        lambda _ctx: _runtime_with_config(fake_config),
    )

    def _pipeline(*, request: FittingRequest) -> _FakeFitResult:
        captured["request"] = request
        return _FakeFitResult()

    monkeypatch.setattr(fit_module, "fitting_routine_pipeline", _pipeline)
    monkeypatch.setattr(fit_module, "PlotSpectra", _fake_plot_spectra)
    monkeypatch.setattr(fit_module, "write_cli_outputs", _fake_write_cli_outputs)
    monkeypatch.setattr(fit_module.typer, "confirm", _fail_if_confirm_called)

    result = runner.invoke(
        app,
        [
            "fit",
            str(config_path),
            "--outfile",
            "typed-export",
            "--noplot",
            "--verbose",
            "2",
        ],
    )

    assert result.exit_code == 0, result.output
    request = captured["request"]
    assert isinstance(request, FittingRequest)
    assert request.config is fake_config
    assert request.output.outfile == "typed-export"
    assert request.output.noplot is True
    assert request.output.verbose == 2


@pytest.mark.unit
def test_fit_interactive_mode_reruns_and_resets_keyboard_protocol(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "fit.json"
    config_path.write_text("{}", encoding="utf-8")
    fake_config = _build_fit_config()
    pipeline_calls: list[int] = []
    reset_calls: list[str] = []
    confirm_answers = iter([True, False])

    monkeypatch.setattr(
        fit_module,
        "get_cli_runtime",
        lambda _ctx: _runtime_with_config(fake_config),
    )

    def _pipeline(*_args: object, **_kwargs: object) -> _FakeFitResult:
        pipeline_calls.append(1)
        return _FakeFitResult()

    def _confirm(prompt: str, *, default: bool) -> bool:
        assert default is False
        assert prompt == "Would you like to fit again?"
        return next(confirm_answers)

    monkeypatch.setattr(fit_module, "fitting_routine_pipeline", _pipeline)
    monkeypatch.setattr(fit_module, "PlotSpectra", _fake_plot_spectra)
    monkeypatch.setattr(fit_module, "write_cli_outputs", _fake_write_cli_outputs)
    monkeypatch.setattr(fit_module.typer, "confirm", _confirm)

    import spectrafit.cli._types as cli_types

    monkeypatch.setattr(
        cli_types,
        "reset_keyboard_protocol",
        lambda: reset_calls.append("reset"),
    )

    result = runner.invoke(app, ["fit", str(config_path), "--interactive"])

    assert result.exit_code == 0, result.output
    assert len(pipeline_calls) == 2
    assert reset_calls == ["reset", "reset"]

"""Unit tests for the ``spectrafit examples`` CLI surface."""

from __future__ import annotations

from pathlib import Path

import pytest

from spectrafit.cli.main import app
from spectrafit.workflow.validation import ExampleWorkflowSurface
from typer.testing import CliRunner


runner = CliRunner()


@pytest.mark.unit
def test_examples_list_outputs_shipped_example_names(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    examples_module = __import__(
        "spectrafit.cli.commands.examples",
        fromlist=["examples_app"],
    )
    monkeypatch.setattr(
        examples_module,
        "EXAMPLE_INPUTS",
        [
            tmp_path / "basic" / "input.toml",
            tmp_path / "curved-background" / "input.toml",
        ],
    )

    result = runner.invoke(app, ["examples", "list"])

    assert result.exit_code == 0, result.output
    assert "basic" in result.output
    assert "curved-background" in result.output


@pytest.mark.unit
def test_examples_run_delegates_to_shared_workflow_runner(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    examples_module = __import__(
        "spectrafit.cli.commands.examples",
        fromlist=["examples_app"],
    )
    captured: dict[str, object] = {}

    def _fake_run_examples(
        *,
        example_name: str | None = None,
        surface: ExampleWorkflowSurface = ExampleWorkflowSurface.BOTH,
        runner: object | None = None,
        echo: object | None = None,
    ) -> tuple[Path, ...]:
        captured["example_name"] = example_name
        captured["surface"] = surface
        captured["runner"] = runner
        captured["echo"] = echo
        return ()

    monkeypatch.setattr(examples_module, "run_example_workflows", _fake_run_examples)

    result = runner.invoke(app, ["examples", "run", "basic", "--surface", "cli"])

    assert result.exit_code == 0, result.output
    assert captured == {
        "example_name": "basic",
        "surface": ExampleWorkflowSurface.CLI,
        "runner": None,
        "echo": None,
    }

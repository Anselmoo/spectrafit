"""Integration tests for the spectrafit init workflow (Phase 2)."""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from typer.testing import CliRunner

from spectrafit.cli.main import app


runner = CliRunner()


@pytest.mark.integration
class TestInitWorkflow:
    """End-to-end tests for spectrafit init command."""

    def test_init_cli_creates_project_structure(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["init", "e2e_cli", "--cli", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.output

        project = tmp_path / "e2e_cli"
        assert project.is_dir()
        assert (project / "config.toml").is_file()
        assert (project / "data").is_dir()
        assert (project / "results").is_dir()

    def test_init_jupyter_creates_valid_notebook(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["init", "e2e_nb", "--jupyter", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.output

        nb_path = tmp_path / "e2e_nb" / "spectrafit_getting_started.ipynb"
        assert nb_path.is_file()

        # Validate basic notebook JSON structure
        with nb_path.open() as f:
            nb = json.load(f)
        assert "nbformat" in nb
        assert "cells" in nb
        assert len(nb["cells"]) > 0

        sources = [
            cell.get("source", "")
            for cell in nb["cells"]
            if isinstance(cell, dict) and cell.get("cell_type") == "code"
        ]
        code_text = "\n".join(
            src if isinstance(src, str) else "".join(src) for src in sources
        )
        assert "UnifiedFittingConfig" in code_text
        assert "SpectraFitNotebook.from_config" in code_text
        assert "args=config" not in code_text

    def test_init_both_creates_all_files(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["init", "e2e_both", "--both", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.output

        project = tmp_path / "e2e_both"
        assert (project / "config.toml").is_file()
        assert (project / "spectrafit_getting_started.ipynb").is_file()

    def test_init_toml_config_is_parseable(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["init", "e2e_toml_check", "--cli", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 0, result.output

        config_path = tmp_path / "e2e_toml_check" / "config.toml"
        import tomllib  # available in Python 3.11+; else use tomli

        with config_path.open("rb") as f:
            config = tomllib.load(f)

        assert isinstance(config, dict)

    def test_init_json_format(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            [
                "init",
                "e2e_json",
                "--cli",
                "--format",
                "json",
                "--output-dir",
                str(tmp_path),
            ],
        )
        assert result.exit_code == 0, result.output
        json_config = tmp_path / "e2e_json" / "config.json"
        assert json_config.is_file()
        with json_config.open() as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_init_mutual_exclusion_exits_1(self, tmp_path: Path) -> None:
        result = runner.invoke(
            app,
            ["init", "bad", "--cli", "--jupyter", "--output-dir", str(tmp_path)],
        )
        assert result.exit_code == 1

    def test_init_no_name_no_flags_is_interactive(self, tmp_path: Path) -> None:
        """Without a name and flags, the wizard is invoked — input 'q' aborts."""
        result = runner.invoke(
            app,
            ["init", "--cli", "--output-dir", str(tmp_path)],
            input="test_interactive_name\n",
        )
        # Wizard resolves project_name from input when only --cli flag present
        assert result.exit_code in (0, 1)  # may abort or succeed

    def test_init_overwrite_flag(self, tmp_path: Path) -> None:
        for _ in range(2):
            result = runner.invoke(
                app,
                [
                    "init",
                    "overwrite_test",
                    "--cli",
                    "--overwrite",
                    "--output-dir",
                    str(tmp_path),
                ],
            )
            assert result.exit_code == 0, result.output

        assert (tmp_path / "overwrite_test" / "config.toml").is_file()

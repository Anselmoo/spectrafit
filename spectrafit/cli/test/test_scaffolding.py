"""Tests for scaffolding commands (init, new-config)."""

from __future__ import annotations

import json
import tempfile

from pathlib import Path

import pytest
import yaml

from typer.testing import CliRunner

from spectrafit.cli.main import app
from spectrafit.models.registry import REGISTRY


runner = CliRunner()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


# -----------------------------------------------------------------------
# init command
# -----------------------------------------------------------------------


class TestInitCommand:
    """Tests for the ``init`` command."""

    def test_init_creates_directory_structure(self, temp_dir: Path) -> None:
        """Test that init creates project dir, data/, results/, and config."""
        project = temp_dir / "my_project"
        result = runner.invoke(app, ["init", str(project)])
        assert result.exit_code == 0, result.output
        assert (project / "config.json").exists()
        assert (project / "data").is_dir()
        assert (project / "results").is_dir()

    def test_init_default_config_is_valid_json(self, temp_dir: Path) -> None:
        """Test that the generated default config is valid JSON."""
        project = temp_dir / "json_proj"
        runner.invoke(app, ["init", str(project)])
        config = json.loads((project / "config.json").read_text())
        assert "fitting" in config
        assert "peaks" in config["fitting"]
        assert "parameters" in config["fitting"]

    @pytest.mark.parametrize("fmt", ["json", "yaml", "toml"])
    def test_init_with_format(self, temp_dir: Path, fmt: str) -> None:
        """Test init creates config in requested format."""
        project = temp_dir / f"proj_{fmt}"
        result = runner.invoke(app, ["init", str(project), "--format", fmt])
        assert result.exit_code == 0, result.output
        assert (project / f"config.{fmt}").exists()

    def test_init_existing_dir_abort(self, temp_dir: Path) -> None:
        """Test that init aborts when dir exists and user declines."""
        project = temp_dir / "existing"
        project.mkdir()
        result = runner.invoke(app, ["init", str(project)], input="n\n")
        assert result.exit_code != 0 or "Aborted" in result.output

    def test_init_existing_dir_continue(self, temp_dir: Path) -> None:
        """Test that init continues when dir exists and user confirms."""
        project = temp_dir / "existing2"
        project.mkdir()
        result = runner.invoke(app, ["init", str(project)], input="y\n")
        assert result.exit_code == 0, result.output
        assert (project / "config.json").exists()

    def test_init_help(self) -> None:
        """Test init --help works."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "project" in result.output.lower()

    def test_init_yaml_config_is_valid(self, temp_dir: Path) -> None:
        """Test that YAML config is parseable."""
        project = temp_dir / "yaml_proj"
        runner.invoke(app, ["init", str(project), "-f", "yaml"])
        config = yaml.safe_load((project / "config.yaml").read_text())
        assert "fitting" in config

    def test_init_config_has_gaussian(self, temp_dir: Path) -> None:
        """Test that default config includes a gaussian peak."""
        project = temp_dir / "gauss_proj"
        runner.invoke(app, ["init", str(project)])
        config = json.loads((project / "config.json").read_text())
        peak1 = config["fitting"]["peaks"]["1"]
        assert "gaussian" in peak1

    def test_init_config_has_minimizer_optimizer(self, temp_dir: Path) -> None:
        """Test that default config includes minimizer and optimizer."""
        project = temp_dir / "minopt_proj"
        runner.invoke(app, ["init", str(project)])
        config = json.loads((project / "config.json").read_text())
        params = config["fitting"]["parameters"]
        assert "minimizer" in params
        assert "optimizer" in params


# -----------------------------------------------------------------------
# new-config command
# -----------------------------------------------------------------------


class TestNewConfigCommand:
    """Tests for the ``new-config`` command."""

    def test_new_config_default_stdout(self) -> None:
        """Test new-config prints valid JSON to stdout by default."""
        result = runner.invoke(app, ["new-config"])
        assert result.exit_code == 0, result.output
        config = json.loads(result.output)
        assert "fitting" in config

    def test_new_config_multiple_peaks(self) -> None:
        """Test generating config with multiple peaks."""
        result = runner.invoke(app, ["new-config", "-n", "3"])
        assert result.exit_code == 0, result.output
        config = json.loads(result.output)
        assert len(config["fitting"]["peaks"]) == 3

    @pytest.mark.parametrize(
        "model_name",
        ["gaussian", "lorentzian", "voigt", "pseudovoigt"],
    )
    def test_new_config_model_types(self, model_name: str) -> None:
        """Test generating config for various peak model types."""
        result = runner.invoke(app, ["new-config", "-m", model_name])
        assert result.exit_code == 0, result.output
        config = json.loads(result.output)
        peak1 = config["fitting"]["peaks"]["1"]
        assert model_name in peak1
        # Verify parameter names match the registry
        info = REGISTRY.get(model_name)
        for param in info.parameters:
            assert param in peak1[model_name]

    def test_new_config_unknown_model(self) -> None:
        """Test that an unknown model name results in an error."""
        result = runner.invoke(app, ["new-config", "-m", "nonexistent"])
        assert result.exit_code != 0

    @pytest.mark.parametrize("fmt", ["json", "yaml", "toml"])
    def test_new_config_formats_stdout(self, fmt: str) -> None:
        """Test new-config outputs in the requested format."""
        result = runner.invoke(app, ["new-config", "-f", fmt])
        assert result.exit_code == 0, result.output
        assert len(result.output.strip()) > 0

    def test_new_config_output_to_file(self, temp_dir: Path) -> None:
        """Test writing config to a file via --output."""
        out = temp_dir / "out.json"
        result = runner.invoke(app, ["new-config", "-o", str(out)])
        assert result.exit_code == 0, result.output
        config = json.loads(out.read_text())
        assert "fitting" in config

    def test_new_config_output_to_file_yaml(self, temp_dir: Path) -> None:
        """Test writing YAML config to a file."""
        out = temp_dir / "out.yaml"
        result = runner.invoke(app, ["new-config", "-f", "yaml", "-o", str(out)])
        assert result.exit_code == 0, result.output
        config = yaml.safe_load(out.read_text())
        assert "fitting" in config

    def test_new_config_help(self) -> None:
        """Test new-config --help works."""
        result = runner.invoke(app, ["new-config", "--help"])
        assert result.exit_code == 0
        assert "model" in result.output.lower() or "config" in result.output.lower()

    def test_new_config_all_registry_models(self) -> None:
        """Test that every registered model produces a valid config."""
        for name in REGISTRY.names():
            result = runner.invoke(app, ["new-config", "-m", name])
            assert result.exit_code == 0, f"Failed for model {name}: {result.output}"

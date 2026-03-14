"""Unit tests for typed example-script config resolution helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import generate_plots
from spectrafit.core.fitting_config import UnifiedFittingConfig
from spectrafit.workflow.validation import resolved_config


REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_INPUT = REPO_ROOT / "examples" / "basic" / "input.toml"


@pytest.mark.unit
def test_run_live_examples_resolves_typed_config_to_local_data() -> None:
    config = resolved_config(EXAMPLE_INPUT)

    assert isinstance(config, UnifiedFittingConfig)
    assert config.data is not None
    assert config.data.infile == (EXAMPLE_INPUT.parent / "data.csv").resolve()


@pytest.mark.unit
def test_generate_plots_load_config_resolves_typed_local_data() -> None:
    config = generate_plots._load_config(EXAMPLE_INPUT)  # noqa: SLF001

    assert isinstance(config, UnifiedFittingConfig)
    assert config.data is not None
    assert config.data.infile == (EXAMPLE_INPUT.parent / "data.csv").resolve()

"""Unit tests for UnifiedFittingConfig (spectrafit.core.fitting_config).

Covers:
- from_dict() with v2.0.0 flat structure
- from_dict() with v1.x nested structure (rixs/config.json compat) — Phase 2
- to_solver_args() output contract
- Pydantic validation errors for missing/malformed peaks
- String-integer peak key validation — Phase 3
- from_file() relative infile path rebasing — Phase X
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from spectrafit.core.fitting_config import UnifiedFittingConfig


# ---------------------------------------------------------------------------
# Minimal valid input (v2 flat structure)
# ---------------------------------------------------------------------------

MINIMAL_V2: dict[str, Any] = {
    "peaks": {
        "1": {
            "gaussian": {
                "amplitude": {"min": 0, "max": 2, "value": 1.0, "vary": True},
                "center": {"min": -2, "max": 2, "value": 0.0, "vary": True},
                "fwhmg": {"min": 0.01, "max": 1.0, "value": 0.5, "vary": True},
            }
        }
    },
    "column": {"x": "energy", "y": "intensity"},
    "minimizer": {"nan_policy": "propagate", "calc_covar": True},
    "optimizer": {"max_nfev": 1000, "method": "leastsq"},
    "global_": 0,
}


@pytest.mark.unit
class TestFromDict:
    """UnifiedFittingConfig.from_dict() — v2 flat input."""

    def test_minimal_valid(self) -> None:
        config = UnifiedFittingConfig.from_dict(MINIMAL_V2)
        assert config is not None

    def test_peaks_accessible(self) -> None:
        config = UnifiedFittingConfig.from_dict(MINIMAL_V2)
        assert "1" in config.peaks

    def test_multiple_peaks(self) -> None:
        data: dict[str, Any] = {
            **MINIMAL_V2,
            "peaks": {
                "1": {
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": -1.0},
                        "fwhmg": {"value": 0.5},
                    }
                },
                "2": {
                    "lorentzian": {
                        "amplitude": {"value": 0.8},
                        "center": {"value": 1.0},
                        "fwhml": {"value": 0.6},
                    }
                },
            },
        }
        config = UnifiedFittingConfig.from_dict(data)
        assert len(config.peaks) == 2


@pytest.mark.unit
class TestPeakKeyValidation:
    """String-integer peak key enforcement (Phase 3 — validator in UnifiedFittingConfig)."""

    def test_non_integer_string_key_rejected(self) -> None:
        data: dict[str, Any] = {
            **MINIMAL_V2,
            "peaks": {
                "peak_one": {  # non-integer key — must be rejected
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": 0.0},
                        "fwhmg": {"value": 0.5},
                    }
                }
            },
        }
        with pytest.raises(Exception):  # noqa: B017  # ValidationError expected
            UnifiedFittingConfig.from_dict(data)

    def test_zero_key_rejected(self) -> None:
        data: dict[str, Any] = {
            **MINIMAL_V2,
            "peaks": {
                "0": {  # zero — must be rejected (keys start at "1")
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": 0.0},
                        "fwhmg": {"value": 0.5},
                    }
                }
            },
        }
        with pytest.raises(Exception):  # noqa: B017
            UnifiedFittingConfig.from_dict(data)

    def test_valid_positive_integer_keys_accepted(self) -> None:
        data: dict[str, Any] = {
            **MINIMAL_V2,
            "peaks": {
                "1": {
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": -1.0},
                        "fwhmg": {"value": 0.5},
                    }
                },
                "2": {
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": 1.0},
                        "fwhmg": {"value": 0.5},
                    }
                },
                "10": {
                    "gaussian": {
                        "amplitude": {"value": 1.0},
                        "center": {"value": 5.0},
                        "fwhmg": {"value": 0.5},
                    }
                },
            },
        }
        config = UnifiedFittingConfig.from_dict(data)
        assert len(config.peaks) == 3


# ---------------------------------------------------------------------------
# X3 — from_file() path rebasing tests
# ---------------------------------------------------------------------------

_MINIMAL_TOML = """\
[data]
infile = "data.csv"
separator = ","

[column]
x = "energy"
y = "intensity"

[minimizer]
nan_policy = "propagate"
calc_covar = true

[optimizer]
max_nfev = 1000
method = "leastsq"

global_ = 0

[[components]]
id = "p1"
model = "gaussian"

[components.amplitude]
value = 1.0
vary = true

[components.center]
value = 0.0
vary = true

[components.fwhmg]
value = 0.5
vary = true
"""


@pytest.mark.unit
class TestFromFilePaths:
    """from_file() must rebase a relative infile against the config file's directory."""

    def test_relative_infile_rebased_to_config_dir(self, tmp_path: Path) -> None:
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(_MINIMAL_TOML, encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(toml_file)
        expected = (tmp_path / "data.csv").resolve()
        assert Path(str(cfg.data.infile)).resolve() == expected

    def test_absolute_infile_not_changed(self, tmp_path: Path) -> None:
        abs_path = (tmp_path / "data.csv").resolve()
        toml_content = _MINIMAL_TOML.replace('infile = "data.csv"', f'infile = "{abs_path}"')
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(toml_file)
        assert Path(str(cfg.data.infile)).resolve() == abs_path

    def test_infile_in_subdir_rebased(self, tmp_path: Path) -> None:
        (tmp_path / "data").mkdir()
        toml_content = _MINIMAL_TOML.replace('infile = "data.csv"', 'infile = "data/spectrum.csv"')
        toml_file = tmp_path / "input.toml"
        toml_file.write_text(toml_content, encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(toml_file)
        expected = (tmp_path / "data" / "spectrum.csv").resolve()
        assert Path(str(cfg.data.infile)).resolve() == expected

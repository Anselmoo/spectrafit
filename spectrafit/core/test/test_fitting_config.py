"""Tests for the unified fitting configuration model."""

from __future__ import annotations

import json

from typing import TYPE_CHECKING
from typing import Any


if TYPE_CHECKING:
    from pathlib import Path

import pytest
import yaml

from spectrafit.core.fitting_config import ColumnConfig
from spectrafit.core.fitting_config import UnifiedFittingConfig


pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MINIMAL_PEAKS: dict[str, Any] = {
    "1": {
        "pseudovoigt": {
            "amplitude": {"max": 2, "min": 0, "vary": True, "value": 1},
            "center": {"max": 2, "min": -2, "vary": True, "value": 0},
            "fwhmg": {"max": 0.1, "min": 0.02, "vary": True, "value": 0.01},
            "fwhml": {"max": 0.1, "min": 0.01, "vary": True, "value": 0.01},
        }
    }
}


@pytest.fixture
def minimal_dict() -> dict[str, Any]:
    """Return a minimal valid configuration dictionary."""
    return {"peaks": MINIMAL_PEAKS}


@pytest.fixture
def full_dict() -> dict[str, Any]:
    """Return a full configuration dictionary with all fields."""
    return {
        "peaks": MINIMAL_PEAKS,
        "minimizer": {"nan_policy": "omit", "calc_covar": False},
        "optimizer": {"max_nfev": 500, "method": "least_squares"},
        "column": {"x": "eV", "y": "counts"},
        "global": 1,
        "conf_interval": {"alpha": 0.05, "max_nfev": 100000},
    }


# ---------------------------------------------------------------------------
# ColumnConfig
# ---------------------------------------------------------------------------


class TestColumnConfig:
    """Tests for ColumnConfig defaults and overrides."""

    def test_defaults(self) -> None:
        """ColumnConfig uses 'energy' / 'intensity' by default."""
        col = ColumnConfig()
        assert col.x == "energy"
        assert col.y == "intensity"

    def test_custom(self) -> None:
        """ColumnConfig accepts custom column names."""
        col = ColumnConfig(x="eV", y="counts")
        assert col.x == "eV"
        assert col.y == "counts"


# ---------------------------------------------------------------------------
# UnifiedFittingConfig — creation & defaults
# ---------------------------------------------------------------------------


class TestUnifiedFittingConfigDefaults:
    """Tests for default values when only peaks are provided."""

    def test_minimal_creation(self, minimal_dict: dict[str, Any]) -> None:
        """Config can be created with only the required 'peaks' field."""
        cfg = UnifiedFittingConfig.model_validate(minimal_dict)
        assert cfg.peaks == MINIMAL_PEAKS
        assert cfg.global_ == 0
        assert cfg.conf_interval is False
        assert cfg.column.x == "energy"
        assert cfg.column.y == "intensity"

    def test_minimizer_default(self, minimal_dict: dict[str, Any]) -> None:
        """Default minimizer uses 'propagate' nan_policy and calc_covar=True."""
        cfg = UnifiedFittingConfig.model_validate(minimal_dict)
        assert cfg.minimizer.nan_policy == "propagate"
        assert cfg.minimizer.calc_covar is True

    def test_optimizer_default(self, minimal_dict: dict[str, Any]) -> None:
        """Default optimizer uses 'leastsq' method and no nfev limit."""
        cfg = UnifiedFittingConfig.model_validate(minimal_dict)
        assert cfg.optimizer.method == "leastsq"
        assert cfg.optimizer.max_nfev is None


# ---------------------------------------------------------------------------
# UnifiedFittingConfig — full configuration
# ---------------------------------------------------------------------------


class TestUnifiedFittingConfigFull:
    """Tests for a fully specified configuration."""

    def test_all_fields(self, full_dict: dict[str, Any]) -> None:
        """All explicit fields are captured correctly."""
        cfg = UnifiedFittingConfig.model_validate(full_dict)
        assert cfg.minimizer.nan_policy == "omit"
        assert cfg.minimizer.calc_covar is False
        assert cfg.optimizer.max_nfev == 500
        assert cfg.optimizer.method == "least_squares"
        assert cfg.column.x == "eV"
        assert cfg.column.y == "counts"
        assert cfg.global_ == 1
        assert cfg.conf_interval == {"alpha": 0.05, "max_nfev": 100000}

    def test_global_alias(self) -> None:
        """The 'global' alias populates global_ correctly."""
        cfg = UnifiedFittingConfig.model_validate({"peaks": MINIMAL_PEAKS, "global": 2})
        assert cfg.global_ == 2

    def test_global_underscore(self) -> None:
        """The 'global_' field name also works (populate_by_name=True)."""
        cfg = UnifiedFittingConfig.model_validate(
            {"peaks": MINIMAL_PEAKS, "global_": 1}
        )
        assert cfg.global_ == 1


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------


class TestFromDict:
    """Tests for the from_dict classmethod."""

    def test_round_trip(self, full_dict: dict[str, Any]) -> None:
        """from_dict produces the same result as model_validate."""
        cfg = UnifiedFittingConfig.from_dict(full_dict)
        assert cfg.peaks == MINIMAL_PEAKS
        assert cfg.optimizer.method == "least_squares"


# ---------------------------------------------------------------------------
# from_file
# ---------------------------------------------------------------------------


class TestFromFile:
    """Tests for loading from JSON, YAML, and TOML files."""

    def test_from_json(self, tmp_path: Path, full_dict: dict[str, Any]) -> None:
        """Load configuration from a .json file."""
        p = tmp_path / "config.json"
        p.write_text(json.dumps(full_dict), encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(p)
        assert cfg.peaks == MINIMAL_PEAKS
        assert cfg.optimizer.method == "least_squares"

    def test_from_yaml(self, tmp_path: Path, full_dict: dict[str, Any]) -> None:
        """Load configuration from a .yaml file."""
        p = tmp_path / "config.yaml"
        p.write_text(yaml.dump(full_dict), encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(p)
        assert cfg.peaks == MINIMAL_PEAKS

    def test_from_yml(self, tmp_path: Path, minimal_dict: dict[str, Any]) -> None:
        """Load configuration from a .yml file."""
        p = tmp_path / "config.yml"
        p.write_text(yaml.dump(minimal_dict), encoding="utf-8")
        cfg = UnifiedFittingConfig.from_file(p)
        assert cfg.global_ == 0

    def test_from_toml(self, tmp_path: Path) -> None:
        """Load configuration from a .toml file."""
        import tomli_w

        data: dict[str, Any] = {
            "peaks": MINIMAL_PEAKS,
            "minimizer": {"nan_policy": "raise"},
        }
        p = tmp_path / "config.toml"
        with p.open("wb") as f:
            tomli_w.dump(data, f)
        cfg = UnifiedFittingConfig.from_file(p)
        assert cfg.minimizer.nan_policy == "raise"

    def test_unsupported_extension(self, tmp_path: Path) -> None:
        """Unsupported file extensions raise OSError."""
        p = tmp_path / "config.csv"
        p.write_text("", encoding="utf-8")
        with pytest.raises(OSError, match="Unsupported file format"):
            UnifiedFittingConfig.from_file(p)


# ---------------------------------------------------------------------------
# to_solver_args
# ---------------------------------------------------------------------------


class TestToSolverArgs:
    """Tests for the to_solver_args conversion method."""

    def test_output_keys(self, minimal_dict: dict[str, Any]) -> None:
        """to_solver_args returns expected top-level keys."""
        args = UnifiedFittingConfig.from_dict(minimal_dict).to_solver_args()
        assert set(args) == {
            "peaks",
            "minimizer",
            "optimizer",
            "column",
            "global_",
            "conf_interval",
        }

    def test_column_is_list(self, minimal_dict: dict[str, Any]) -> None:
        """Column is serialised as a two-element list for the solver."""
        args = UnifiedFittingConfig.from_dict(minimal_dict).to_solver_args()
        assert args["column"] == ["energy", "intensity"]

    def test_minimizer_is_dict(self, full_dict: dict[str, Any]) -> None:
        """Minimizer section is a plain dict in solver args."""
        args = UnifiedFittingConfig.from_dict(full_dict).to_solver_args()
        assert isinstance(args["minimizer"], dict)
        assert args["minimizer"]["nan_policy"] == "omit"

    def test_optimizer_is_dict(self, full_dict: dict[str, Any]) -> None:
        """Optimizer section is a plain dict in solver args."""
        args = UnifiedFittingConfig.from_dict(full_dict).to_solver_args()
        assert isinstance(args["optimizer"], dict)
        assert args["optimizer"]["method"] == "least_squares"

    def test_global_value(self, full_dict: dict[str, Any]) -> None:
        """global_ is forwarded correctly."""
        args = UnifiedFittingConfig.from_dict(full_dict).to_solver_args()
        assert args["global_"] == 1

    def test_conf_interval_forwarded(self, full_dict: dict[str, Any]) -> None:
        """conf_interval dict is forwarded as-is."""
        args = UnifiedFittingConfig.from_dict(full_dict).to_solver_args()
        assert args["conf_interval"] == {"alpha": 0.05, "max_nfev": 100000}


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class TestValidationErrors:
    """Tests for expected validation failures."""

    def test_missing_peaks(self) -> None:
        """Peaks is a required field."""
        with pytest.raises(ValueError):
            UnifiedFittingConfig.model_validate({})

    def test_invalid_global_too_high(self) -> None:
        """global_ > 2 is rejected."""
        with pytest.raises(ValueError):
            UnifiedFittingConfig.model_validate({"peaks": MINIMAL_PEAKS, "global": 5})

    def test_invalid_global_negative(self) -> None:
        """global_ < 0 is rejected."""
        with pytest.raises(ValueError):
            UnifiedFittingConfig.model_validate({"peaks": MINIMAL_PEAKS, "global": -1})


# ---------------------------------------------------------------------------
# Extra fields (extra="allow")
# ---------------------------------------------------------------------------


class TestExtraFields:
    """Tests that extra fields are accepted and preserved."""

    def test_extra_field_preserved(self) -> None:
        """Unknown keys are kept thanks to extra='allow'."""
        cfg = UnifiedFittingConfig.model_validate(
            {"peaks": MINIMAL_PEAKS, "description": "my experiment"}
        )
        assert cfg.model_extra
        assert cfg.model_extra["description"] == "my experiment"

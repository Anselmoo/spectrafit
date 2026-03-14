"""Tests for DataConfig — typed data-loading configuration model."""

from __future__ import annotations

from pathlib import Path

import pytest

from pydantic import ValidationError
from spectrafit.adapters.data_config_args import data_config_from_args_dict
from spectrafit.models.data_config import DataConfig
from spectrafit.models.fitting_context import FittingContext


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestDataConfigDefaults:
    """DataConfig has sensible defaults for all optional fields."""

    def test_minimal_construction(self, tmp_path: Path) -> None:
        infile = tmp_path / "data.txt"
        infile.touch()
        cfg = DataConfig(infile=infile)
        assert cfg.separator == r"\s+"
        assert cfg.header == 0
        assert cfg.decimal == "."
        assert cfg.comment is None
        assert cfg.x_col == "energy"
        assert cfg.y_col == "intensity"
        assert cfg.global_ == 0

    def test_infile_is_coerced_to_path(self, tmp_path: Path) -> None:
        cfg = DataConfig(infile=str(tmp_path / "data.txt"))
        assert isinstance(cfg.infile, Path)

    def test_custom_fields(self, tmp_path: Path) -> None:
        cfg = DataConfig(
            infile=tmp_path / "data.csv",
            separator=",",
            header=1,
            decimal=",",
            comment="#",
            x_col="x",
            y_col="y",
            context=FittingContext.from_global_int(1),
        )
        assert cfg.separator == ","
        assert cfg.decimal == ","
        assert cfg.comment == "#"
        assert cfg.x_col == "x"
        assert cfg.y_col == "y"
        assert cfg.global_ == 1

    def test_legacy_global_field_rejected(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            DataConfig(infile=tmp_path / "data.csv", **{"global": 1})


# ---------------------------------------------------------------------------
# legacy args adapter
# ---------------------------------------------------------------------------


class TestLegacyArgsAdapter:
    """Dedicated adapter bridges the legacy dict interface into DataConfig."""

    def test_full_dict_with_column_list(self, tmp_path: Path) -> None:
        """Old ``column`` list format is transparently converted."""
        infile = tmp_path / "spectrum.txt"
        args = {
            "infile": str(infile),
            "separator": ",",
            "header": 0,
            "decimal": ".",
            "comment": "#",
            "column": ["energy", "intensity"],
            "global_": 0,
        }
        cfg = data_config_from_args_dict(args)
        assert cfg.infile == infile
        assert cfg.separator == ","
        assert cfg.x_col == "energy"
        assert cfg.y_col == "intensity"
        assert cfg.global_ == 0

    def test_full_dict_with_x_y_col(self, tmp_path: Path) -> None:
        """New ``x_col``/``y_col`` format works directly."""
        infile = tmp_path / "spectrum.txt"
        args = {
            "infile": str(infile),
            "x_col": "wavenumber",
            "y_col": "absorbance",
            "global_": 0,
        }
        cfg = data_config_from_args_dict(args)
        assert cfg.x_col == "wavenumber"
        assert cfg.y_col == "absorbance"

    def test_minimal_dict_uses_defaults(self, tmp_path: Path) -> None:
        cfg = data_config_from_args_dict({"infile": str(tmp_path / "f.txt")})
        assert cfg.separator == r"\s+"
        assert cfg.header is None
        assert cfg.decimal == "."
        assert cfg.comment is None
        assert cfg.x_col == "energy"
        assert cfg.y_col == "intensity"
        assert cfg.global_ == 0

    def test_global_flag_truthy(self, tmp_path: Path) -> None:
        cfg = data_config_from_args_dict(
            {"infile": str(tmp_path / "f.txt"), "global_": 1}
        )
        assert cfg.global_ == 1


# ---------------------------------------------------------------------------
# from_unified
# ---------------------------------------------------------------------------


class TestFromUnified:
    """DataConfig.from_unified derives column and global_ from UnifiedFittingConfig."""

    def _make_config(self) -> object:
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        return UnifiedFittingConfig(
            components=[
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "min": 0, "max": 2, "vary": True},
                        "center": {"value": 0.0, "min": -1, "max": 1, "vary": True},
                        "fwhmg": {
                            "value": 0.5,
                            "min": 0.1,
                            "max": 2.0,
                            "vary": True,
                        },
                    },
                }
            ]
        )

    def test_column_from_config(self, tmp_path: Path) -> None:
        cfg = self._make_config()
        dc = DataConfig.from_unified(cfg, tmp_path / "data.txt")
        assert dc.x_col == "energy"
        assert dc.y_col == "intensity"

    def test_infile_is_path(self, tmp_path: Path) -> None:
        cfg = self._make_config()
        dc = DataConfig.from_unified(cfg, str(tmp_path / "data.txt"))
        assert isinstance(dc.infile, Path)

    def test_default_separator(self, tmp_path: Path) -> None:
        cfg = self._make_config()
        dc = DataConfig.from_unified(cfg, tmp_path / "data.txt")
        assert dc.separator == r"\s+"

    def test_custom_separator(self, tmp_path: Path) -> None:
        cfg = self._make_config()
        dc = DataConfig.from_unified(cfg, tmp_path / "data.csv", separator=",")
        assert dc.separator == ","

    def test_global_zero_by_default(self, tmp_path: Path) -> None:
        cfg = self._make_config()
        dc = DataConfig.from_unified(cfg, tmp_path / "data.txt")
        assert dc.global_ == 0

    def test_prefers_data_owned_columns_over_compat_column(self, tmp_path: Path) -> None:
        from spectrafit.core.fitting_config import UnifiedFittingConfig

        cfg = UnifiedFittingConfig(
            components=[
                {
                    "id": "p1",
                    "model": "gaussian",
                    "parameters": {
                        "amplitude": {"value": 1.0, "min": 0, "max": 2, "vary": True},
                        "center": {"value": 0.0, "min": -1, "max": 1, "vary": True},
                        "fwhmg": {"value": 0.5, "min": 0.1, "max": 2.0, "vary": True},
                    },
                }
            ],
            column={"x": "legacy_x", "y": "legacy_y"},
            data=DataConfig(
                infile=tmp_path / "owned.csv",
                x_col="owned_x",
                y_col="owned_y",
                separator=",",
            ),
        )

        dc = DataConfig.from_unified(cfg, tmp_path / "data.txt")

        assert cfg.column.x == "owned_x"
        assert cfg.column.y == "owned_y"
        assert dc.x_col == "owned_x"
        assert dc.y_col == "owned_y"

"""Tests for DataConfig — typed data-loading configuration model."""

from __future__ import annotations

from pathlib import Path

from spectrafit.models.data_config import DataConfig


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
            **{"global": 1},
        )
        assert cfg.separator == ","
        assert cfg.decimal == ","
        assert cfg.comment == "#"
        assert cfg.x_col == "x"
        assert cfg.y_col == "y"
        assert cfg.global_ == 1


# ---------------------------------------------------------------------------
# from_args_dict
# ---------------------------------------------------------------------------


class TestFromArgsDict:
    """DataConfig.from_args_dict bridges the legacy dict interface."""

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
        cfg = DataConfig.from_args_dict(args)
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
        cfg = DataConfig.from_args_dict(args)
        assert cfg.x_col == "wavenumber"
        assert cfg.y_col == "absorbance"

    def test_minimal_dict_uses_defaults(self, tmp_path: Path) -> None:
        cfg = DataConfig.from_args_dict({"infile": str(tmp_path / "f.txt")})
        assert cfg.separator == r"\s+"
        assert cfg.header is None
        assert cfg.decimal == "."
        assert cfg.comment is None
        assert cfg.x_col == "energy"
        assert cfg.y_col == "intensity"
        assert cfg.global_ == 0

    def test_global_flag_truthy(self, tmp_path: Path) -> None:
        cfg = DataConfig.from_args_dict(
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

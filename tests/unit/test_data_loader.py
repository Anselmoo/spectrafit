"""Unit tests for data loading helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from spectrafit.core.data_loader import load_data
from spectrafit.core.data_loader import sniff_separator
from spectrafit.models.data_config import DataConfig


@pytest.mark.unit
def test_sniff_separator_detects_csv_delimiter(tmp_path: Path) -> None:
    data_file = tmp_path / "spectrum.csv"
    data_file.write_text("energy,intensity\n0,1\n1,2\n", encoding="utf-8")

    assert sniff_separator(data_file) == ","


@pytest.mark.unit
def test_sniff_separator_falls_back_to_default_on_oserror(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.csv"

    assert sniff_separator(missing_file) == r"\s+"


@pytest.mark.unit
def test_load_data_autodetects_separator_from_default_config(tmp_path: Path) -> None:
    data_file = tmp_path / "spectrum.csv"
    data_file.write_text("energy,intensity\n0,1\n1,2\n", encoding="utf-8")
    cfg = DataConfig(infile=data_file, separator=r"\s+", header=0)

    loaded = load_data(cfg)

    assert list(loaded.columns) == ["energy", "intensity"]
    assert loaded["intensity"].tolist() == [1.0, 2.0]


@pytest.mark.unit
def test_load_data_wraps_value_errors(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    data_file = tmp_path / "spectrum.csv"
    data_file.write_text("energy,intensity\n0,1\n", encoding="utf-8")
    cfg = DataConfig(infile=data_file, separator=",", header=0)

    def _raise_value_error(*args: object, **kwargs: object) -> object:
        msg = "broken parser"
        raise ValueError(msg)

    monkeypatch.setattr("spectrafit.core.data_loader.pd.read_csv", _raise_value_error)

    with pytest.raises(ValueError, match="Failed to load data"):
        load_data(cfg)

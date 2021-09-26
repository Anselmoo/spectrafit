"""Pytest of tools model."""
import numpy as np
import pandas as pd
import pytest

from pandas._testing import assert_frame_equal
from spectrafit.tools import energy_range
from spectrafit.tools import energy_shift
from spectrafit.tools import intensity_smooth
from spectrafit.tools import oversampling
from spectrafit.tools import save_as_json


df = pd.DataFrame(
    {
        "energy": np.linspace(0, 10, 100),
        "intensity": np.random.rand(100),
    }
)


def test_energy_range_1() -> None:
    """Testing energy range for no range."""
    args = {
        "energy_start": None,
        "energy_stop": None,
        "column": ["energy"],
    }
    assert_frame_equal(
        energy_range(df, args),
        df,
    )


def test_energy_range_2() -> None:
    """Testing energy range for start energy only."""
    args = {
        "energy_start": 1,
        "energy_stop": None,
        "column": ["energy"],
    }
    assert_frame_equal(
        energy_range(df, args),
        df[(df["energy"] >= args["energy_start"])],
    )


def test_energy_range_3() -> None:
    """Testing energy range for stop energy only."""
    args = {
        "energy_start": None,
        "energy_stop": 5,
        "column": ["energy"],
    }
    assert_frame_equal(
        energy_range(df, args),
        df[(df["energy"] <= args["energy_stop"])],
    )


def test_energy_range_4() -> None:
    """Testing energy range for start & stop energy."""
    args = {
        "energy_start": 0,
        "energy_stop": 10,
        "column": ["energy"],
    }
    assert_frame_equal(
        energy_range(df, args),
        df[
            (df["energy"] >= args["energy_start"])
            & (df["energy"] <= args["energy_stop"])
        ],
    )


def test_oversampling_1() -> None:
    """Testing oversampling for no oversampling."""
    args = {
        "oversampling": None,
        "column": ["energy"],
    }
    assert_frame_equal(
        oversampling(df, args),
        df,
    )


def test_oversampling_2() -> None:
    """Testing oversampling for yes oversampling."""
    args = {
        "oversampling": True,
        "column": ["energy", "intensity"],
    }
    assert oversampling(df, args).shape[0] == 500


def test_smoothing_1() -> None:
    """Testing smoothing for no smoothing."""
    args = {
        "smooth": None,
        "column": ["energy"],
    }
    assert_frame_equal(
        intensity_smooth(df, args),
        df,
    )


def test_smoothing_2() -> None:
    """Testing smoothing for yes smoothing."""
    args = {
        "smooth": 5,
        "column": ["energy", "intensity"],
    }
    assert intensity_smooth(df, args).shape[0] == 100


def test_energy_shift_1() -> None:
    """Testing energy shift for no shift."""
    args = {
        "shift": None,
        "column": ["energy"],
    }
    assert_frame_equal(
        energy_shift(df, args),
        df,
    )


def test_energy_shift_2() -> None:
    """Testing energy shift for yes shift."""
    args = {
        "shift": 2,
        "column": ["energy"],
    }
    assert_frame_equal(
        energy_shift(df, args),
        df,
    )


def test_save_as_json_fail() -> None:
    """Testing save as json for no file."""
    args = {
        "outfile": None,
        "data": df,
    }
    with pytest.raises(FileNotFoundError):
        save_as_json(args)

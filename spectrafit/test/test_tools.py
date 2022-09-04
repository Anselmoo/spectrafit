"""Pytest of tools model."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pandas._testing import assert_frame_equal
from spectrafit.models import SolverModels
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.tools import SaveResult
from spectrafit.tools import check_keywords_consistency


class TestPreProcessing:
    """Test Pre-Processing tool."""

    df = pd.DataFrame(
        {
            "energy": np.linspace(0, 10, 100),
            "intensity": np.random.rand(100),
        }
    )

    def test_energy_range_1(self) -> None:
        """Testing energy range for no range."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert_frame_equal(PreProcessing(self.df, args)()[0], self.df)

    def test_energy_range_2(self) -> None:
        """Testing energy range for start energy only."""
        args = {
            "energy_start": 1,
            "energy_stop": None,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert_frame_equal(
            PreProcessing(self.df, args)()[0],
            self.df[(self.df["energy"] >= args["energy_start"])],
        )

    def test_energy_range_3(self) -> None:
        """Testing energy range for stop energy only."""
        args = {
            "energy_start": None,
            "energy_stop": 5,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert_frame_equal(
            PreProcessing(self.df, args)()[0],
            self.df[(self.df["energy"] <= args["energy_stop"])],
        )

    def test_energy_range_4(self) -> None:
        """Testing energy range for start & stop energy."""
        args = {
            "energy_start": 0,
            "energy_stop": 10,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert_frame_equal(
            PreProcessing(self.df, args).energy_range(self.df, args),
            self.df[
                (self.df["energy"] >= args["energy_start"])
                & (self.df["energy"] <= args["energy_stop"])
            ],
        )

    def test_oversampling(self) -> None:
        """Testing oversampling for yes oversampling."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": True,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert PreProcessing(self.df, args).oversampling(self.df, args).shape[0] == 500

    def test_smoothing(self) -> None:
        """Testing smoothing for yes smoothing."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": None,
            "smooth": 5,
            "column": ["energy", "intensity"],
        }
        assert (
            PreProcessing(self.df, args).intensity_smooth(self.df, args).shape[0] == 100
        )

    def test_energy_shift(self) -> None:
        """Testing energy shift for no shift."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": 2.2,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }

        assert PreProcessing(self.df, args)()[0]["energy"].min() == args["shift"]

    def test_return_args(self) -> None:
        """Testing return args."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert PreProcessing(self.df, args)()[1] == args

    def test_keyword_fail(self) -> None:
        """Testing energy range for no range."""
        args = {
            "energy_start": 2,
            "energy_stop": 4,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["Energy", "intensity"],
        }
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            PreProcessing(self.df, args)()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1

    def test_keyword_not_fail(self) -> None:
        """Testing consistency between cmd and input keywords."""
        args_1 = {"keyword": "value"}
        args_2 = {"keyword": "value", "keyword2": "value"}

        check_keywords_consistency(args_1, args_2)

    def test_keyword_fail_2(self) -> None:
        """Testing consistency between cmd and input keywords."""
        args_1 = {"keyword4": "value"}
        args_2 = {"keyword": "value", "keyword2": "value", "keyword3": "value"}

        with pytest.raises(KeyError) as pytest_wrapped_e:
            check_keywords_consistency(args_1, args_2)

        assert pytest_wrapped_e.type == KeyError
        assert pytest_wrapped_e.value.args[0] == str(
            f"ERROR: The {list(args_1.keys())[0]} is not parameter of the `cmd-input`!"
        )


class TestSaving:
    """Test Saving tool."""

    df = pd.DataFrame(
        {
            "energy": np.linspace(0, 10, 100),
            "intensity": np.random.rand(100),
        }
    )

    def test_save_as_json_fail(self) -> None:
        """Testing save as json for no file."""
        args = {
            "outfile": None,
            "data": self.df,
        }
        with pytest.raises(FileNotFoundError):
            SaveResult(self.df, args).save_as_json

    def test_save_all(self) -> None:
        """Testing save all for no file."""
        args = {
            "outfile": "spectrafit/test/export/test_SaveResult",
            "linear_correlation": self.df.to_dict(),
            "fit_insights": {"variables": self.df.to_dict()},
        }
        SaveResult(self.df, args)()
        assert (
            len(list(Path(".").glob("spectrafit/test/export/test_SaveResult*.json")))
            == 1
        )
        assert (
            len(list(Path(".").glob("spectrafit/test/export/test_SaveResult*.csv")))
            == 3
        )


class TestPostProcessing:
    """Test Post-Processing tool."""

    args_0 = {
        "autopeak": False,
        "global_": 0,
        "column": ["Energy", "Intensity_1"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "conf_interval": None,
        "peaks": {
            "1": {
                "pseudovoigt": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 0.1},
                    "fwhml": {"max": 2.5, "min": 0.00001, "vary": True, "value": 1},
                }
            },
            "2": {
                "pseudovoigt": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 1.0},
                    "fwhml": {"max": 2.5, "min": 0.0001, "vary": True, "value": 0.01},
                }
            },
        },
    }
    args_1 = {
        "autopeak": False,
        "global_": 1,
        "column": ["Energy"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "conf_interval": None,
        "peaks": {
            "1": {
                "pseudovoigt": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 0.1},
                    "fwhml": {"max": 2.5, "min": 0.00001, "vary": True, "value": 1},
                }
            },
            "2": {
                "pseudovoigt": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 1.0},
                    "fwhml": {"max": 2.5, "min": 0.0001, "vary": True, "value": 0.01},
                }
            },
        },
    }
    df = pd.DataFrame(
        {
            "Energy": np.arange(10).astype(np.float64),
            "Intensity_1": np.random.rand(10),
            "Intensity_2": np.random.rand(10),
            "Intensity_3": np.random.rand(10),
            "Intensity_4": np.random.rand(10),
        }
    )

    def test_post_processing_local(self) -> None:
        """Testing post processing for local fitting."""
        minimizer, result = SolverModels(df=self.df, args=self.args_0)()

        df, args = PostProcessing(
            df=self.df, args=self.args_0, minimizer=minimizer, result=result
        )()
        assert type(df) == pd.DataFrame
        assert type(args) == dict

    def test_post_processing_global(self) -> None:
        """Testing post processing for global fitting."""
        minimizer, result = SolverModels(df=self.df, args=self.args_1)()

        df, args = PostProcessing(
            df=self.df, args=self.args_1, minimizer=minimizer, result=result
        )()
        assert type(df) == pd.DataFrame
        assert type(args) == dict

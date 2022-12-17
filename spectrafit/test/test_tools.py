"""Pytest of tools model."""
from pathlib import Path
from typing import Any
from typing import Dict

import numpy as np
import pandas as pd
import pytest

from pandas._testing import assert_frame_equal
from spectrafit.models import SolverModels
from spectrafit.tools import PostProcessing
from spectrafit.tools import PreProcessing
from spectrafit.tools import SaveResult
from spectrafit.tools import check_keywords_consistency


@pytest.fixture(name="random_dataframe")
def df() -> pd.DataFrame:
    """Dataframe fixture."""
    return pd.DataFrame(
        {
            "energy": np.linspace(0, 10, 100),
            "intensity": np.random.rand(100),
        }
    )


@pytest.fixture(name="random_dataframe_global")
def df_large() -> pd.DataFrame:
    """Dataframe fixture."""
    return pd.DataFrame(
        {
            "Energy": np.arange(10).astype(np.float64),
            "Intensity_1": np.random.rand(10),
            "Intensity_2": np.random.rand(10),
            "Intensity_3": np.random.rand(10),
            "Intensity_4": np.random.rand(10),
        }
    )


@pytest.fixture(name="args_0")
def args_0() -> Dict[str, Any]:
    """Args fixture."""
    return {
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
                    "amplitude": {"max": 100, "min": 1, "vary": True, "value": 5},
                    "center": {"max": 20, "min": -20, "vary": True, "value": 0.0},
                    "fwhmg": {"max": 2.51, "min": 0.00002, "vary": True, "value": 1.0},
                    "fwhml": {"max": 2.52, "min": 0.001, "vary": True, "value": 0.01},
                }
            },
        },
    }


@pytest.fixture(name="args_1")
def args_1() -> Dict[str, Any]:
    """Args fixture."""
    return {
        "autopeak": False,
        "global_": 1,
        "column": ["Energy"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "conf_interval": {
            "trace": True,
            "maxiter": 20,
            "verbose": 1,
            "prob_func": None,
        },
        "peaks": {
            "1": {
                "pseudovoigt": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 0.1},
                    "fwhml": {"max": 2.5, "min": 0.00001, "vary": True, "value": 1},
                }
            },
        },
    }


@pytest.fixture(name="args_conf_interval_fail")
def args_2() -> Dict[str, Any]:
    """Args fixture."""
    return {
        "autopeak": False,
        "global_": 0,
        "column": ["energy", "intensity"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "conf_interval": {
            "p_names": ["pseudovoigt_amplitude_1"],
            "sigmas": 0.001,
            "trace": True,
            "maxiter": 1,
            "verbose": 0,
            "prob_func": None,
        },
        "peaks": {
            "1": {
                "constant": {
                    "amplitude": {"max": 200, "min": 10, "vary": False, "value": 1},
                }
            },
        },
    }


class TestPreProcessing:
    """Test Pre-Processing tool."""

    def test_energy_range_1(self, random_dataframe: pd.DataFrame) -> None:
        """Testing energy range for no range."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert_frame_equal(PreProcessing(random_dataframe, args)()[0], random_dataframe)

    def test_energy_range_2(self, random_dataframe: pd.DataFrame) -> None:
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
            PreProcessing(random_dataframe, args)()[0],
            random_dataframe[(random_dataframe["energy"] >= args["energy_start"])],
        )

    def test_energy_range_3(self, random_dataframe: pd.DataFrame) -> None:
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
            PreProcessing(random_dataframe, args)()[0],
            random_dataframe[(random_dataframe["energy"] <= args["energy_stop"])],
        )

    def test_energy_range_4(self, random_dataframe: pd.DataFrame) -> None:
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
            PreProcessing(random_dataframe, args).energy_range(random_dataframe, args),
            random_dataframe[
                (random_dataframe["energy"] >= args["energy_start"])
                & (random_dataframe["energy"] <= args["energy_stop"])
            ],
        )

    def test_oversampling(self, random_dataframe: pd.DataFrame) -> None:
        """Testing oversampling for yes oversampling."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": True,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert (
            PreProcessing(random_dataframe, args)
            .oversampling(random_dataframe, args)
            .shape[0]
            == 500
        )

    def test_smoothing(self, random_dataframe: pd.DataFrame) -> None:
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
            PreProcessing(random_dataframe, args)
            .smooth_signal(random_dataframe, args)
            .shape[0]
            == 100
        )

    def test_energy_shift(self, random_dataframe: pd.DataFrame) -> None:
        """Testing energy shift for no shift."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": 2.2,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }

        assert (
            PreProcessing(random_dataframe, args)()[0]["energy"].min() == args["shift"]
        )

    def test_return_args(self, random_dataframe: pd.DataFrame) -> None:
        """Testing return args."""
        args = {
            "energy_start": None,
            "energy_stop": None,
            "shift": None,
            "oversampling": None,
            "smooth": None,
            "column": ["energy", "intensity"],
        }
        assert PreProcessing(random_dataframe, args)()[1] == args

    def test_keyword_fail(self, random_dataframe: pd.DataFrame) -> None:
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
            PreProcessing(random_dataframe, args)()

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

    def test_save_as_json_fail(self, random_dataframe: pd.DataFrame) -> None:
        """Testing save as json for no file."""
        args = {
            "outfile": None,
            "data": random_dataframe,
        }
        with pytest.raises(FileNotFoundError):
            SaveResult(random_dataframe, args).save_as_json

    def test_save_all(self, random_dataframe: pd.DataFrame, tmp_path: Path) -> None:
        """Testing save all for no file."""
        args = {
            "outfile": str(tmp_path / "test_SaveResult"),
            "linear_correlation": random_dataframe.to_dict(),
            "fit_insights": {"variables": random_dataframe.to_dict()},
        }
        SaveResult(random_dataframe, args)()
        assert len(list(Path(tmp_path).glob("test_SaveResult*.json"))) == 1
        assert len(list(Path(tmp_path).glob("test_SaveResult*.csv"))) == 3


class TestPostProcessing:
    """Test Post-Processing tool."""

    def test_post_processing_local(
        self, random_dataframe_global: pd.DataFrame, args_0: Dict[str, Any]
    ) -> None:
        """Testing post processing for local fitting."""
        minimizer, result = SolverModels(df=random_dataframe_global, args=args_0)()

        df, args = PostProcessing(
            df=random_dataframe_global, args=args_0, minimizer=minimizer, result=result
        )()
        assert type(df) == pd.DataFrame
        assert type(args) == dict

    def test_post_processing_global(
        self, random_dataframe_global: pd.DataFrame, args_1: Dict[str, Any]
    ) -> None:
        """Testing post processing for global fitting."""
        minimizer, result = SolverModels(df=random_dataframe_global, args=args_1)()

        df, args = PostProcessing(
            df=random_dataframe_global, args=args_1, minimizer=minimizer, result=result
        )()
        assert type(df) == pd.DataFrame
        assert type(args) == dict

    def test_insight_report_empty_conv(
        self,
        random_dataframe: pd.DataFrame,
        args_conf_interval_fail: Dict[str, Any],
    ) -> None:
        """Testing insight report for no report of the confidence interval."""
        minimizer, result = SolverModels(
            df=random_dataframe, args=args_conf_interval_fail
        )()
        pp = PostProcessing(
            df=random_dataframe,
            args=args_conf_interval_fail,
            minimizer=minimizer,
            result=result,
        )
        pp.make_insight_report
        assert pp.args["confidence_interval"] == {}

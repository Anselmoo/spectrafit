"""Pytest of the model-module."""
import math

from math import log
from math import pi
from math import sqrt
from typing import Any
from typing import Dict
from typing import Tuple

import numpy as np
import pandas as pd
import pytest

from lmfit import Minimizer
from lmfit import Parameters
from numpy.typing import NDArray
from pydantic import ValidationError
from spectrafit.models import AutoPeakDetection
from spectrafit.models import Constants
from spectrafit.models import DistributionModels
from spectrafit.models import ModelParameters
from spectrafit.models import SolverModels
from spectrafit.models import calculated_model


def assert_solver_models(mp: Tuple[Minimizer, Any]) -> None:
    """Assert SolverModels."""
    assert isinstance(mp.__str__(), str)
    assert isinstance(mp, tuple)


class TestConstants:
    """Test constants."""

    def test_ln2(self) -> None:
        """Test the Constants class."""
        assert Constants.ln2 == log(2.0)

    def test_sq2pi(self) -> None:
        """Test the Constants class."""
        assert Constants.sq2pi == sqrt(2.0 * pi)

    def test_sqpi(self) -> None:
        """Test the Constants class."""
        assert Constants.sqpi == sqrt(pi)

    def test_sq2(self) -> None:
        """Test the Constants class."""
        assert Constants.sq2 == sqrt(2.0)

    def test_fwhmg2sig(self) -> None:
        """Test the Constants class."""
        assert Constants.fwhmg2sig == 1 / (2.0 * sqrt(2.0 * log(2.0)))

    def test_fwhml2sig(self) -> None:
        """Test the Constants class."""
        assert Constants.fwhml2sig == 1 / 2.0

    def test_fwhmv2sig(self) -> None:
        """Test the Constants class."""
        assert math.isclose(Constants.fwhmv2sig, 1 / 3.60131, rel_tol=1e-5)


class TestNotSupported:
    """Test of not supported models."""

    args = {
        "autopeak": False,
        "column": ["energy", "intensity"],
        "global_": 0,
        "minimizer": {"method": "Nelder-Mead", "tol": 1e-6},
        "optimizer": {"method": "Nelder-Mead", "tol": 1e-6},
        "peaks": {
            "1": {
                "dummy": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 0.1},
                    "fwhml": {"max": 2.5, "min": 0.00001, "vary": True, "value": 1},
                }
            },
        },
    }
    df = pd.DataFrame(
        {
            "energy": np.arange(10),
            "intensity": np.random.random_sample((10,)),
        }
    )

    def test_solver_model_exit_local(self) -> None:
        """Exit-Test of solver_model for local fitting."""
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df, args=self.args
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == NotImplementedError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1 is not supported!"

    def test_solver_model_exit_global(self) -> None:
        """Exit-Test of solver_model for global fitting."""
        _args = self.args
        _args["global_"] = 1
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df, args=_args
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == NotImplementedError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1_1 is not supported!"

    def test_calculated_model_exit(self) -> None:
        """Exit-Test of solver_model."""
        params = Parameters()
        params.add("dummy_amplitude_1", value=1.0)
        with pytest.raises(NotImplementedError) as pytest_wrapped_e:
            calculated_model(
                params=params,
                x=self.df["energy"].values,
                df=self.df["intensity"].values,
                global_fit=0,
            ).will_exit_somewhere_down_the_stack()
        assert pytest_wrapped_e.type == NotImplementedError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1 is not supported!"

    def test_auto_global_fail(self) -> None:
        """Test of no global fitting and auto peak is allowed."""
        _args = self.args
        _args["global_"] = 1
        _args["autopeak"] = True

        with pytest.raises(KeyError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df, args=_args
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == KeyError
        assert (
            pytest_wrapped_e.value.args[0]
            == "Global fitting mode with automatic peak detection "
            "is not supported yet."
        )


class TestModelParametersSolver:
    """Test of model parameters."""

    args = {
        "global_": 0,
        "autopeak": False,
        "column": ["Energy", "Intensity"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "peaks": {
            "1": {
                "pseudovoigt": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 0.1},
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
            "3": {
                "gaussian": {
                    "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                    "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                    "fwhmg": {"max": 2.5, "min": 0.00002, "vary": True, "value": 1.0},
                }
            },
        },
    }
    args_global_1 = {
        "autopeak": False,
        "global_": 1,
        "column": ["Energy"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
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
    args_global_2 = {
        "autopeak": False,
        "global_": 2,
        "column": ["Energy"],
        "minimizer": {"nan_policy": "propagate", "calc_covar": False},
        "optimizer": {"max_nfev": 10, "method": "leastsq"},
        "peaks": {
            "1": {
                "1": {
                    "pseudovoigt": {
                        "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                        "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                        "fwhmg": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 0.1,
                        },
                        "fwhml": {"max": 2.5, "min": 0.00001, "vary": True, "value": 1},
                    }
                },
                "2": {
                    "pseudovoigt": {
                        "amplitude": {"max": 200, "min": 0, "vary": True, "value": 1},
                        "center": {"max": 200, "min": -200, "vary": True, "value": 0},
                        "fwhmg": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                        "fwhml": {
                            "max": 2.5,
                            "min": 0.0001,
                            "vary": True,
                            "value": 0.01,
                        },
                    }
                },
            },
        },
    }
    df = pd.DataFrame(
        {
            "Energy": np.arange(10).astype(np.float64),
            "Intensity": np.random.rand(10),
        }
    )
    df_global = pd.DataFrame(
        {
            "Energy": np.arange(10).astype(np.float64),
            "Intensity_1": np.random.rand(10),
            "Intensity_2": np.random.rand(10),
            "Intensity_3": np.random.rand(10),
            "Intensity_4": np.random.rand(10),
        }
    )

    def test_str_return(self) -> None:
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert isinstance(mp.__str__(), str)

    def test_param_return(self) -> None:
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert str(type(mp.return_params)) == "<class 'lmfit.parameter.Parameters'>"

    def test_len_param_normal(self) -> None:
        """Test of length of the paramaters for normal fitting."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert len(mp.return_params.keys()) == 10

    def test_len_param_global_1(self) -> None:
        """Test of length of the paramaters for global fitting."""
        mp = ModelParameters(df=self.df_global, args=self.args_global_1)
        mp.define_parameters_global()
        assert len(mp.return_params.keys()) == 32

    def test_solver_local(self) -> None:
        """Test of SolverModels for local fitting."""
        mp = SolverModels(df=self.df, args=self.args)()
        assert_solver_models(mp)

    def test_solver_global_1(self) -> None:
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_1)()
        assert_solver_models(mp)

    def test_solver_global_2(self) -> None:
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_2)()
        assert_solver_models(mp)

    @pytest.fixture
    def args_setting(self) -> Dict[str, Any]:
        """Fixture for args.

        Returns:
            Dict[str, Any]: Add args for testing.
        """
        return {
            "minimizer": {"nan_policy": "propagate", "calc_covar": False},
            "optimizer": {"max_nfev": 10, "method": "leastsq"},
            "peaks": {
                "1": {
                    "pseudovoigt": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "fwhmg": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                        "fwhml": {
                            "max": 2.5,
                            "min": 0.0001,
                            "vary": True,
                            "value": 0.01,
                        },
                    }
                },
                "2": {
                    "gaussian": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "fwhmg": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "3": {
                    "lorentzian": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "fwhml": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "4": {
                    "exponential": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "decay": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "intercept": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "5": {
                    "power": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "exponent": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "intercept": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "6": {
                    "linear": {
                        "slope": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "intercept": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                    }
                },
                "7": {
                    "constant": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                    }
                },
                "8": {
                    "erf": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "sigma": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "9": {
                    "atan": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "sigma": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "10": {
                    "log": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "sigma": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "11": {
                    "heaviside": {
                        "amplitude": {
                            "max": 200,
                            "min": 0,
                            "vary": True,
                            "value": 1,
                        },
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "sigma": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "12": {
                    "voigt": {
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "fwhmv": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                        "gamma": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
                "13": {
                    "voigt": {
                        "center": {
                            "max": 200,
                            "min": -200,
                            "vary": True,
                            "value": 0,
                        },
                        "fwhmv": {
                            "max": 2.5,
                            "min": 0.00002,
                            "vary": True,
                            "value": 1.0,
                        },
                    }
                },
            },
        }

    def test_all_model_local(self, args_setting: Dict[str, Any]) -> None:
        """Test of the AllModel class for local fitting."""
        df = pd.DataFrame(
            {
                "Energy": np.arange(100).astype(np.float64),
                "Intensity_1": np.random.rand(100),
                "Intensity_2": np.random.rand(100),
                "Intensity_3": np.random.rand(100),
                "Intensity_4": np.random.rand(100),
            }
        )
        args = {
            "autopeak": False,
            "global_": 0,
            "column": ["Energy", "Intensity_1"],
            **args_setting,
        }
        mp = SolverModels(df=df, args=args)()
        assert_solver_models(mp)

    def test_all_model_global(self, args_setting: Dict[str, Any]) -> None:
        """Test of the AllModel class for global fitting."""
        df = pd.DataFrame(
            {
                "Energy": np.arange(100).astype(np.float64),
                "Intensity_1": np.random.rand(100),
                "Intensity_2": np.random.rand(100),
                "Intensity_3": np.random.rand(100),
                "Intensity_4": np.random.rand(100),
            }
        )
        args = {
            "autopeak": False,
            "global_": 1,
            "column": ["Energy"],
            **args_setting,
        }

        mp = SolverModels(df=df, args=args)()
        assert_solver_models(mp)

    def test_all_model_global_fail(self) -> None:
        """Test of the AllModel class for global fitting."""
        df = pd.DataFrame(
            {
                "Energy": np.arange(100).astype(np.float64),
                "Intensity_1": np.random.rand(100),
                "Intensity_2": np.random.rand(100),
                "Intensity_3": np.random.rand(100),
                "Intensity_4": np.random.rand(100),
            }
        )
        args = {
            "autopeak": True,
            "global_": 1,
            "column": ["Energy"],
            "minimizer": {"nan_policy": "propagate", "calc_covar": False},
            "optimizer": {"max_nfev": 10, "method": "leastsq"},
        }

        with pytest.raises(KeyError) as pytest_wrapped_e:
            _ = SolverModels(
                df=df, args=args
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == KeyError
        assert (
            pytest_wrapped_e.value.args[0]
            == "Global fitting mode with automatic peak detection "
            "is not supported yet."
        )


class TestAutoPeakDetection:
    """Testing of the Auto Peak Detection Class."""

    @staticmethod
    def assert_isinstance(
        peaks: NDArray[np.float64], properties: Dict[str, Any]
    ) -> None:
        """Assert if the peaks and properties are of the correct type."""
        assert isinstance(peaks, np.ndarray)
        assert isinstance(properties, dict)

    def test_key_not_available(self) -> None:
        """Test if the key is not available."""
        args = {"autopeak": True, "global_": 0}
        x = np.arange(0, 10, 0.1)
        data = (
            np.sin(np.arange(0, 10, 0.1)) ** 3 + 2 * np.cos(np.arange(0, 10, 0.1)) ** 2
        )

        auto = AutoPeakDetection(x=x, data=data, args=args)
        _val = auto.check_key_exists(key="missing", args=args, value=2)
        assert _val == 2

    def test_rel_heigh_1(self) -> None:
        """Test if the relative height is calculated correctly."""
        args = {"autopeak": True, "global_": 0}
        x = np.arange(10, dtype=np.float64)
        data = np.arange(10, dtype=np.float64)

        auto = AutoPeakDetection(x=x, data=data, args=args)
        _val = auto.estimated_rel_height
        assert _val == 0.0

    def test_rel_heigh_2(self) -> None:
        """Test if the relative height is calculated correctly."""
        args = {"autopeak": True, "global_": 0}
        x = np.arange(10, dtype=np.float64)
        data = np.sin(10) * np.arange(10, dtype=np.float64)

        auto = AutoPeakDetection(x=x, data=data, args=args)
        _val = auto.estimated_rel_height
        assert _val > 0.0

    def test_plateau_size(self) -> None:
        """Test if the plateau_size is calculated correctly."""
        args = {"autopeak": True, "global_": 0}
        x = np.arange(10, dtype=np.float64)
        data = np.arange(10, dtype=np.float64)

        auto = AutoPeakDetection(x=x, data=data, args=args)
        _val = auto.estimated_plateau_size
        assert _val == (0.0, 9.0)

    def test_distance(self) -> None:
        """Test if the distance is calculated correctly."""
        args = {"autopeak": True, "global_": 0}
        x = 3 * np.arange(10, dtype=np.float64)
        data = 3 * np.exp(10, dtype=np.float64)

        auto = AutoPeakDetection(x=x, data=data, args=args)
        _val = auto.estimate_distance
        assert _val != 1.0

    def test_autopeakdetection_mean(self) -> None:
        """Test of auto default detection with negative values."""
        args = {"autopeak": True, "global_": 0}
        x = np.arange(0, 10, 0.1)
        data = (
            np.sin(np.arange(0, 10, 0.1)) ** 3 + 2 * np.cos(np.arange(0, 10, 0.1)) ** 2
        )

        auto = AutoPeakDetection(x=x, data=data, args=args)
        auto.initialize_peak_detection()
        peaks, properties = auto.__autodetect__()

        self.assert_isinstance(peaks, properties)

    def test_autopeakdetection_hmean(self) -> None:
        """Test of auto default detection only positive values."""
        args = {"autopeak": True}
        df = pd.read_csv("spectrafit/test/import/test_data.csv")
        x, data = df["Energy"].values, df["Noisy_Intensity"].values

        auto = AutoPeakDetection(x=x, data=data, args=args)
        auto.initialize_peak_detection()
        peaks, properties = auto.__autodetect__()

        assert len(peaks) == 21
        self.assert_isinstance(peaks, properties)

    def test_autopeakdetection_userdef(self) -> None:
        """Test of auto default detection with user definitions."""
        args = {
            "autopeak": {
                "height": (0.0, 10),
                "threshold": (0.0, 10),
                "distance": 2,
                "prominence": (0.0, 1.0),
                "width": (0.0, 10),
                "wlen": 20,
                "rel_height": 1,
                "plateau_size": 0.5,
            }
        }
        df = pd.read_csv("spectrafit/test/import/test_data.csv")
        x, data = df["Energy"].values, df["Noisy_Intensity"].values

        auto = AutoPeakDetection(x=x, data=data, args=args)
        auto.initialize_peak_detection()
        peaks, properties = auto.__autodetect__()

        assert len(peaks) == 174
        assert len(properties.keys()) == 13
        self.assert_isinstance(peaks, properties)

    def test_wlen(self) -> None:
        """Test numerical return of wlen."""
        ad = AutoPeakDetection(
            x=np.arange(2, dtype=float),
            data=np.arange(2, dtype=float),
            args={"autopeak": True},
        )
        val = ad.estimated_wlen

        assert val == 1 + 1e-9

    def test_raise_autopeaks(self) -> None:
        """Test raise of AutoPeakDetection."""
        args = {"autopeak": {"no_implimented": 0}}
        with pytest.raises(ValidationError) as excinfo:
            auto = AutoPeakDetection(
                x=np.arange(2, dtype=float), data=np.arange(2, dtype=float), args=args
            )
            auto.initialize_peak_detection()

        assert "no_implimented" in str(excinfo.value)
        assert excinfo.type is ValidationError

    def test_raise_autopeaks_type(self) -> None:
        """Test raise of AutoPeakDetection for wrong type."""
        args = {"autopeak": [{"no_implimented": 0}]}
        with pytest.raises(TypeError) as pytest_wrapped_e:
            auto = AutoPeakDetection(
                x=np.arange(2, dtype=float), data=np.arange(2, dtype=float), args=args
            )
            auto.initialize_peak_detection()

        assert pytest_wrapped_e.type == TypeError

    def test_noraise_autopeaks(self) -> None:
        """Test no raise of AutoPeakDetection."""
        args = {"autopeak": True}
        _ = AutoPeakDetection(
            x=np.arange(2, dtype=float),
            data=np.arange(2, dtype=float),
            args=args,
        )

    def test_autopeakdetection_userdef_voigt(self) -> None:
        """Test of auto default detection with voigt model."""
        args = {
            "global_": 0,
            "column": ["Energy", "Noisy_Intensity"],
            "autopeak": {
                "modeltype": "voigt",
                "height": (0.0, 10),
                "threshold": (0.0, 10),
                "distance": 2,
                "prominence": (0.0, 1.0),
                "width": (0.0, 10),
                "wlen": 20,
                "rel_height": 1,
                "plateau_size": 0.5,
            },
        }
        df = pd.read_csv("spectrafit/test/import/test_data.csv")

        mp = ModelParameters(df=df, args=args)
        mp.__perform__()
        assert len(mp.return_params.keys()) == 522

    def test_autopeakdetection_userdef_pseudovoigt(self) -> None:
        """Test of auto default detection with pseudovoigt model."""
        args = {
            "global_": 0,
            "column": ["Energy", "Noisy_Intensity"],
            "autopeak": {
                "modeltype": "pseudovoigt",
                "height": (0.0, 10),
                "threshold": (0.0, 10),
                "distance": 2,
                "prominence": (0.0, 1.0),
                "width": (0.0, 10),
                "wlen": 20,
                "rel_height": 1,
                "plateau_size": 0.5,
            },
        }
        df = pd.read_csv("spectrafit/test/import/test_data.csv")

        mp = ModelParameters(df=df, args=args)
        mp.__perform__()
        assert len(mp.return_params.keys()) > 0

    def test_autopeakdetection_userdef_lorentzian(self) -> None:
        """Test of auto default detection with lorentzian model."""
        args = {
            "global_": 0,
            "column": ["Energy", "Noisy_Intensity"],
            "autopeak": {
                "modeltype": "lorentzian",
                "height": (0.0, 10),
                "threshold": (0.0, 10),
                "distance": 2,
                "prominence": (0.0, 1.0),
                "width": (0.0, 10),
                "wlen": 20,
                "rel_height": 1,
                "plateau_size": 0.5,
            },
        }
        df = pd.read_csv("spectrafit/test/import/test_data.csv")

        mp = ModelParameters(df=df, args=args)
        mp.__perform__()
        assert len(mp.return_params.keys()) > 0

    def test_autopeakdetection_userdef_default(self) -> None:
        """Test of auto specific detection with default model."""
        args = {
            "global_": 0,
            "column": ["Energy", "Noisy_Intensity"],
            "autopeak": {
                "height": (0.0, 10),
                "threshold": (0.0, 10),
                "distance": 2,
                "prominence": (0.0, 1.0),
                "width": (0.0, 10),
                "wlen": 20,
                "rel_height": 1,
                "plateau_size": 0.5,
            },
        }
        df = pd.read_csv("spectrafit/test/import/test_data.csv")

        mp = ModelParameters(df=df, args=args)
        mp.__perform__()
        assert len(mp.return_params.keys()) == 522

    def test_autopeakdetection_userdef_failmodel(self) -> None:
        """Test of auto specific detection with wrong model."""
        args = {
            "global_": 0,
            "column": ["Energy", "Noisy_Intensity"],
            "autopeak": {
                "modeltype": "nomodel",
                "height": (0.0, 10),
                "threshold": (0.0, 10),
                "distance": 2,
                "prominence": (0.0, 1.0),
                "width": (0.0, 10),
                "wlen": 20,
                "rel_height": 1,
                "plateau_size": 0.5,
            },
        }
        df = pd.read_csv("spectrafit/test/import/test_data.csv")

        with pytest.raises(KeyError) as pytest_wrapped_e:
            mp = ModelParameters(df=df, args=args)
            mp.__perform__()
        # peaks, properties = auto.__autodetect__()
        assert pytest_wrapped_e.type == KeyError


class TestModel:
    """Test the distribution class and its models."""

    @pytest.fixture
    def x_data(self) -> NDArray[np.float64]:
        """Create x data."""
        return np.linspace(0, 10, 100, dtype=float)

    @pytest.fixture
    def df_data(self) -> pd.DataFrame:
        """Create x,y data."""
        return pd.DataFrame(
            {
                "Energy": np.linspace(0, 10, 100, dtype=float),
                "Intensity": np.linspace(0, 10, 100, dtype=float),
            }
        )

    @pytest.mark.parametrize(
        "model, params",
        [
            ("gaussian", {"amplitude": 1.0, "center": 5.0, "fwhmg": 1.0}),
            ("lorentzian", {"amplitude": 1.0, "center": 5.0, "fwhml": 1.0}),
            ("voigt", {"center": 5.0, "fwhmv": 1.0, "gamma": 1}),
            (
                "pseudovoigt",
                {"amplitude": 1.0, "center": 5.0, "fwhmg": 1, "fwhml": 1.0},
            ),
            ("exponential", {"amplitude": 1.0, "decay": 1, "intercept": 1.0}),
            ("power", {"amplitude": 1.0, "exponent": 1.0, "intercept": 1.0}),
            ("linear", {"slope": 1.0, "intercept": 1.0}),
            ("constant", {"amplitude": 1.0}),
            ("erf", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("heaviside", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("atan", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("log", {"amplitude": 1.0, "center": 5.0, "sigma": 1.0}),
            ("cgaussian", {"amplitude": 1.0, "center": 5.0, "fwhmg": 1.0}),
            ("clorentzian", {"amplitude": 1.0, "center": 5.0, "fwhml": 1.0}),
            ("cvoigt", {"amplitude": 1.0, "center": 5.0, "fwhmv": 1.0}),
            (
                "polynom2",
                {"coefficient0": 1.0, "coefficient1": 1.0, "coefficient2": 1.0},
            ),
            (
                "polynom3",
                {
                    "coefficient0": 1.0,
                    "coefficient1": 1.0,
                    "coefficient2": 1.0,
                    "coefficient3": 1.0,
                },
            ),
            (
                "pearson1",
                {"amplitude": 1.0, "center": 5.0, "sigma": 1.0, "exponent": 1.0},
            ),
            (
                "pearson2",
                {"amplitude": -1.0, "center": 2.5, "sigma": 1.2, "exponent": -1.0},
            ),
            (
                "pearson3",
                {
                    "amplitude": 1.0,
                    "center": 5.0,
                    "sigma": 1.0,
                    "exponent": 1.0,
                    "skewness": 1.0,
                },
            ),
            (
                "pearson4",
                {
                    "amplitude": 1.0,
                    "center": 5.0,
                    "sigma": -1.0,
                    "exponent": 1.0,
                    "skewness": -1.0,
                    "kurtosis": 1.0,
                },
            ),
        ],
    )
    def test_distrubtion_models(
        self, x_data: NDArray[np.float64], model: str, params: Dict[str, float]
    ) -> None:
        """Test of all distribution models."""
        y_data = getattr(DistributionModels(), model)(x_data, **params)
        assert isinstance(y_data, np.ndarray)
        assert len(y_data) == 100

    @pytest.mark.parametrize(
        "model, params",
        [
            ("gaussian", {"amplitude": {}, "center": {}, "fwhmg": {}}),
            ("lorentzian", {"amplitude": {}, "center": {}, "fwhml": {}}),
            ("voigt", {"center": {}, "fwhmv": {}, "gamma": {}}),
            (
                "pseudovoigt",
                {"amplitude": {}, "center": {}, "fwhmg": {}, "fwhml": {}},
            ),
            ("exponential", {"amplitude": {}, "decay": {}, "intercept": {}}),
            ("power", {"amplitude": {}, "exponent": {}, "intercept": {}}),
            ("linear", {"slope": {}, "intercept": {}}),
            ("constant", {"amplitude": {}}),
            ("erf", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("heaviside", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("atan", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("log", {"amplitude": {}, "center": {}, "sigma": {}}),
            ("cgaussian", {"amplitude": {}, "center": {}, "fwhmg": {}}),
            ("clorentzian", {"amplitude": {}, "center": {}, "fwhml": {}}),
            ("cvoigt", {"amplitude": {}, "center": {}, "fwhmv": {}}),
            (
                "polynom2",
                {"coefficient0": {}, "coefficient1": {}, "coefficient2": {}},
            ),
            (
                "polynom3",
                {
                    "coefficient0": {},
                    "coefficient1": {},
                    "coefficient2": {},
                    "coefficient3": {},
                },
            ),
            (
                "pearson1",
                {"amplitude": {}, "center": {}, "sigma": {}, "exponent": {}},
            ),
            (
                "pearson2",
                {"amplitude": {}, "center": {}, "sigma": {}, "exponent": {}},
            ),
            (
                "pearson3",
                {
                    "amplitude": {},
                    "center": {},
                    "sigma": {},
                    "exponent": {},
                    "skewness": {},
                },
            ),
            (
                "pearson4",
                {
                    "amplitude": {},
                    "center": {},
                    "sigma": {},
                    "exponent": {},
                    "skewness": {},
                    "kurtosis": {},
                },
            ),
        ],
    )
    def test_model_exitst(
        self, df_data: pd.DataFrame, model: str, params: Dict[str, Dict[Any, Any]]
    ) -> None:
        """Test if the model exists."""
        args = {
            "global_": 0,
            "autopeak": False,
            "column": ["Energy", "Intensity"],
            "minimizer": {"nan_policy": "propagate", "calc_covar": False},
            "optimizer": {"max_nfev": 10, "method": "leastsq"},
            "peaks": {"1": {model: params}},
        }
        mp = SolverModels(df=df_data, args=args)()

        assert_solver_models(mp)
        assert len(mp) == 2
        for name in mp[0].params.keys():
            assert model in name

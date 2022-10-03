"""Pytest of the model-module."""
import numpy as np
import pandas as pd
import pytest

from lmfit import Parameters
from pydantic import ValidationError
from spectrafit.models import AutoPeakDetection
from spectrafit.models import Constants
from spectrafit.models import ModelParameters
from spectrafit.models import SolverModels
from spectrafit.models import calculated_model


class TestConstants:
    """Test constants."""

    def test_log2(self) -> None:
        """Test the Constants class."""
        assert Constants.log2 == np.log(2)

    def test_sq2pi(self) -> None:
        """Test the Constants class."""
        assert Constants.sq2pi == np.sqrt(2.0 * np.pi)

    def test_sqpi(self) -> None:
        """Test the Constants class."""
        assert Constants.sqpi == np.sqrt(np.pi)

    def test_sq2(self) -> None:
        """Test the Constants class."""
        assert Constants.sq2 == np.sqrt(2.0)

    def test_sig2fwhm(self) -> None:
        """Test the Constants class."""
        assert Constants.sig2fwhm == 2.0 * np.sqrt(2.0 * np.log(2.0))


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
        with pytest.raises(KeyError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df, args=self.args
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == KeyError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1 is not supported!"

    def test_solver_model_exit_global(self) -> None:
        """Exit-Test of solver_model for global fitting."""
        _args = self.args
        _args["global_"] = 1
        with pytest.raises(KeyError) as pytest_wrapped_e:
            _ = SolverModels(
                df=self.df, args=_args
            )().will_exit_somewhere_down_the_stack()  # type: ignore

        assert pytest_wrapped_e.type == KeyError
        assert pytest_wrapped_e.value.args[0] == "dummy_amplitude_1_1 is not supported!"

    def test_calculated_model_exit(self) -> None:
        """Exit-Test of solver_model."""
        params = Parameters()
        params.add("dummy_amplitude_1", value=1.0)
        with pytest.raises(KeyError) as pytest_wrapped_e:
            calculated_model(
                params=params,
                x=self.df["energy"].values,
                df=self.df["intensity"].values,
                global_fit=0,
            ).will_exit_somewhere_down_the_stack()
        assert pytest_wrapped_e.type == KeyError
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
                            "value": 0.1,
                        },
                        "fwhml": {
                            "max": 2.5,
                            "min": 0.00001,
                            "vary": True,
                            "value": 1,
                        },
                    }
                },
                "2": {
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
        assert type(mp.__str__()) == str

    def test_param_return(self) -> None:
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert str(type(mp.return_params)) == "<class 'lmfit.parameter.Parameters'>"

    def test_len_param_normal(self) -> None:
        """Test of length of the paramaters for normal fitting."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert len(mp.return_params.keys()) == 8

    def test_len_param_global_1(self) -> None:
        """Test of length of the paramaters for global fitting."""
        mp = ModelParameters(df=self.df_global, args=self.args_global_1)
        mp.define_parameters_global()
        assert len(mp.return_params.keys()) == 32

    def test_solver_local(self) -> None:
        """Test of SolverModels for local fitting."""
        mp = SolverModels(df=self.df, args=self.args)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

    def test_solver_global_1(self) -> None:
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_1)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

    def test_solver_global_2(self) -> None:
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_2)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

    def test_all_model_local(self) -> None:
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
        mp = SolverModels(df=df, args=args)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

    def test_all_model_global(self) -> None:
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

        mp = SolverModels(df=df, args=args)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

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
        x = np.arange(10)
        data = np.arange(10)

        auto = AutoPeakDetection(x=x, data=data, args=args)
        _val = auto.estimated_rel_height
        assert _val == 0.0

    def test_rel_heigh_2(self) -> None:
        """Test if the relative height is calculated correctly."""
        args = {"autopeak": True, "global_": 0}
        x = np.arange(10)
        data = np.sin(10) * np.arange(10)

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

        assert type(peaks) == np.ndarray
        assert type(properties) == dict

    def test_autopeakdetection_hmean(self) -> None:
        """Test of auto default detection only positive values."""
        args = {"autopeak": True}
        df = pd.read_csv("spectrafit/test/import/test_data.csv")
        x, data = df["Energy"].values, df["Noisy_Intensity"].values

        auto = AutoPeakDetection(x=x, data=data, args=args)
        auto.initialize_peak_detection()
        peaks, properties = auto.__autodetect__()

        assert type(peaks) == np.ndarray
        assert len(peaks) == 21
        assert type(properties) == dict

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

        assert type(peaks) == np.ndarray
        assert len(peaks) == 174
        assert type(properties) == dict
        assert len(properties.keys()) == 13

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
            _, _ = auto.__autodetect__()

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
            peaks, properties = auto.__autodetect__()

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
                "model_type": "voigt",
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
                "model_type": "pseudovoigt",
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
                "model_type": "lorentzian",
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
                "model_type": "nomodel",
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

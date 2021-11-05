"""Pytest of the model-module."""
import numpy as np
import pandas as pd
import pytest

from lmfit import Parameters
from spectrafit.models import Constants
from spectrafit.models import ModelParameters
from spectrafit.models import SolverModels
from spectrafit.models import calculated_model


class TestConstants:
    """Test constants."""

    def test_log2(self):
        """Test the Constants class."""
        assert Constants.log2 == np.log(2)

    def test_sq2pi(self):
        """Test the Constants class."""
        assert Constants.sq2pi == np.sqrt(2.0 * np.pi)

    def test_sqpi(self):
        """Test the Constants class."""
        assert Constants.sqpi == np.sqrt(np.pi)

    def test_sq2(self):
        """Test the Constants class."""
        assert Constants.sq2 == np.sqrt(2.0)

    def test_sig2fwhm(self):
        """Test the Constants class."""
        assert Constants.sig2fwhm == 2.0 * np.sqrt(2.0 * np.log(2.0))


class TestNotSupported:
    """Test of not supported models."""

    args = {
        "column": ["energy", "intensity"],
        "global": 0,
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

    def test_solver_model_exit(self):
        """Exit-Test of solver_model."""
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            SolverModels(
                df=self.df, args=self.args
            )().will_exit_somewhere_down_the_stack()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == "dummy_amplitude_1 is not supported"

    def test_calculated_model_exit(self):
        """Exit-Test of solver_model."""
        params = Parameters()
        params.add("dummy_amplitude_1", value=1.0)
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            calculated_model(
                params=params,
                x=self.df["energy"].values,
                df=self.df["intensity"].values,
                global_fit=0,
            ).will_exit_somewhere_down_the_stack()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == "dummy_amplitude_1 is not supported"


class TestModelParametersSolver:
    """Test of model parameters."""

    args = {
        "global": 0,
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
        "global": 1,
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
        "global": 2,
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

    def test_str_return(self):
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert type(mp.__str__()) == str

    def test_param_return(self):
        """Test of str-return."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert str(type(mp.return_params)) == "<class 'lmfit.parameter.Parameters'>"

    def test_len_param_normal(self):
        """Test of length of the paramaters for normal fitting."""
        mp = ModelParameters(df=self.df, args=self.args)
        mp.define_parameters()
        assert len(mp.return_params.keys()) == 8

    def test_len_param_global_1(self):
        """Test of length of the paramaters for global fitting."""
        mp = ModelParameters(df=self.df_global, args=self.args_global_1)
        mp.define_parameters_global()
        assert len(mp.return_params.keys()) == 32

    def test_solver_local(self):
        """Test of SolverModels for local fitting."""
        mp = SolverModels(df=self.df, args=self.args)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

    def test_solver_global_1(self):
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_1)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

    def test_solver_global_2(self):
        """Test of SolverModels for global fitting."""
        mp = SolverModels(df=self.df_global, args=self.args_global_2)()
        assert type(mp.__str__()) == str
        assert type(mp) == tuple

"""Pytest of the model-module."""
import numpy as np
import pandas as pd
import pytest

from spectrafit.models import Constants
from spectrafit.models import calculated_model
from spectrafit.models import solver_model


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

    def test_solver_model_exit(self):
        """Exit-Test of solver_model."""
        params: dict = {"dummy_amplitude_"}
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            solver_model(
                params=params,
                x=np.arange(10, dtype=np.float),
                data=np.random.random_sample((10,)),
            ).will_exit_somewhere_down_the_stack()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == "dummy_amplitude_ is not supported"

    def test_calculated_model_exit(self):
        """Exit-Test of solver_model."""
        params: dict = {"dummy_amplitude_"}
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            calculated_model(
                params=params,
                x=np.arange(10, dtype=np.float),
                df=pd.DataFrame({"intensity": np.random.random_sample((10,))}),
            ).will_exit_somewhere_down_the_stack()
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == "dummy_amplitude_ is not supported"

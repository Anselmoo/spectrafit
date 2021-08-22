"""Pytest of the model-module."""
import numpy as np

from spectrafit.models import Constants


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

"""Tests for the SpectraFit __init__.py file."""

import importlib
import sys
import warnings

import spectrafit

from pytest import MonkeyPatch
from spectrafit import PYTHON_38_VERSION
from spectrafit import __version__


def test_version() -> None:
    """Test the version string."""
    assert __version__ == "1.2.2"


def test_python_38_warning(monkeypatch: MonkeyPatch) -> None:
    """Test that a warning is issued for Python 3.8."""
    # Set the Python version to 3.8
    monkeypatch.setattr(sys, "version_info", (3, 8, 0))

    version_str = f"{PYTHON_38_VERSION[0]}.{PYTHON_38_VERSION[1]}"

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Reload the module to trigger the warning
        importlib.reload(spectrafit)

        # Check that a warning was issued
        assert len(w) == 1
        assert issubclass(w[-1].category, DeprecationWarning)
        assert (
            f"Support for Python {version_str} is approaching its end-of-life."
            in str(w[-1].message)
        )


def test_no_warning_for_other_versions(monkeypatch: MonkeyPatch) -> None:
    """Test that no warning is issued for Python versions other than 3.8."""
    # Set the Python version to 3.9
    monkeypatch.setattr(sys, "version_info", (3, 9, 0))

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        # Reload the module to ensure no warning is triggered
        importlib.reload(spectrafit)

        # Check that no warning was issued
        assert len(w) == 0

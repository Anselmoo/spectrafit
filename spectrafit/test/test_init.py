"""Tests for the SpectraFit __init__.py file."""

from __future__ import annotations

import importlib
import sys
import warnings

from typing import TYPE_CHECKING

# Need to import pytest for runtime usage with MonkeyPatch
import pytest  # noqa: TC002 (needed at runtime for MonkeyPatch)


if TYPE_CHECKING:
    from types import ModuleType


def reload_spectrafit() -> ModuleType:
    """Reload or import spectrafit to evaluate import-time warnings.

    Returns:
        ModuleType: The reloaded module when already imported, otherwise a
            freshly imported module.

    """
    if "spectrafit" in sys.modules:
        return importlib.reload(sys.modules["spectrafit"])
    return importlib.import_module("spectrafit")


def test_version() -> None:
    """Test that the package __version__ matches the installed distribution version."""
    from importlib.metadata import version as pkg_version

    from spectrafit import __version__

    assert __version__ == pkg_version("spectrafit")


def test_package_lifecycle_warning() -> None:
    """Test that a lifecycle warning is issued when SpectraFit is imported."""
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        module = reload_spectrafit()

    assert any(
        issubclass(warning.category, FutureWarning)
        and module.PACKAGE_LIFECYCLE_NOTICE in str(warning.message)
        for warning in captured
    )


def test_python_end_of_life_warning(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a warning is issued for Python 3.9."""
    module = importlib.import_module("spectrafit")

    # Set the Python version to 3.9
    monkeypatch.setattr(sys, "version_info", (3, 9, 0))

    version_str = f"{module.PYTHON_END_OF_LIFE[0]}.{module.PYTHON_END_OF_LIFE[1]}"

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        # Reload the module to trigger the warning
        module = reload_spectrafit()

    assert any(
        issubclass(warning.category, FutureWarning)
        and module.PACKAGE_LIFECYCLE_NOTICE in str(warning.message)
        for warning in captured
    )
    assert any(
        issubclass(warning.category, DeprecationWarning)
        and f"Support for Python {version_str} is approaching its end-of-life."
        in str(warning.message)
        for warning in captured
    )


def test_no_warning_for_other_versions(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that only the lifecycle warning is issued for Python versions other than 3.9."""
    module = importlib.import_module("spectrafit")

    # Set the Python version to 3.10
    monkeypatch.setattr(sys, "version_info", (3, 10, 0))

    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        # Reload the module to ensure only the lifecycle warning is triggered
        module = reload_spectrafit()

    assert any(
        issubclass(warning.category, FutureWarning)
        and module.PACKAGE_LIFECYCLE_NOTICE in str(warning.message)
        for warning in captured
    )
    assert not any(
        issubclass(warning.category, DeprecationWarning) for warning in captured
    )

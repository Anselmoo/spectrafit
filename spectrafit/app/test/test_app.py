"""Test of the Jupiter plugin app."""

from __future__ import annotations

import sys

from unittest import mock

import pytest

from spectrafit.app import app


@pytest.mark.skipif(
    sys.version_info[:2] == (3, 8), reason="Test not supported on Python 3.8"
)
def test_jupyter() -> None:
    """Test the jupyter plugin app."""
    with (
        mock.patch.object(app, "__name__", "__main__"),
        mock.patch.object(app, "sys"),
        mock.patch.object(app, "main"),
    ):
        app.__app__()
        app.sys.exit.assert_called_once_with(app.main())  # type: ignore

"""Test of the Jupiter plugin app."""

from __future__ import annotations

from unittest import mock

import pytest

from spectrafit.app import app


pytestmark = pytest.mark.unit


def test_jupyter() -> None:
    """Test the jupyter plugin app."""
    with (
        mock.patch.object(app, "__name__", "__main__"),
        mock.patch.object(app, "sys"),
        mock.patch.object(app, "main"),
    ):
        app.__app__()
        app.sys.exit.assert_called_once_with(app.main())  # type: ignore

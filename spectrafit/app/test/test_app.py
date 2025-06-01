"""Test of the Jupiter plugin app."""

from __future__ import annotations

from unittest import mock

from spectrafit.app import app


def test_jupyter() -> None:
    """Test the jupyter plugin app."""
    with (
        mock.patch.object(app, "__name__", "__main__"),
        mock.patch.object(app, "sys"),
        mock.patch.object(app, "main"),
    ):
        app.__app__()
        app.sys.exit.assert_called_once_with(app.main())  # type: ignore

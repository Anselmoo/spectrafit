"""Test of the Jupiter plugin app."""
import mock


def test_jupyter() -> None:
    """Test the jupyter plugin app."""
    from spectrafit.app import app

    with mock.patch.object(app, "__name__", "__main__"):
        with mock.patch.object(app, "sys"):
            with mock.patch.object(app, "main"):
                app.__app__()
                app.sys.exit.assert_called_once_with(app.main())

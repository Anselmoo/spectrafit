"""Starting jupyter lab as a app."""


import sys

from jupyterlab.labapp import main


def jupyter() -> None:
    """Run jupyter lab as app in the absence of token."""
    sys.argv.extend(
        [
            "--NotebookApp.token=''",
            "--NotebookApp.password=''",
            "--ServerApp.allow_remote_access=True",
            "--ServerApp.allow_origin='*'",
            "--ServerApp.allow_root=True",
            "--ServerApp.port=8888",
        ]
    )
    sys.exit(main())


def __app__() -> None:
    """Run jupyter lab as app if file is run as main."""
    if __name__ == "__main__":
        jupyter()


__app__()

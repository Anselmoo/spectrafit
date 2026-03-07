"""Start JupyterLab as an app.

Entry point registered as ``spectrafit-jupyter`` in ``pyproject.toml``.
"""

from __future__ import annotations

import sys

from jupyterlab.labapp import main


def jupyter() -> None:
    """Run JupyterLab in token-less server mode.

    Configures JupyterLab with open access settings suitable for a local
    fitting session and delegates to the standard JupyterLab launcher.
    """
    sys.argv.extend(
        [
            "--NotebookApp.token=''",
            "--NotebookApp.password=''",
            "--ServerApp.allow_remote_access=True",
            "--ServerApp.allow_origin='*'",
            "--ServerApp.allow_root=True",
            "--ServerApp.port=8888",
        ],
    )
    sys.exit(main())

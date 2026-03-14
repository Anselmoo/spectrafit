"""Start JupyterLab as an app.

Entry point registered as ``spectrafit-jupyter`` in ``pyproject.toml``.
"""

from __future__ import annotations

import sys

from typing import TYPE_CHECKING

from jupyterlab.labapp import main


if TYPE_CHECKING:
    from pathlib import Path


def jupyter(notebook_file: Path | None = None) -> None:
    """Run JupyterLab in token-less server mode.

    Resets ``sys.argv`` so that JupyterLab's argument parser sees only the
    server configuration options — not the leftover ``spectrafit jupyter``
    CLI tokens that would be misinterpreted as file-path arguments.

    Args:
        notebook_file: Optional path to a ``.ipynb`` file to open on launch.
            When *None* JupyterLab opens in the current working directory.
    """
    # Replace sys.argv entirely: keep only argv[0] (script name) so that
    # JupyterLab's main() does not misinterpret the CLI subcommand tokens
    # (e.g. "jupyter") as a notebook path to open.
    new_argv: list[str] = [sys.argv[0]]
    if notebook_file is not None:
        new_argv.append(str(notebook_file))
    new_argv.extend(
        [
            "--NotebookApp.token=''",
            "--NotebookApp.password=''",
            "--ServerApp.allow_remote_access=True",
            "--ServerApp.allow_origin='*'",
            "--ServerApp.allow_root=True",
            "--ServerApp.port=8888",
        ],
    )
    sys.argv = new_argv
    raise SystemExit(
        main()
    )  # intentional: CLI entry point, propagates Jupyter server exit code

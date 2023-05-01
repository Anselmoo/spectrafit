"""SpectraFit, fast command line tool for fitting data."""
from pathlib import Path

import tomli


with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
    pyproject = tomli.load(f)
    __version__ = pyproject["tool"]["poetry"]["version"]

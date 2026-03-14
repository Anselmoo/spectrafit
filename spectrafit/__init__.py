"""SpectraFit, fast command line tool for fitting data.

!!! info "About Versioning"

    SpectraFit uses [Semantic Versioning](https://semver.org/).

!!! warning "About Python Versions"

    SpectraFit targets Python 3.12 and above. Python 3.11 and older are no longer
    supported, see also
    [Release Schedule](https://devguide.python.org/versions/#end-of-life-branches).
"""

from __future__ import annotations

import sys
import warnings

from typing import Literal


PYTHON_END_OF_LIFE: tuple[Literal[3], Literal[11]] = (3, 11)

if sys.version_info[:2] == PYTHON_END_OF_LIFE:
    version_str = f"{PYTHON_END_OF_LIFE[0]}.{PYTHON_END_OF_LIFE[1]}"
    warnings.warn(
        f"Support for Python {version_str} is approaching its end-of-life."
        " Please consider upgrading to Python 3.12 or newer."
        " For more details, see:"
        "https://devguide.python.org/versions/#end-of-life-branches.",
        DeprecationWarning,
        stacklevel=2,
    )

__version__ = "2.0.0"

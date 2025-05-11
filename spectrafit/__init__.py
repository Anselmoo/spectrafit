"""SpectraFit, fast command line tool for fitting data.

!!! info "About Versioning"

    SpectraFit uses [Semantic Versioning](https://semver.org/).

!!! warning "About Python Versions"

    Currently, SpectraFit only supports Python 3.8 and above. Soon, Python 3.8
    will be deprecated in favor of Python 3.9 and above, see also
    [Release Schedule](https://devguide.python.org/versions/#end-of-life-branches).
"""

from __future__ import annotations

import sys
import warnings
from typing import Tuple

from typing_extensions import Literal

PYTHON_END_OF_LIFE: Tuple[Literal[3], Literal[8]] = (3, 8)

if sys.version_info[:2] == PYTHON_END_OF_LIFE:
    version_str = f"{PYTHON_END_OF_LIFE[0]}.{PYTHON_END_OF_LIFE[1]}"
    warnings.warn(
        f"Support for Python {version_str} is approaching its end-of-life."
        " Please consider upgrading to Python 3.9 or newer."
        " For more details, see:"
        "https://devguide.python.org/versions/#end-of-life-branches.",
        DeprecationWarning,
        stacklevel=2,
    )

__version__ = "1.3.1"

"""SpectraFit, fast command line tool for fitting data.

!!! info "About Versioning"

    SpectraFit uses [Semantic Versioning](https://semver.org/).

!!! warning "About Python Versions"

    Currently, SpectraFit only supports Python 3.8 and above. Soon, Python 3.8
    will be deprecated in favor of Python 3.9 and above, see also
    [Release Schedule](https://devguide.python.org/versions/#end-of-life-branches).
"""

import sys
import warnings


if sys.version_info[:2] == (3, 8):
    warnings.warn(
        "Support for Python 3.8 is approaching its end-of-life. "
        "Please consider upgrading to Python 3.9 or newer. "
        "For more details, see: "
        "https://devguide.python.org/versions/#end-of-life-branches.",
        DeprecationWarning,
    )

__version__ = "1.0.4"

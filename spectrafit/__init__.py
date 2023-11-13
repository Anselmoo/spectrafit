"""SpectraFit, fast command line tool for fitting data.

!!! info "About Versioning"

    SpectraFit uses [Semantic Versioning](https://semver.org/).

!!! info "About the Font Cache"

    For avoiding problems with the font cache, the font cache is rebuilt at the
    beginning of the program. This can take a few seconds. If you want to avoid
    this, you can comment out the line `matplotlib.font_manager._rebuild()` in
    the `__init__.py` file.

"""


__version__ = "1.0.0"

import matplotlib.font_manager


matplotlib.font_manager.findfont("serif", rebuild_if_missing=True)

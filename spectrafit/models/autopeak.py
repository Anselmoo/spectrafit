"""Model parameter definition for curve fitting — backward-compat re-export shim.

.. deprecated:: 2.0.0
   All symbols in this module have been moved to purpose-built modules.
   Import directly from the new locations instead:

   - TypeAliases → :mod:`spectrafit.models.types`
   - :class:`ModelParameters` → :mod:`spectrafit.models.model_parameters`
   - :class:`ReferenceKeys` → :mod:`spectrafit.models.model_parameters`
   - :class:`FittingMode` → :mod:`spectrafit.models.fitting_context`

   This shim will be removed in v2.1.0.

AutoPeak detection has been removed in v2.0.0 and will be redesigned.
"""

from __future__ import annotations

import warnings

from spectrafit.models.model_parameters import ModelParameters  # noqa: F401
from spectrafit.models.model_parameters import ReferenceKeys  # noqa: F401
from spectrafit.models.types import FittingArgs  # noqa: F401
from spectrafit.models.types import ModelParameterSpec  # noqa: F401
from spectrafit.models.types import ParameterConstraint  # noqa: F401
from spectrafit.models.types import PeakModelSpec  # noqa: F401
from spectrafit.models.types import PeaksDict  # noqa: F401


warnings.warn(
    "spectrafit.models.autopeak is deprecated and will be removed in v2.1.0. "
    "Import from spectrafit.models.types, spectrafit.models.model_parameters, "
    "or spectrafit.models.global_fitting instead.",
    DeprecationWarning,
    stacklevel=2,
)

GLOBAL_NONE = 0  # Formerly GlobalMode.NONE — standard single-dataset fit
GLOBAL_STANDARD = 1  # Formerly GlobalMode.STANDARD — multi-dataset global fit
GLOBAL_WITH_PRE = 2  # Formerly GlobalMode.WITH_PRE — global fit with pre-defined params

_MIN_DATASETS_FOR_SHARING = 2

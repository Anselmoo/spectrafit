"""CompositeModelBundle — lmfit model composition and component decomposition.

This module provides the bridge between a list of :class:`~spectrafit.models.peak_models.Component`
objects and a single lmfit ``CompositeModel`` that can be handed to the
numerical optimiser.

The central design principle is **lmfit-native composition**:
``model_all = model_1 + model_2 + ... + model_n`` using lmfit's own
``__add__`` operator.  This gives us:

- Automatic composite parameter namespace (all prefixed by component id).
- Cross-component ``expr`` constraints handled natively by lmfit's
  ``asteval`` engine.
- Per-component curve recovery via ``model.eval(result.params, x=x)``
  — no duplicate evaluation loop.

Usage example
-------------
.. code-block:: python

    from spectrafit.models.peak_models import Component, FitParameter
    from spectrafit.models.bundle import build_composite_bundle

    components = [
        Component(id="p1", model="gaussian",
                  parameters={"amplitude": FitParameter(value=1.0, min=0.0, max=2.0),
                               "center": FitParameter(value=0.0),
                               "fwhmg": FitParameter(value=0.3)}),
        Component(id="bg", model="linear",
                  parameters={"slope": FitParameter(value=0.0, vary=False),
                               "intercept": FitParameter(value=0.0)}),
    ]

    bundle = build_composite_bundle(components)
    params = bundle.make_params()          # all component defaults merged
    result = bundle.composite.fit(y, params, x=x)
    curves = bundle.decompose(result.params, x)  # {"p1": array, "bg": array}
"""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

import numpy as np


if TYPE_CHECKING:
    import lmfit

    from numpy.typing import NDArray

    from spectrafit.models.peak_models import Component


@dataclass
class CompositeModelBundle:
    """A fully-assembled lmfit composite model with decomposition support.

    Args:
        composite: The composite lmfit model (``m1 + m2 + ...``).  Pass
            this to ``composite.fit(data, params, x=x)``.
        params: Merged ``lmfit.Parameters`` with all component defaults
            pre-applied by :func:`build_composite_bundle`.
        parts: Ordered list of ``(component_id, lmfit.Model)`` pairs
            retained for per-component curve recovery.
    """

    composite: lmfit.Model
    params: lmfit.Parameters
    parts: list[tuple[str, lmfit.Model]] = field(default_factory=list)

    def decompose(
        self,
        result_params: lmfit.Parameters,
        x: NDArray[np.float64],
    ) -> dict[str, NDArray[np.float64]]:
        """Evaluate each component individually using fitted parameters.

        Replaces the manual per-component re-evaluation loop that existed
        in the old pipeline.  Each component's curve is ``model.eval()``
        called with the full ``result_params`` dict — lmfit handles prefix
        resolution automatically.

        Args:
            result_params: The ``result.params`` from a completed fit.
            x: Independent-variable array.

        Returns:
            Mapping of ``{component_id: component_curve_array}``.

        Examples:
            >>> bundle = build_composite_bundle(components)
            >>> result = bundle.composite.fit(y, bundle.params, x=x)
            >>> curves = bundle.decompose(result.params, x)
            >>> set(curves.keys()) == {c.id for c in components}
            True
        """
        return {
            comp_id: np.asarray(model.eval(result_params, x=x))
            for comp_id, model in self.parts
        }


def build_composite_bundle(
    components: list[Component],
) -> CompositeModelBundle:
    """Build a :class:`CompositeModelBundle` from a list of components.

    Steps:
    1. For each component, call :meth:`~spectrafit.models.peak_models.Component.to_lmfit_model`
       to create an ``lmfit.Model`` with the correct prefix.
    2. Merge all component models with lmfit's ``__add__`` operator.
    3. Call ``composite.make_params()`` to get default parameters.
    4. For each component, call
       :meth:`~spectrafit.models.peak_models.Component.apply_parameters`
       to override defaults with user constraints.

    Args:
        components: Non-empty list of :class:`~spectrafit.models.peak_models.Component`
            objects.

    Returns:
        :class:`CompositeModelBundle` with ``composite``, ``parts``, and
        ``params`` fully populated.

    Raises:
        ValueError: If ``components`` is empty.

    Examples:
        >>> bundle = build_composite_bundle([gaussian_comp, bg_comp])
        >>> sorted(bundle.params.keys())
        ['bg_intercept', 'bg_slope', 'p1_amplitude', 'p1_center', 'p1_fwhmg']
    """
    if not components:
        msg = "components must contain at least one Component"
        raise ValueError(msg)

    lm_models: list[tuple[str, lmfit.Model]] = [
        (comp.id, comp.to_lmfit_model()) for comp in components
    ]

    # lmfit's __add__ creates a CompositeModel
    composite = lm_models[0][1]
    for _, m in lm_models[1:]:
        composite = composite + m

    params = composite.make_params()

    for comp in components:
        comp.apply_parameters(params)

    return CompositeModelBundle(
        composite=composite,
        parts=lm_models,
        params=params,
    )

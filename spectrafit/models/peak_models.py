"""Pydantic models for individual fitting components.

This module contains the data layer for the v2.0.0 component-based fitting
pipeline.  It defines two Pydantic models:

- :class:`FitParameter` — validated representation of a single parameter
  constraint (value, min, max, vary, expr).
- :class:`Component` — a named fitting component that maps to one
  :class:`lmfit.Model` instance.

The boundary between Pydantic and lmfit is entirely in this module:
Pydantic validates user input; :meth:`Component.to_lmfit_model` hands
control to lmfit for numerical optimisation.

Naming convention
-----------------
All lmfit parameter names are constructed exclusively via
:func:`~spectrafit.models.naming.lmfit_param_name`.  No inline
``f"{x}_{y}"`` formatting is used anywhere else.
"""

from __future__ import annotations

import math

from typing import TYPE_CHECKING
from typing import Any

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import field_validator
from pydantic import model_validator

from spectrafit.models.naming import lmfit_param_name
from spectrafit.models.naming import sanitize_component_id
from spectrafit.models.naming import translate_dot_notation


if TYPE_CHECKING:
    import lmfit


_BOUNDS_LEN: int = 2  # [min, max] pair expected in v2 bounds shorthand


class FitParameter(BaseModel):
    """Validated representation of a single lmfit parameter constraint.

    Args:
        value: Initial value for the parameter.
        min: Lower bound. Defaults to ``-inf``.
        max: Upper bound. Defaults to ``+inf``.
        vary: Whether to optimize this parameter. Defaults to ``True``.
        expr: Expression for constrained parameters (dot or underscore
            notation, e.g. ``"main.amplitude * 0.5"``).  Dot notation is
            automatically translated to lmfit underscore notation at parse
            time.

    Examples:
        >>> p = FitParameter(value=1.0, min=0.0, max=2.0)
        >>> p.vary
        True
        >>> p = FitParameter(value=0.5, expr="main.amplitude * 0.5")
        >>> p.expr
        'main_amplitude * 0.5'
    """

    model_config = ConfigDict(extra="forbid")

    value: float = 0.0
    min: float = -math.inf
    max: float = math.inf
    vary: bool = True
    expr: str | None = None

    @model_validator(mode="before")
    @classmethod
    def expand_bounds(cls, data: Any) -> Any:
        """Expand ``bounds = [min, max]`` shorthand to ``min``/``max`` fields.

        This allows the v2 TOML schema to use compact inline tables::

            amplitude = { value = 1.0, bounds = [0.0, 3.0], vary = true }

        instead of the verbose form::

            amplitude = { value = 1.0, min = 0.0, max = 3.0, vary = true }

        Args:
            data: Raw input dict or scalar value.

        Returns:
            Dict with ``bounds`` replaced by ``min`` and ``max``.
        """
        if isinstance(data, dict) and "bounds" in data:
            bounds = data["bounds"]
            if isinstance(bounds, (list, tuple)) and len(bounds) == _BOUNDS_LEN:
                data = dict(data)
                data.pop("bounds")
                data.setdefault("min", bounds[0])
                data.setdefault("max", bounds[1])
        return data

    @field_validator("expr", mode="before")
    @classmethod
    def translate_expr(cls, v: str | None) -> str | None:
        """Translate dot notation to lmfit underscore notation.

        Args:
            v: Raw expression string or ``None``.

        Returns:
            Translated expression or ``None``.
        """
        return translate_dot_notation(str(v)) if v is not None else v

    def apply_to(self, params: lmfit.Parameters, lmfit_name: str) -> None:
        """Override the default lmfit parameter with user-supplied constraints.

        Args:
            params: lmfit Parameters object (already populated by
                ``model.make_params()``).
            lmfit_name: Fully-qualified lmfit parameter name
                (e.g. ``"p1_amplitude"``).
        """
        params[lmfit_name].set(
            value=self.value,
            min=self.min,
            max=self.max,
            vary=self.vary,
            expr=self.expr,
        )


class Component(BaseModel):
    """A single fitting component: model type + parameter constraints.

    ``id`` is the namespace root for all lmfit parameter names belonging to
    this component.  The lmfit parameter name for field ``"amplitude"`` of
    component ``"1"`` is ``"p1_amplitude"`` — computed exclusively via
    :func:`~spectrafit.models.naming.lmfit_param_name`.

    Args:
        id: Unique component identifier.  Numeric ids (e.g. ``"1"``) are
            automatically sanitized to ``"p1"`` so they are valid lmfit
            prefixes.
        model: Registry key identifying the model type
            (e.g. ``"gaussian"``, ``"lorentzian"``).
        parameters: Mapping of parameter field name → :class:`FitParameter`.

    Examples:
        >>> from spectrafit.models.peak_models import Component, FitParameter
        >>> comp = Component(
        ...     id="1",
        ...     model="gaussian",
        ...     parameters={
        ...         "amplitude": FitParameter(value=1.0, min=0.0, max=2.0),
        ...         "center": FitParameter(value=0.0, min=-1.0, max=1.0),
        ...         "fwhmg": FitParameter(value=0.3, min=0.1, max=1.0),
        ...     },
        ... )
        >>> comp.id
        'p1'
        >>> from spectrafit.models.naming import lmfit_param_name
        >>> lmfit_param_name(comp.id, "amplitude")
        'p1_amplitude'
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    model: str
    parameters: dict[str, FitParameter] = {}

    @field_validator("id", mode="before")
    @classmethod
    def sanitize_id(cls, v: str) -> str:
        """Ensure the component id is a valid lmfit prefix.

        Args:
            v: Raw id string (may be numeric).

        Returns:
            Sanitized id.
        """
        return sanitize_component_id(v)

    @model_validator(mode="after")
    def validate_model_in_registry(self) -> Component:
        """Check that the model name exists in REGISTRY.

        Returns:
            The validated component.

        Raises:
            ValueError: If the model name is not registered.
        """
        # Import here to avoid circular import at module level
        from spectrafit.models.registry import REGISTRY  # noqa: PLC0415

        if self.model not in REGISTRY:
            available = REGISTRY.names()
            msg = f"Unknown model '{self.model}'. Available models: {available}"
            raise ValueError(msg)
        return self

    def to_lmfit_model(self) -> lmfit.Model:
        """Create an lmfit.Model instance for this component.

        The model is created with the prefix ``f"{self.id}_"`` so that
        lmfit generates parameter names like ``"p1_amplitude"``.

        Returns:
            lmfit.Model instance ready for use in a composite model.

        Examples:
            >>> comp = Component(id="1", model="gaussian", parameters={})
            >>> lm = comp.to_lmfit_model()
            >>> sorted(lm.make_params().keys())
            ['p1_amplitude', 'p1_center', 'p1_fwhmg']
        """
        from spectrafit.models.registry import REGISTRY  # noqa: PLC0415

        return REGISTRY.get(self.model).make_lmfit_model(prefix=f"{self.id}_")

    def apply_parameters(self, params: lmfit.Parameters) -> None:
        """Override lmfit defaults with user-supplied constraints.

        Called after ``model.make_params()`` to apply the ``min``, ``max``,
        ``vary``, and ``expr`` constraints from :attr:`parameters`.

        Only parameters that appear in ``params`` (i.e. parameters that the
        model actually declares) are overridden.  Unknown field names are
        silently ignored to allow partial specifications.

        Args:
            params: lmfit Parameters to update in-place.
        """
        for field_name, fit_param in self.parameters.items():
            lm_name = lmfit_param_name(self.id, field_name)
            if lm_name in params:
                fit_param.apply_to(params, lm_name)

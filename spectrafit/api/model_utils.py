"""Utility functions for type-safe API model creation.

This module provides helper functions to create API model objects from dictionaries,
ensuring type compatibility with mypy.
"""

from __future__ import annotations

from typing import Optional
from typing import cast

from spectrafit.api.moessbauer_model import AmplitudeAPI
from spectrafit.api.moessbauer_model import BackgroundAPI
from spectrafit.api.moessbauer_model import FwhmlAPI
from spectrafit.api.moessbauer_model import HyperfineFieldAPI
from spectrafit.api.moessbauer_model import IsomerShiftAPI
from spectrafit.api.moessbauer_model import QuadrupoleSplittingAPI


def create_amplitude_api(
    data: dict[str, float | bool | None],
) -> AmplitudeAPI:
    """Create an AmplitudeAPI instance from a dictionary.

    Args:
        data: Dictionary with amplitude parameters

    Returns:
        AmplitudeAPI: Properly instantiated model
    """
    vary = True
    expr = None

    if "vary" in data:
        vary_value = data.get("vary")
        vary = bool(vary_value) if vary_value is not None else True

    if "expr" in data:
        expr_value = data.get("expr")
        expr = cast("Optional[str]", expr_value)

    return AmplitudeAPI(
        max=data.get("max"),
        min=data.get("min"),
        vary=vary,
        value=data.get("value"),
        expr=expr,
    )


def create_isomershift_api(
    data: dict[str, float | bool | None],
) -> IsomerShiftAPI:
    """Create an IsomerShiftAPI instance from a dictionary.

    Args:
        data: Dictionary with isomer shift parameters

    Returns:
        IsomerShiftAPI: Properly instantiated model
    """
    vary = True
    expr = None

    if "vary" in data:
        vary_value = data.get("vary")
        vary = bool(vary_value) if vary_value is not None else True

    if "expr" in data:
        expr_value = data.get("expr")
        expr = cast("Optional[str]", expr_value)

    return IsomerShiftAPI(
        max=data.get("max"),
        min=data.get("min"),
        vary=vary,
        value=data.get("value"),
        expr=expr,
    )


def create_fwhml_api(
    data: dict[str, float | bool | None],
) -> FwhmlAPI:
    """Create a FwhmlAPI instance from a dictionary.

    Args:
        data: Dictionary with FWHM parameters

    Returns:
        FwhmlAPI: Properly instantiated model
    """
    vary = True
    expr = None

    if "vary" in data:
        vary_value = data.get("vary")
        vary = bool(vary_value) if vary_value is not None else True

    if "expr" in data:
        expr_value = data.get("expr")
        expr = cast("Optional[str]", expr_value)

    return FwhmlAPI(
        max=data.get("max"),
        min=data.get("min"),
        vary=vary,
        value=data.get("value"),
        expr=expr,
    )


def create_background_api(
    data: dict[str, float | bool | None],
) -> BackgroundAPI:
    """Create a BackgroundAPI instance from a dictionary.

    Args:
        data: Dictionary with background parameters

    Returns:
        BackgroundAPI: Properly instantiated model
    """
    vary = True
    expr = None

    if "vary" in data:
        vary_value = data.get("vary")
        vary = bool(vary_value) if vary_value is not None else True

    if "expr" in data:
        expr_value = data.get("expr")
        expr = cast("Optional[str]", expr_value)

    return BackgroundAPI(
        max=data.get("max"),
        min=data.get("min"),
        vary=vary,
        value=data.get("value"),
        expr=expr,
    )


def create_quadrupolesplitting_api(
    data: dict[str, float | bool | None],
) -> QuadrupoleSplittingAPI:
    """Create a QuadrupoleSplittingAPI instance from a dictionary.

    Args:
        data: Dictionary with quadrupole splitting parameters

    Returns:
        QuadrupoleSplittingAPI: Properly instantiated model
    """
    vary = True
    expr = None

    if "vary" in data:
        vary_value = data.get("vary")
        vary = bool(vary_value) if vary_value is not None else True

    if "expr" in data:
        expr_value = data.get("expr")
        expr = cast("Optional[str]", expr_value)

    return QuadrupoleSplittingAPI(
        max=data.get("max"),
        min=data.get("min"),
        vary=vary,
        value=data.get("value"),
        expr=expr,
    )


def create_hyperfinefield_api(
    data: dict[str, float | bool | None],
) -> HyperfineFieldAPI:
    """Create a HyperfineFieldAPI instance from a dictionary.

    Args:
        data: Dictionary with hyperfine field parameters

    Returns:
        HyperfineFieldAPI: Properly instantiated model
    """
    vary = True
    expr = None

    if "vary" in data:
        vary_value = data.get("vary")
        vary = bool(vary_value) if vary_value is not None else True

    if "expr" in data:
        expr_value = data.get("expr")
        expr = cast("Optional[str]", expr_value)

    return HyperfineFieldAPI(
        max=data.get("max"),
        min=data.get("min"),
        vary=vary,
        value=data.get("value"),
        expr=expr,
    )

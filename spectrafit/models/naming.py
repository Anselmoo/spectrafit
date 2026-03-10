"""Canonical naming utilities for lmfit parameter names.

These three functions are the **single source of truth** for the naming
convention used throughout the fitting pipeline.  No other module may
construct lmfit parameter names via inline string formatting — always call
`lmfit_param_name`.

**Naming contract**

``lmfit parameter name = {sanitized_id}_{field_name}``

Examples:
    ```
    lmfit_param_name("main", "amplitude")  →  "main_amplitude"
    lmfit_param_name("1",    "center")     →  "p1_center"
    lmfit_param_name("bg",   "slope")      →  "bg_slope"
    ```

User-facing expressions use dot notation (natural for scientists):

    ``"main.amplitude * 0.3"``

This is translated to lmfit underscore notation at config parse time:

    ``"main_amplitude * 0.3"``
"""

from __future__ import annotations

import re


def sanitize_component_id(raw_id: str) -> str:
    """Ensure a component id is a valid lmfit prefix.

    lmfit requires that a prefix (and therefore every parameter name derived
    from it) starts with a letter.  Numeric ids such as ``"1"`` or ``"39449"``
    are common in legacy SpectraFit input files and are automatically prefixed
    with ``"p"``.

    Args:
        raw_id: User-supplied component id (e.g. ``"1"``, ``"main"``, ``"bg"``).

    Returns:
        Sanitized id that is safe to use as an lmfit prefix
        (e.g. ``"p1"``, ``"main"``, ``"bg"``).

    Examples:
        >>> sanitize_component_id("1")
        'p1'
        >>> sanitize_component_id("main")
        'main'
        >>> sanitize_component_id("39449")
        'p39449'
        >>> sanitize_component_id("bg")
        'bg'
    """
    return re.sub(r"^(\d)", r"p\1", raw_id)


def lmfit_param_name(component_id: str, field_name: str) -> str:
    """Canonical lmfit parameter name: ``{sanitized_id}_{field_name}``.

    This is the **only** place this formula is written.  All other code
    calls this function instead of formatting the name inline.

    Args:
        component_id: Component's id (raw, pre-sanitization is accepted).
        field_name: The parameter field name
            (e.g. ``"amplitude"``, ``"center"``).

    Returns:
        The unique lmfit parameter name.

    Examples:
        >>> lmfit_param_name("main", "amplitude")
        'main_amplitude'
        >>> lmfit_param_name("1", "center")
        'p1_center'
        >>> lmfit_param_name("bg", "slope")
        'bg_slope'
    """
    return f"{sanitize_component_id(component_id)}_{field_name}"


def translate_dot_notation(expr: str) -> str:
    """Translate user dot-notation to lmfit underscore names.

    Scientists write ``"id.field"`` because that is natural.  lmfit requires
    ``"id_field"`` because dots are not valid in Python identifiers (which is
    what ``asteval`` processes during fitting).

    This translation happens **once** at config parse time via
    `FitParameter`'s field validator.
    The translated expression is stored and passed to lmfit; the user never
    sees the underscore form.

    Args:
        expr: User expression using dot notation
            (e.g. ``"main.amplitude * 0.3"``).

    Returns:
        Expression with dot notation replaced by underscore notation
        (e.g. ``"main_amplitude * 0.3"``).

    Examples:
        >>> translate_dot_notation("main.amplitude * 0.3")
        'main_amplitude * 0.3'
        >>> translate_dot_notation("left.center + right.center")
        'left_center + right_center'
        >>> translate_dot_notation("2 * bg.intercept")
        '2 * bg_intercept'
        >>> translate_dot_notation("plain_name")
        'plain_name'
    """
    return re.sub(r"\b([a-zA-Z_]\w*)\.([a-zA-Z_]\w*)\b", r"\1_\2", expr)

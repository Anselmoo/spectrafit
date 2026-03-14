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

from dataclasses import dataclass


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


def dataset_scoped_name(base_name: str, dataset_index: int | str) -> str:
    """Attach a one-based dataset suffix to a canonical base name.

    This helper centralizes the dataset-index suffix convention used by both
    global lmfit parameter names and global-fit dataframe columns.
    """
    return f"{base_name}_{dataset_index}"


def global_lmfit_param_name(
    component_id: str,
    field_name: str,
    dataset_index: int,
) -> str:
    """Canonical global-fit lmfit parameter name.

    Format:
        ``{sanitized_id}_{field_name}_{dataset_index}``
    """
    return dataset_scoped_name(
        lmfit_param_name(component_id, field_name), dataset_index
    )


def global_contribution_name(contribution_id: str, dataset_index: int) -> str:
    """Canonical global-fit contribution/dataframe column name."""
    return dataset_scoped_name(contribution_id, dataset_index)


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


def restore_dot_notation(
    expr: str,
    *,
    known_parameters: dict[str, tuple[str, ...]],
) -> str:
    """Translate known lmfit-style identifiers back to user-facing dot notation.

    Args:
        expr: Expression using lmfit underscore parameter names.
        known_parameters: Mapping from component id to known parameter names so
            only real component-field pairs are restored.

    Returns:
        Expression with known ``component_field`` tokens restored to
        ``component.field`` form.
    """
    restored = expr
    replacements = sorted(
        (
            (f"{component_id}_{parameter_name}", f"{component_id}.{parameter_name}")
            for component_id, parameter_names in known_parameters.items()
            for parameter_name in parameter_names
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for lmfit_name, dot_name in replacements:
        restored = re.sub(rf"\b{re.escape(lmfit_name)}\b", dot_name, restored)
    return restored


@dataclass(frozen=True, slots=True)
class GlobalLmfitContributionKey:
    """Typed parser for global lmfit contribution parameter names.

    Global fitting still produces parameter names in the legacy shape
    ``{contribution_id}_{field_name}_{dataset_index}``.  The contribution id
    may itself contain underscores, so parsing must happen from the right-most
    boundary rather than with a positional ``split("_")``.
    """

    contribution_id: str
    field_name: str
    dataset_index: int

    @classmethod
    def parse(cls, parameter_name: str) -> GlobalLmfitContributionKey:
        """Parse a global contribution parameter name.

        Args:
            parameter_name: lmfit parameter name in
                ``{contribution_id}_{field_name}_{dataset_index}`` format.

        Returns:
            Parsed contribution key.

        Raises:
            ValueError: If the name does not match the required shape.
        """
        normalized_name = parameter_name.lower()
        message = (
            "Global lmfit parameter names must match "
            "'{contribution_id}_{field_name}_{dataset_index}'."
        )
        try:
            contribution_id, field_name, dataset_token = normalized_name.rsplit(
                "_",
                maxsplit=2,
            )
        except ValueError as exc:
            raise ValueError(message) from exc

        if not contribution_id or not field_name:
            raise ValueError(message)

        try:
            dataset_index = int(dataset_token)
        except ValueError as exc:
            raise ValueError(message) from exc

        if dataset_index < 1:
            raise ValueError(message)

        return cls(
            contribution_id=contribution_id,
            field_name=field_name,
            dataset_index=dataset_index,
        )

    @property
    def registry_model(self) -> str:
        """Return the registry model key prefix for the contribution."""
        return self.contribution_id.split("_", maxsplit=1)[0]

    @property
    def contribution_name(self) -> str:
        """Return the per-dataset contribution label."""
        return global_contribution_name(self.contribution_id, self.dataset_index)

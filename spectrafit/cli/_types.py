"""Shared type definitions and enums for CLI commands."""

from __future__ import annotations

import sys

from enum import Enum


def reset_keyboard_protocol() -> None:
    r"""Reset enhanced keyboard protocols before interactive prompts.

    Modern terminals (VS Code, Ghostty, WezTerm, Kitty) may enable the kitty
    keyboard protocol, which encodes keypresses as escape sequences
    (e.g. ``\x1b[121;1u`` for ``y``, ``\x1b[99;5u`` for Ctrl+C).
    Standard ``click``/``typer`` prompts read raw characters and will never
    match these sequences, making interactive prompts appear unresponsive.

    Sending ``\x1b[>0u`` disables all kitty keyboard enhancements and
    restores normal character input. Non-kitty terminals silently ignore it.
    """
    if sys.stdout.isatty():
        sys.stdout.write("\x1b[>0u")
        sys.stdout.flush()


class OutputFormatEnum(str, Enum):
    """Enum for output file format choices."""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"

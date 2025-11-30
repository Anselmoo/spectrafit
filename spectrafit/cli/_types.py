"""Shared type definitions and enums for CLI commands."""

from __future__ import annotations

from enum import Enum


class SeparatorEnum(str, Enum):
    """Enum for separator choices."""

    TAB = "\t"
    COMMA = ","
    SEMICOLON = ";"
    COLON = ":"
    PIPE = "|"
    SPACE = " "
    REGEX = "s+"


class DecimalEnum(str, Enum):
    """Enum for decimal separator choices."""

    DOT = "."
    COMMA = ","


class GlobalFitEnum(int, Enum):
    """Enum for global fitting mode choices."""

    CLASSIC = 0
    AUTO = 1
    CUSTOM = 2


class VerboseEnum(int, Enum):
    """Enum for verbose level choices."""

    SILENT = 0
    TABLE = 1
    DICT = 2


class OutputFormatEnum(str, Enum):
    """Enum for output file format choices."""

    JSON = "json"
    YAML = "yaml"
    TOML = "toml"

"""Shared config file loading helpers for canonical fitting configuration."""

from __future__ import annotations

import json
import tomllib

from collections.abc import Mapping
from pathlib import Path

import yaml


def _rebase_infile_value(infile: object, *, config_dir: Path) -> object:
    """Rebase a relative infile string against the config directory."""
    if isinstance(infile, str) and not Path(infile).is_absolute():
        return str((config_dir / infile).resolve())
    return infile


def _rebase_loaded_payload(
    raw: Mapping[str, object], *, config_dir: Path
) -> Mapping[str, object]:
    """Rebase supported infile locations after decoding a config payload."""
    normalized = dict(raw)
    rebased = False

    root_infile = normalized.get("infile")
    rebased_root_infile = _rebase_infile_value(root_infile, config_dir=config_dir)
    if rebased_root_infile != root_infile:
        normalized["infile"] = rebased_root_infile
        rebased = True

    data_section = normalized.get("data")
    if isinstance(data_section, Mapping):
        infile_value = data_section.get("infile")
        rebased_data_infile = _rebase_infile_value(infile_value, config_dir=config_dir)
        if rebased_data_infile != infile_value:
            mutable_data = dict(data_section)
            mutable_data["infile"] = rebased_data_infile
            normalized["data"] = mutable_data
            rebased = True

    if rebased:
        return normalized
    return raw


def load_config_payload(path: Path | str) -> Mapping[str, object]:
    """Load a JSON, YAML, or TOML config file into a canonical raw mapping.

    Relative ``data.infile`` values are rebased against the config file's directory
    so CLI and notebook callers share identical path semantics.
    """
    config_path = Path(path)

    if config_path.suffix == ".toml":
        with config_path.open("rb") as config_file:
            raw: object = tomllib.load(config_file)
    elif config_path.suffix == ".json":
        with config_path.open(encoding="utf-8") as config_file:
            raw = json.load(config_file)
    elif config_path.suffix in {".yaml", ".yml"}:
        with config_path.open(encoding="utf-8") as config_file:
            raw = yaml.load(config_file, Loader=yaml.FullLoader)
    else:
        msg = (
            f"Unsupported file format '{config_path.suffix}'. "
            "Supported formats are: .json, .yaml, .yml, .toml"
        )
        raise OSError(msg)

    if not isinstance(raw, Mapping):
        msg = f"Configuration payload in '{config_path}' must be a mapping."
        raise TypeError(msg)

    return _rebase_loaded_payload(raw, config_dir=config_path.parent)


__all__ = ["load_config_payload"]

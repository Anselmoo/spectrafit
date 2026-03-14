---
title: Migration Guide — v1.x → v2.0.0
description: Step-by-step instructions for upgrading SpectraFit from v1.x to v2.0.0
tags:
  - migration
  - breaking-changes
  - v2.0.0
  - upgrade
---

# Migration Guide — v1.x → v2.0.0

!!! warning "Breaking Changes"

    **SpectraFit v2.0.0** removes several modules and features. This guide walks
    you through every change you need to make. For the full list of removals, see
    the [v2.0.0 Breaking Changes](../changelogs/v2.0.0-breaking-changes.md).

---

## Quick Checklist

Use this checklist to track your upgrade progress:

- [ ] Remove all Mössbauer imports and configuration
- [ ] Remove all RIXS imports and configuration
- [ ] Remove `AutoPeakDetection` usage (keep `ModelParameters` / `ReferenceKeys` if needed)
- [ ] Remove `autopeak` field from JSON, YAML, or TOML configuration files
- [ ] Remove Mössbauer model types from `peaks` configuration
- [ ] Remove `spectrafit.tools` imports
- [ ] Stop using `spectrafit-moessbauer` CLI command
- [ ] Stop using `--autopeak` CLI flag
- [ ] Replace static `Examples/` data with `SyntheticSpectrum` generator
- [ ] Remove any PPTX export code
- [ ] Update CI/CD pipelines that reference removed entry points or markers
- [ ] Refresh notebook examples to use `import spectrafit.notebook as sf` as the default authoring path

---

## Removed Features

### :magnet: Mössbauer Spectroscopy

All Mössbauer spectroscopy support has been **removed entirely** (~3,000 lines
across 27 files). There is no replacement or compatibility shim.

!!! info "Affected Users"

    If your workflow depends on Mössbauer models (`moesbauer_singlet`,
    `moesbauer_doublet`, `moesbauer_sextet`, `moesbauer_octet`), you must
    remove these from your configuration and code before upgrading.

### :ocean: RIXS Plugin

The Resonant Inelastic X-ray Scattering converter plugin has been **fully
removed**. There is no replacement.

### :mountain: AutoPeak Detection

The automatic peak detection feature has been gutted. The `AutoPeakDetection`
class and related methods are removed.

!!! note "Module Retained as Placeholder"

    The `spectrafit.models.autopeak` module file still exists but only contains
    `ReferenceKeys` and `ModelParameters`. It serves as a placeholder for a
    future redesign.

| Symbol | Status |
|---|---|
| `AutoPeakDetection` class | :x: Removed |
| `define_parameters_auto` method | :x: Removed |
| `detection_check` method | :x: Removed |
| `autopeak` configuration field | :x: Removed |
| `ModelParameters` class | :x: Removed; use `spectrafit.models.parameter_builder.ParameterBuilder` |
| `ReferenceKeys` class | :white_check_mark: Available from `spectrafit.models.parameter_builder` |

!!! warning "Legacy model builder shim removed"

    `spectrafit.models.model_parameters` has been removed in v2.x.
    Import the canonical implementation from
    `spectrafit.models.parameter_builder` instead.

### :file_folder: Static Examples

The `Examples/` directory (43 files, ~1 MB) has been deleted. Use the new
`SyntheticSpectrum` generator instead (see [New Features](#new-features-in-v200)
below).

### :wrench: PPTX Export

PowerPoint export functionality has been removed.

---

## Import Path Changes

The following table lists every import affected by v2.0.0:

| v1.x Import | v2.0.0 Status | Action Required |
|---|---|---|
| `from spectrafit.models.moessbauer import ...` | :x: Removed | Delete import |
| `from spectrafit.api.moessbauer_model import ...` | :x: Removed | Delete import |
| `from spectrafit.api.model_utils import ...` | :x: Removed | Delete import |
| `from spectrafit.api.physical_constants import ...` | :x: Removed | Delete import |
| `from spectrafit.plugins.moessbauer_plugin import ...` | :x: Removed | Delete import |
| `from spectrafit.plugins.rixs_converter import ...` | :x: Removed | Delete import |
| `from spectrafit.models.autopeak import AutoPeakDetection` | :x: Removed | Delete import |
| `from spectrafit.tools import ...` | :x: Removed | Delete import |
| `from spectrafit.models.autopeak import ModelParameters` | :white_check_mark: Available | No change needed |
| `from spectrafit.models.autopeak import ReferenceKeys` | :white_check_mark: Available | No change needed |
| `from spectrafit.jupyter import SpectraFitNotebook` | :white_check_mark: Available | Keep for advanced runtime integrations; prefer `import spectrafit.notebook as sf` for new notebooks |
| `import spectrafit.notebook as sf` | :sparkles: New | Preferred notebook authoring surface in v2.x |
| `from spectrafit.models.registry import REGISTRY` | :sparkles: New | See [Model Registry](#model-registry) |
| `from spectrafit.generators.synthetic import SyntheticSpectrum` | :sparkles: New | See [Synthetic Data](#synthetic-data-generator) |

---

## Notebook Authoring in v2.x

For new or refreshed notebooks, prefer the compact notebook facade:

```python
import spectrafit.notebook as sf

df = sf.read("data.csv", x="energy", y="intensity")
result = sf.fit(
    df,
    peaks=[sf.peak("gaussian", id="main", amplitude=(1.0, 0.0, 2.0))],
    name="analysis",
)
artifacts = result.save("outputs/live/notebook")
```

This keeps routine notebook work to one import, shorthand builders, and a
bundled export call. Use `sf.tie("main.center + 0.5")` for tied parameters in
scientist-friendly dot notation.

Keep `spectrafit.jupyter.*` when you need advanced escape hatches such as
config-to-notebook materialization or lower-level runtime integrations.

---

## Configuration Changes

### `autopeak` Field Removed

!!! danger "Configuration Incompatibility"

    The `autopeak` field is **no longer accepted** in fitting configuration
    files. If present, SpectraFit will raise an error.

=== "v1.x (remove this)"

    ```json
    {
      "autopeak": {
        "modeltype": "voigt",
        "height": 0.01,
        "threshold": 0.01,
        "distance": 10,
        "prominence": 0.01,
        "width": 0,
        "wlen": 100
      }
    }
    ```

=== "v2.0.0"

    ```json
    {
      "peaks": {
        "1": {
          "pseudovoigt": {
            "amplitude": { "max": 2, "min": 0, "vary": true, "value": 1 },
            "center": { "max": 2, "min": -2, "vary": true, "value": 0 },
            "fwhmg": { "max": 0.1, "min": 0.02, "vary": true, "value": 0.01 },
            "fwhml": { "max": 0.1, "min": 0.01, "vary": true, "value": 0.01 }
          }
        }
      }
    }
    ```

### Mössbauer Models Removed from `peaks`

Mössbauer model types are no longer valid in the `peaks` configuration block:

- `moesbauer_singlet`
- `moesbauer_doublet`
- `moesbauer_sextet`
- `moesbauer_octet`

!!! warning "Action Required"

    Remove any Mössbauer model entries from your `peaks` configuration. There
    is no v2.0.0 replacement for these models.

---

## CLI Changes

### `spectrafit-moessbauer` Command Removed

The dedicated Mössbauer CLI entry point no longer exists.

=== "v1.x"

    ```bash
    spectrafit-moessbauer data.txt input.json
    ```

=== "v2.0.0"

    ```text
    # No replacement — Mössbauer support has been removed.
    ```

### `--autopeak` Flag Removed

The `--autopeak` flag is no longer accepted by the `spectrafit` CLI.

=== "v1.x"

    ```bash
    spectrafit data.txt input.json --autopeak
    ```

=== "v2.0.0"

    ```text
    # Define peaks explicitly in your configuration file instead.
    spectrafit data.txt input.json
    ```

### `pytest` Marker Removed

The `moessbauer` pytest marker has been removed. If your test suite uses
`@pytest.mark.moessbauer`, remove or replace those markers.

---

## New Features in v2.0.0

### Model Registry

A centralized registry replaces string-based model dispatch with structured
lookups.

!!! example "Using the Model Registry"

    ```python
    from spectrafit.models.registry import REGISTRY

    # List all available models
    for model in REGISTRY.list_models():
        print(f"{model.name}: {model.parameters}")

    # Look up a specific model
    info = REGISTRY.get("gaussian")
    print(info.function, info.parameters)

    # Check if a model exists
    assert "gaussian" in REGISTRY
    ```

### Synthetic Data Generator

The `SyntheticSpectrum` class provides reproducible test data generation,
replacing the static `Examples/` directory.

!!! example "Generating Synthetic Spectra"

    ```python
    from spectrafit.generators.synthetic import PeakDefinition
    from spectrafit.generators.synthetic import SyntheticSpectrum

    # Define a spectrum with known ground-truth parameters
    spectrum = SyntheticSpectrum(
        x_min=-5.0,
        x_max=5.0,
        num_points=500,
        noise_level=0.02,
        seed=42,
        peaks=[
            PeakDefinition(
                model="gaussian",
                params={"amplitude": 1.0, "center": 0.0, "fwhmg": 1.0},
            ),
            PeakDefinition(
                model="lorentzian",
                params={"amplitude": 0.5, "center": 2.0, "fwhml": 0.8},
            ),
        ],
    )

    # Generate data as a pandas DataFrame
    df = spectrum.to_dataframe()
    ```

!!! tip "Replacing Static Example Files"

    If your tests or scripts loaded data from the old `Examples/` directory,
    switch to `SyntheticSpectrum` for reproducible, parameterized test data
    with exact ground-truth values.

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'spectrafit.models.moessbauer'`

**Cause:** Code still imports Mössbauer modules that were removed in v2.0.0.

**Fix:** Delete the import and any code that depends on it.

```python
# Remove this:
from spectrafit.models.moessbauer import MoesbauerSinglet  # noqa: ERA001
```

### `ModuleNotFoundError: No module named 'spectrafit.tools'`

**Cause:** The `spectrafit.tools` module was removed.

**Fix:** Remove the import. Functionality was migrated to core modules in v1.x.

### `KeyError: 'autopeak'` or `ValidationError` on configuration load

**Cause:** Your configuration file still contains the `autopeak` field.

**Fix:** Remove the `autopeak` block from your JSON, YAML, or TOML input file.
Define peaks explicitly in the `peaks` configuration instead.

### `command not found: spectrafit-moessbauer`

**Cause:** The `spectrafit-moessbauer` entry point was removed.

**Fix:** Mössbauer support is no longer available. Remove the command from your
scripts and CI/CD pipelines.

### `ImportError: cannot import name 'AutoPeakDetection'`

**Cause:** `AutoPeakDetection` was removed from `spectrafit.models.autopeak`.

**Fix:** Remove the import. Define peaks explicitly in your configuration file.
`ModelParameters` and `ReferenceKeys` remain available if needed.

---

## Related References

- [v2.0.0 Breaking Changes](../changelogs/v2.0.0-breaking-changes.md) — Full
  list of removals and changes
- [Usage Guide](usage.md) — How to configure and run SpectraFit
- [Features](features.md) — Available fitting features and statistics

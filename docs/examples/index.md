---
title: SpectraFit Examples
description: Practical examples demonstrating the usage and capabilities of SpectraFit for spectral analysis
tags:
  - examples
  - tutorials
  - command-line
  - jupyter
  - practical-applications
---

# SpectraFit Examples

This section provides practical examples to help you understand and use **SpectraFit** effectively for your spectroscopic data analysis.

## Overview

The examples demonstrate various use cases and features of **SpectraFit**, from
basic peak fitting to advanced applications. The recommended place to begin in
v2 is the collection of **repository-shipped examples** under `examples/`,
because they give you runnable local data, readable TOMLs, committed notebooks,
and persistent live artifacts that you can inspect after every run.

!!! tip "Learning Path"
Start with the basic examples and progress to more advanced topics. The examples build upon concepts introduced in earlier sections.

## Repository-shipped examples

These are the most teachable starting points for a new SpectraFit user working
from a cloned checkout.

<div class="grid cards" markdown>

- :material-flask-outline: **Basic single-peak workflow**

  Purpose: learn the smallest useful v2 fit.

  - Path: `examples/basic/`
  - CLI: `uv run spectrafit fit examples/basic/input.toml --noplot`
  - Notebook: `jupyter lab examples/basic/notebook.ipynb`
  - Live outputs:
    - `examples/basic/outputs/live/cli/`
    - `examples/basic/outputs/live/notebook/`
  - Companion README: `examples/basic/README.md`

- :material-graph-outline: **Two constrained peaks**

  Purpose: learn cross-component constraints with overlapping features.

  - Path: `examples/two-peak-constrained/`
  - CLI: `uv run spectrafit fit examples/two-peak-constrained/input.toml --noplot`
  - Notebook: `jupyter lab examples/two-peak-constrained/notebook.ipynb`
  - Live outputs:
    - `examples/two-peak-constrained/outputs/live/cli/`
    - `examples/two-peak-constrained/outputs/live/notebook/`
  - Companion README: `examples/two-peak-constrained/README.md`

- :material-chart-timeline-variant: **Curved background**

  Purpose: learn how to fit a peak when the baseline is curved rather than flat.

  - Path: `examples/curved-background/`
  - CLI: `uv run spectrafit fit examples/curved-background/input.toml --noplot`
  - Notebook: `jupyter lab examples/curved-background/notebook.ipynb`
  - Live outputs:
    - `examples/curved-background/outputs/live/cli/`
    - `examples/curved-background/outputs/live/notebook/`
  - Companion README: `examples/curved-background/README.md`

- :material-chart-waterfall: **Peak plus edge**

  Purpose: learn how to combine a resonance peak with a smooth edge-like background.

  - Path: `examples/peak-plus-edge/`
  - CLI: `uv run spectrafit fit examples/peak-plus-edge/input.toml --noplot`
  - Notebook: `jupyter lab examples/peak-plus-edge/notebook.ipynb`
  - Live outputs:
    - `examples/peak-plus-edge/outputs/live/cli/`
    - `examples/peak-plus-edge/outputs/live/notebook/`
  - Companion README: `examples/peak-plus-edge/README.md`

</div>

### Recommended repo workflow

```bash
uv sync --extra jupyter
uv run poe generate-examples
uv run spectrafit fit examples/basic/input.toml --noplot
jupyter lab examples/basic/notebook.ipynb
```

### Generated validation overlays

Run `uv run poe generate-plots` when you want local or CI Plotly overlays under
`examples/*/fit_validation.html`. These HTML files are generated on demand and
are not treated as committed source-of-truth product artifacts.

### Output layout

| Surface | Output directory | Typical files |
|---------|------------------|---------------|
| CLI live workflow | `examples/<name>/outputs/live/cli/` | `input.resolved.json`, `<name>_fit.csv`, `<name>_components.csv`, `<name>_correlation.csv`, `<name>_summary.json` |
| Notebook live workflow | `examples/<name>/outputs/live/notebook/` | `fit_<name>.csv`, `metric_<name>.csv`, `peaks_<name>.csv`, `fit_<name>.html`, `report_<name>.toml`, `<name>.lock` |

!!! note "Notebook UX"
    For the committed examples, open the local notebook file directly with
    JupyterLab. Each notebook already uses `import spectrafit.notebook as sf`,
    compact `sf.peak(...)` / `sf.background(...)` builders, and one
    `result.save(...)` call for bundled notebook exports. When you need more
    control, treat `spectrafit.jupyter` as an advanced escape hatch rather than
    the default learning path.

## Command-Line Examples

<div class="grid cards" markdown>

- :material-console: **[Fitting of a Single Feature](example1.md)** - Learn how to fit a single peak using the command-line interface.
- :material-file-document-multiple: **[JSON, TOML, YAML Inputs](example2.md)** - Use different input file formats for your fitting parameters.
- :material-chart-bell-curve: **[Multi Peak Fitting](example3.md)** - Handle complex spectra with multiple overlapping peaks.
- :material-flask: **[Working with Real Life Data](example4.md)** - Apply **SpectraFit** to experimental spectroscopic data.
- :material-function: **[Working with Expressions](example5.md)** - Create custom expressions for specialized fitting needs.
- :material-earth: **[Global Fitting](example6.md)** - Fit multiple datasets simultaneously with shared parameters.
- :material-robot: **[Automatic Fitting](example7.md)** - Use automated approaches for initial parameter estimation.
- :material-file-import: **[Working with Athena Data](example8.md)** - Import and process data from Athena XAS software.

</div>

## Jupyter Notebook Examples

Jupyter notebooks provide an interactive environment for **SpectraFit**, allowing real-time visualization and parameter adjustments.

<div class="grid cards" markdown>

- :material-chart-line: **[Default Plot](example9_1.ipynb)** - Basic visualization of fitting results in a notebook.
- :material-palette: **[Themes](example9_2.ipynb)** - Customize the appearance of your plots.
- :material-file-export: **[Export Results](example9_3.ipynb)** - Save and export your fitting results in various formats.
- :material-map: **[RIXS Map Visualization](example9_4.ipynb)** - Generate 2D maps from RIXS spectroscopy data.
- :material-earth: **[RIXS Global-Fitting in Jupyter](example9_6.ipynb)** - Apply global fitting approaches to RIXS datasets.

- :material-atom: **[Mössbauer Spectroscopy](example10_1.ipynb)**

  Fit and analyze Mössbauer spectra with specialized models.

</div>

## Application Areas

These examples cover applications in various spectroscopic techniques:

- X-ray Absorption Spectroscopy (XAS)
- X-ray Emission Spectroscopy (XES)
- Resonant Inelastic X-ray Scattering (RIXS)
- Optical Spectroscopy
- Vibrational Spectroscopy
- Mössbauer Spectroscopy

## Next Steps

After exploring these examples, you may want to:

- Refer to the [Documentation](../doc/index.md) for deeper understanding
- Check the [API Reference](../api/spectrafit_api.md) for programmatic usage
- Create your own fitting procedures based on these examples

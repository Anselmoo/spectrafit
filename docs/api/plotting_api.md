# Plotting API

SpectraFit exposes two plotting layers:

- **`spectrafit.plotting`** — CLI pipeline plots (seaborn/matplotlib, driven by `PlotConfig`)
- **`spectrafit.jupyter.plotting`** — Jupyter notebook plots (Plotly, driven by `PlotAPI`)

---

## CLI Plotting — `spectrafit.plotting`

::: spectrafit.plotting

---

## Jupyter Plotting — `spectrafit.jupyter.plotting`

The `DataFramePlot` class provides Plotly-based interactive plots for use inside
Jupyter notebooks. It is a mixin base class for
`spectrafit.jupyter.core.SpectraFitNotebook`.

!!! note "Column constants"
    `DataFramePlot` caches a single `ColumnNamesAPI` instance as a class variable
    (`_COLUMNS`) rather than constructing one on every method call.

::: spectrafit.jupyter.plotting

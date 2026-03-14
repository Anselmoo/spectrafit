# Notebook API

!!! note "Primary notebook surface"

    Start new notebook work with `import spectrafit.notebook as sf`. The compact
    facade keeps the beginner path to one import, shorthand builders, and one
    `result.save(...)` call while still compiling into SpectraFit's canonical
    fitting pipeline.

## Primary entry points

- `spectrafit.notebook.read` loads a CSV or dataframe and remembers notebook
  metadata such as the source path and x/y columns.
- `spectrafit.notebook.peak` and `spectrafit.notebook.background` build
  canonical components from notebook-friendly shorthand.
- `spectrafit.notebook.fixed` and `spectrafit.notebook.tie` express fixed and
  tied parameters. `sf.tie(...)` accepts user-facing dot notation such as
  `"main.center + 0.5"`.
- `spectrafit.notebook.fit` runs the canonical pipeline and returns a
  `FitSession`.
- `FitSession.save(...)` writes the bundled notebook export set in one call.

## Beginner notebook workflow

```python
from pathlib import Path

import spectrafit.notebook as sf

df = sf.read("data.csv", x="energy", y="intensity")

result = sf.fit(
    df,
    peaks=[
        sf.peak(
            "gaussian",
            id="main",
            amplitude=(1.0, 0.0, 2.0),
            center=(0.0, -1.0, 1.0),
            fwhmg=(0.4, 0.05, 1.5),
        ),
    ],
    background=[
        sf.background(
            "linear",
            id="bg",
            slope=sf.fixed(0.0),
            intercept=(0.02, 0.0, 0.5),
        ),
    ],
    optimizer=sf.OptimizerConfig(method="leastsq", max_nfev=500),
    name="analysis",
)

result.summary
result.metrics
artifacts = result.save(Path("outputs/live/notebook"))
```

This keeps the common notebook workflow to:

1. `sf.read(...)`
2. edit compact `sf.peak(...)` / `sf.background(...)` cells
3. call `sf.fit(...)`
4. export everything with `result.save(...)`

## Bundled notebook exports

`result.save(...)` writes:

- `fit_<name>.csv`
- `metric_<name>.csv`
- `peaks_<name>.csv`
- `fit_<name>.html`
- `report_<name>.toml`
- `<name>.lock`

## Progressive escape hatches

When you need more control, the notebook facade intentionally exposes the same
validated building blocks used elsewhere in SpectraFit:

- `sf.Component`, `sf.FitParameter`, `sf.DataConfig`, `sf.FittingContext`, and
  solver config models are re-exported for advanced notebook authoring.
- `FitSession.to_config()` and `FitSession.to_toml(...)` let you inspect or
  persist the validated config behind a notebook run.
- `spectrafit.jupyter.materialize_notebook_from_config` and
  `spectrafit convert --format ipynb` remain the advanced path for generating
  editable notebooks from validated config files.
- `spectrafit.jupyter.SpectraFitNotebook` remains available for lower-level
  runtime integrations, but it is no longer the primary notebook starting point
  in the docs.

## API reference

::: spectrafit.notebook

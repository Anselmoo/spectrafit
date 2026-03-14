# Jupyter interface

!!! note "Core surface, not a plugin contract"

    This page remains in the historical `plugins/` docs section, but notebook
    support is a first-class SpectraFit surface rather than a bundled plugin
    protocol.

## Current ownership

- The primary notebook authoring surface is `spectrafit.notebook`.
- Notebook materialization still lives in
  `spectrafit.jupyter.materialize_notebook_from_config`.
- Lower-level runtime integrations still live in
  `spectrafit.jupyter.SpectraFitNotebook`.
- `spectrafit convert --format ipynb` materializes an editable notebook directly
  from a validated SpectraFit config file.
- Reusable example and live-workflow validation logic lives in
  `spectrafit.workflow.validation`; `scripts/run_live_examples.py` is only a
  thin wrapper around that module.

## Recommended notebook workflows

### 1. Start with the one-import notebook facade

For notebook-first analysis, this is the primary documented path:

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
        )
    ],
    background=[
        sf.background(
            "linear",
            id="bg",
            slope=sf.fixed(0.0),
            intercept=(0.02, 0.0, 0.5),
        )
    ],
    optimizer=sf.OptimizerConfig(method="leastsq", max_nfev=500),
    name="analysis",
)

artifacts = result.save(Path("outputs/live/notebook"))
```

This keeps the notebook story to one import, compact component builders, and one
bundled export call. Use `sf.tie("main.center + 0.5")` when you need tied
parameters; dot notation is translated to lmfit-safe names automatically.

### 2. Materialize a notebook from a config file

Use the CLI or Python API when you want a checked-in or shareable `.ipynb`
artifact generated from a validated config:

```bash
spectrafit convert input.toml --format ipynb --output analysis.ipynb
```

Equivalent Python API:

```python
from pathlib import Path

from spectrafit.jupyter import materialize_notebook_from_config

materialize_notebook_from_config(
    config_path=Path("input.toml"),
    output_path=Path("analysis.ipynb"),
)
```

The generated notebook still presents the beginner-friendly `spectrafit.notebook`
workflow inside the notebook body.

### 3. Drop to advanced notebook runtime APIs when needed

Use the lower-level `spectrafit.jupyter` runtime directly when you need advanced
control over materialization or runtime orchestration:

```python
import pandas as pd

from spectrafit.jupyter import SpectraFitNotebook

notebook = SpectraFitNotebook.from_config(df=df, config=config, fname="analysis")
notebook.solver_model(
    notebook.initial_model,
    config=config,
    show_plot=False,
    show_metric=False,
)
notebook.generate_fit_report()
```

Treat this as an escape hatch for advanced integrations rather than the primary
notebook starting point.

## CLI surface

- `spectrafit jupyter` launches the Jupyter-oriented entry surface.
- `spectrafit convert --format ipynb` creates a materialized notebook from a
  config file.
- `spectrafit init --jupyter` scaffolds a starter notebook that already uses the
  one-import `spectrafit.notebook` flow.

These are core CLI features. They do not depend on external plugin discovery.

## Related references

- [CLI reference](../interface/cli-reference.md)
- [Notebook API](../api/notebook_api.md)
- [v2 migration guide](../interface/migration-v2.md)

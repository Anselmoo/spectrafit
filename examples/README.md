# SpectraFit v2 Examples

Ready-to-run fitting examples for scientists who want to learn the v2 workflow
without first building their own configuration from scratch.

Each example directory is intentionally self-contained:

- `data.csv` — committed synthetic spectrum for local, reproducible runs
- `input.toml` — human-readable v2 config shared by CLI and notebook workflows
- `notebook.ipynb` — runnable notebook rooted in the example directory
- `fit_validation.html` — optional Plotly validation overlay generated on demand
  via `uv run poe generate-plots`
- `outputs/live/` — persistent artifacts produced by the example live workflows

The committed TOMLs intentionally use inline `[components.parameters]` tables so
the parameter values, bounds, and constraints stay easy to scan in one place.

## Examples

| Directory | Models used | What you learn |
|-----------|-------------|----------------|
| `basic/` | Gaussian + Linear | The smallest useful v2 fit, readable TOML layout, and the expected CLI/notebook outputs |
| `two-peak-constrained/` | Gaussian + Pseudo-Voigt + Linear | Cross-component constraints with dot notation and a more realistic overlapping-peak workflow |
| `curved-background/` | Gaussian + Polynom2 | How to fit a real peak when the baseline is curved rather than flat |
| `peak-plus-edge/` | Pseudo-Voigt + Erf + Constant | How to combine a resonance peak with a smooth edge-like background |

Every example directory also contains:

- `data.csv` — local synthetic input data
- `input.toml` — canonical v2 config shared by CLI and notebook flows
- `notebook.ipynb` — runnable notebook rooted in the example directory and
  authored around the one-import `spectrafit.notebook` flow (`sf.read`,
  `sf.peak`, `sf.background`, `sf.fit`, `result.save`)
- `outputs/live/cli/` — CLI-side live outputs such as resolved config, fit CSV,
  fit HTML, component table, correlation table, and summary JSON
- `outputs/live/notebook/` — notebook-side live outputs such as fit/metric/peak
  CSVs, fit HTML, report TOML, and the notebook lockfile

## Quickstart

### Environment

From the repository root, install a local environment with notebook support:

```bash
uv sync --extra jupyter
```

### Regenerate synthetic data

```bash
uv run poe generate-examples              # default seed=42
uv run poe generate-examples -- --seed 7  # reproducible alternative
```

### Run a fit

```bash
uv run spectrafit fit examples/basic/input.toml --noplot
uv run spectrafit fit examples/two-peak-constrained/input.toml --noplot
uv run spectrafit fit examples/curved-background/input.toml --noplot
uv run spectrafit fit examples/peak-plus-edge/input.toml --noplot
```

After a successful live CLI run, inspect:

- `examples/basic/outputs/live/cli/basic_fit.csv`
- `examples/basic/outputs/live/cli/basic_fit.html`
- `examples/basic/outputs/live/cli/basic_summary.json`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_fit.csv`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_fit.html`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_summary.json`

### Open the example notebooks

```bash
jupyter lab examples/basic/notebook.ipynb
jupyter lab examples/two-peak-constrained/notebook.ipynb
jupyter lab examples/curved-background/notebook.ipynb
jupyter lab examples/peak-plus-edge/notebook.ipynb
```

Each committed notebook is the primary beginner path for notebook work: it
imports `spectrafit.notebook as sf`, loads the local `data.csv` with
`sf.read(...)`, defines compact `sf.peak(...)` / `sf.background(...)` builders,
runs `sf.fit(...)`, and exports the bundled artifact set with one
`result.save(...)` call into that example's `outputs/live/notebook/`
directory.

If you need more control later, use the progressive escape hatches behind the
facade: `sf.Component` / `sf.FitParameter`, `result.to_toml(...)`, or the lower
level `spectrafit.jupyter` materialization/runtime APIs.

### Use the built-in example CLI

```bash
uv run spectrafit examples list
uv run spectrafit examples run basic --surface cli
uv run spectrafit examples run basic --surface notebook
uv run spectrafit examples run --surface both
```

This is the canonical user-facing surface for running shipped examples. The
`poe live` task remains useful for repo automation, but it now delegates to the
same product-owned workflow logic.

After a successful notebook run, inspect:

- `examples/basic/outputs/live/notebook/fit_basic.csv`
- `examples/basic/outputs/live/notebook/fit_basic.html`
- `examples/basic/outputs/live/notebook/metric_basic.csv`
- `examples/basic/outputs/live/notebook/peaks_basic.csv`
- `examples/basic/outputs/live/notebook/report_basic.toml`
- `examples/basic/outputs/live/notebook/basic.lock`

### What the two surfaces write

| Surface | Output directory | Typical files |
|---------|------------------|---------------|
| CLI live workflow | `examples/<name>/outputs/live/cli/` | `input.resolved.json`, `<name>_fit.csv`, `<name>_fit.html`, `<name>_components.csv`, `<name>_correlation.csv`, `<name>_summary.json` |
| Notebook live workflow | `examples/<name>/outputs/live/notebook/` | `fit_<name>.csv`, `fit_<name>.html`, `metric_<name>.csv`, `peaks_<name>.csv`, `report_<name>.toml`, `<name>.lock` |

The CLI and notebook outputs are intentionally different: the CLI keeps the
resolved configuration and richer report-style exports, while the notebook flow
keeps the editable, dataframe-oriented CSV exports and lockfile that are useful
inside iterative notebook work.

!!! note "Prefer direct notebook paths for the shipped examples"
    Open `examples/<name>/notebook.ipynb` directly in JupyterLab. This is the
    clearest path for the committed examples and drops you straight into the
    one-import `spectrafit.notebook` workflow with bundled `result.save(...)`
    exports.

### Validate all examples (integration test)

```bash
uv run poe validate-examples
```

### Generate validation overlays on demand

```bash
uv run poe generate-plots
```

This writes `examples/*/fit_validation.html` as a generated local/CI artifact.
Those HTML overlays are intentionally gitignored so the committed example
surface stays focused on `data.csv`, `input.toml`, `notebook.ipynb`, and
documented live outputs.

### Run the full live CLI + notebook workflow

```bash
uv run poe live
uv run spectrafit examples run --surface both
```

This regenerates the committed synthetic example data and notebooks, runs every
`examples/*/input.toml` through the CLI, and then executes the same examples
through the compact `spectrafit.notebook` export flow to verify notebook-mode artifacts.

Use this when you want to refresh the committed example artifacts and confirm
that both user-facing surfaces still behave as documented.

## v2 Schema at a Glance

```toml
schema_version = "2.0"
config_type    = "peak_fit"

[meta]
description = "Human-readable description"

[data]
infile = "data.csv"
x_col  = "energy"
y_col  = "intensity"

[solver]
method     = "leastsq"
max_nfev   = 1000
nan_policy = "propagate"
calc_covar = true

[[components]]
id    = "peak1"
model = "gaussian"          # lower-case registry name

[components.parameters]
amplitude = { value = 1.0,  bounds = [0.0, 3.0],  vary = true }
center    = { value = 0.0,  bounds = [-1.0, 1.0], vary = true }
fwhmg     = { value = 0.4,  bounds = [0.05, 1.5], vary = true }
```

### Key differences from v1

| v1                              | v2                                          |
|---------------------------------|---------------------------------------------|
| `schema_version = "1.0"`        | `schema_version = "2.0"`                    |
| `min` / `max` keys              | `bounds = [min, max]` inline table          |
| No `[data]` section             | `[data]` with `infile`, `x_col`, `y_col`   |
| No `[solver]` section           | `[solver]` with `method`, `max_nfev`, …    |
| Separate minimizer/optimizer    | Unified `[solver]` block                    |

### Cross-component constraints

Use `expr` with `vary = false` to link parameter values across components:

```toml
# p2.center tracks p1.center with a fixed +1.0 offset
center = { value = 0.5, vary = false, expr = "p1.center + 1.0" }

# p2's Lorentzian width mirrors its own Gaussian width
fwhml  = { value = 0.25, vary = false, expr = "p2.fwhmg" }
```

Dot-notation (`component_id.parameter_name`) is translated to lmfit's
underscore form (`component_id_parameter_name`) automatically at parse time.

## Migrating from v1

Run the bundled migration tool:

```bash
uv run poe migrate-v1 old_input.toml -o new_input.toml
```

Or see the [migration guide](../docs/migration_v1_to_v2.md) for a detailed
walkthrough of every schema change.

## Available Models

All lower-case model names accepted in `model = "..."`:

| Name           | Category     | Parameters                                      |
|----------------|--------------|-------------------------------------------------|
| `gaussian`     | peak         | amplitude, center, fwhmg                        |
| `lorentzian`   | peak         | amplitude, center, fwhml                        |
| `pseudovoigt`  | peak         | amplitude, center, fwhmg, fwhml                 |
| `voigt`        | peak         | center, fwhmv, gamma                            |
| `linear`       | background   | slope, intercept                                |
| `constant`     | background   | amplitude                                       |
| `exponential`  | background   | amplitude, decay, intercept                     |
| `power`        | background   | amplitude, exponent, intercept                  |
| `pearson1`–`4` | pearson      | amplitude, center, sigma, exponent[, skewness…] |
| `erf`          | step         | amplitude, center, sigma                        |
| `heaviside`    | step         | amplitude, center, sigma                        |
| `atan`         | step         | amplitude, center, sigma                        |
| `log`          | step         | amplitude, center, sigma                        |
| `cgaussian`    | cumulative   | amplitude, center, fwhmg                        |
| `clorentzian`  | cumulative   | amplitude, center, fwhml                        |
| `cvoigt`       | cumulative   | amplitude, center, fwhmv, gamma                 |
| `polynom2`     | polynomial   | coefficient0, coefficient1, coefficient2        |
| `polynom3`     | polynomial   | coefficient0–3                                  |

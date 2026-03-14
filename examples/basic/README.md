# Basic Example — Single Gaussian Peak

Fit a single Gaussian peak sitting on a flat linear background.

This is the smallest useful SpectraFit v2 workflow and the recommended first
example for a scientist who wants to learn:

- how the v2 `input.toml` is organized
- how the CLI run differs from the notebook run
- where persistent example artifacts appear after each workflow

If you only read one example before adapting SpectraFit to your own data, start
here.

## What this example teaches

1. A readable one-peak TOML using the committed local `data.csv`
2. The canonical `spectrafit fit ...` command for a v2 config
3. The local notebook workflow driven by `import spectrafit.notebook as sf`
4. The output layout under `outputs/live/cli/` and `outputs/live/notebook/`

## Ground Truth Parameters

| Component | Parameter   | Value | Varies |
|-----------|-------------|-------|--------|
| `peak1`   | amplitude   | 1.0   | yes    |
| `peak1`   | center      | 0.0   | yes    |
| `peak1`   | fwhmg       | 0.4   | yes    |
| `bg`      | slope       | 0.0   | no     |
| `bg`      | intercept   | 0.02  | yes    |

Gaussian noise with `scale=0.02` and `seed=42` was added to the clean signal.

## How to Run

**Prerequisite — install notebook support in the repo environment if needed:**

```bash
uv sync --extra jupyter
```

**Step 1 — (re-)generate the synthetic data:**

```bash
uv run poe generate-examples
```

**Step 2 — run the fit:**

```bash
uv run spectrafit fit examples/basic/input.toml --noplot
```

Expected persistent CLI artifacts appear under:

- `examples/basic/outputs/live/cli/basic_fit.csv`
- `examples/basic/outputs/live/cli/basic_fit.html`
- `examples/basic/outputs/live/cli/basic_components.csv`
- `examples/basic/outputs/live/cli/basic_correlation.csv`
- `examples/basic/outputs/live/cli/basic_summary.json`
- `examples/basic/outputs/live/cli/input.resolved.json`

Use these files when you want a report-style record of the fit with the exact
resolved config that was executed.

**Step 3 — open the local notebook:**

```bash
jupyter lab examples/basic/notebook.ipynb
```

The committed notebook is the primary beginner path for this example: it
imports `spectrafit.notebook as sf`, loads the local `data.csv` through
`sf.read(...)`, defines compact `sf.peak(...)` / `sf.background(...)` builders,
runs `sf.fit(...)`, and exports live notebook artifacts with one
`result.save(...)` call to `outputs/live/notebook/`. If you need more control,
advanced escape hatches such as `sf.OptimizerConfig`, `result.to_toml(...)`, and
the lower-level `spectrafit.jupyter` APIs remain available.

Expected persistent notebook artifacts appear under:

- `examples/basic/outputs/live/notebook/fit_basic.csv`
- `examples/basic/outputs/live/notebook/fit_basic.html`
- `examples/basic/outputs/live/notebook/metric_basic.csv`
- `examples/basic/outputs/live/notebook/peaks_basic.csv`
- `examples/basic/outputs/live/notebook/report_basic.toml`
- `examples/basic/outputs/live/notebook/basic.lock`

Use these files when you want notebook-friendly CSV exports that can be
replotted, compared, or versioned alongside exploratory analysis.

**Optional Step 4 — generate a local validation overlay:**

```bash
uv run poe generate-plots
```

If you generate local validation plots, inspect
`examples/basic/fit_validation.html` to compare the synthetic dataset and
fitted curve at a glance. This HTML file is generated on demand and is not
treated as a committed source-of-truth artifact.

## Expected outcome

After running both surfaces, you should be able to answer:

- Does the fitted Gaussian center recover the peak near `0.0`?
- Does the flat linear background stay close to the committed truth?
- Do the CLI and notebook outputs both appear in the expected `outputs/live/`
  subdirectories?

## Files

| File | Description |
|------|-------------|
| `input.toml` | v2 fitting configuration |
| `data.csv` | Synthetic spectrum (200 points, −2 to 2) |
| `notebook.ipynb` | Runnable notebook rooted in this example |
| `fit_validation.html` | Generated Plotly validation overlay (via `uv run poe generate-plots`) |
| `outputs/live/cli/` | Persistent CLI artifacts for this example |
| `outputs/live/notebook/` | Persistent notebook artifacts for this example |

## Schema Notes

- `schema_version = "2.0"` selects the v2 parser path.
- `[[components]]` blocks list models in fit order; the composite signal is
  their sum.
- Each parameter table accepts `value`, `bounds`, `vary`, and (optionally)
  `expr` for cross-component constraints.
- Model names are lower-case strings from the SpectraFit registry (e.g.
  `"gaussian"`, `"linear"`).

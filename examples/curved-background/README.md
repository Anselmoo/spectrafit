# Curved Background Example

Fit a single Gaussian peak on top of a gently curved quadratic baseline.

This example is the best next step after `examples/basic/` when your data is
still single-spectrum but the baseline is no longer flat enough for a simple
linear background.

## What this example teaches

1. How to fit a peak when baseline curvature matters
2. How `polynom2` complements peak models in both CLI and notebook workflows
3. How to inspect the same scenario through report-style CLI outputs and the
   one-import notebook workflow

## Ground Truth Components

| Component | Model | Parameters |
|-----------|-------|------------|
| `peak1` | `gaussian` | amplitude `1.1`, center `0.35`, fwhmg `0.45` |
| `bg` | `polynom2` | coefficient0 `0.08`, coefficient1 `-0.03`, coefficient2 `0.02` |

Gaussian noise with `scale=0.015` and `seed=42` was added to the clean signal.

## How to Run

**Step 1 - regenerate the committed synthetic artifacts if needed:**

```bash
uv run poe generate-examples
```

**Step 2 - run the CLI fit:**

```bash
uv run spectrafit fit examples/curved-background/input.toml --noplot
```

Expected persistent CLI artifacts appear under:

- `examples/curved-background/outputs/live/cli/curved-background_fit.csv`
- `examples/curved-background/outputs/live/cli/curved-background_fit.html`
- `examples/curved-background/outputs/live/cli/curved-background_summary.json`

**Step 3 - open the local notebook:**

```bash
jupyter lab examples/curved-background/notebook.ipynb
```

The committed notebook is the primary beginner path for this example: it
imports `spectrafit.notebook as sf`, loads the local `data.csv` through
`sf.read(...)`, defines compact `sf.peak(...)` / `sf.background(...)` builders,
runs `sf.fit(...)`, and exports live notebook artifacts with one
`result.save(...)` call to `outputs/live/notebook/`. Advanced escape hatches
such as `sf.OptimizerConfig`, `result.to_toml(...)`, and the lower-level
`spectrafit.jupyter` APIs remain available when you need them.

Expected persistent notebook artifacts appear under:

- `examples/curved-background/outputs/live/notebook/fit_curved-background.csv`
- `examples/curved-background/outputs/live/notebook/fit_curved-background.html`
- `examples/curved-background/outputs/live/notebook/metric_curved-background.csv`
- `examples/curved-background/outputs/live/notebook/peaks_curved-background.csv`
- `examples/curved-background/outputs/live/notebook/report_curved-background.toml`
- `examples/curved-background/outputs/live/notebook/curved-background.lock`

**Optional Step 4 - generate a local validation overlay:**

```bash
uv run poe generate-plots
```

If you generate local validation plots, inspect
`examples/curved-background/fit_validation.html` to compare the synthetic data
and fitted shape. This HTML file is generated on demand and is not treated as a
committed source-of-truth artifact.

## Expected Outcome

After running both surfaces, you should be able to confirm:

- the Gaussian peak is recovered near `0.35`
- the quadratic baseline absorbs slow curvature instead of distorting the peak
- both `outputs/live/cli/` and `outputs/live/notebook/` contain the documented files

## Files

| File | Description |
|------|-------------|
| `input.toml` | v2 fitting configuration with a quadratic baseline |
| `data.csv` | Synthetic spectrum with curved background |
| `notebook.ipynb` | Runnable notebook rooted in this example |
| `fit_validation.html` | Generated Plotly validation overlay (via `uv run poe generate-plots`) |
| `outputs/live/cli/` | Persistent CLI artifacts for this example |
| `outputs/live/notebook/` | Persistent notebook artifacts for this example |

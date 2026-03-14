# Peak Plus Edge Example

Fit a pseudo-Voigt resonance peak riding on a smooth error-function edge and a
small constant offset.

This example expands the shipped examples beyond "peak plus baseline" by showing
how SpectraFit can model a sharp feature and a step-like background in the same
single-spectrum workflow.

## What this example teaches

1. How to combine peak and step models in one v2 config
2. How edge-like backgrounds change the interpretation of the fit
3. How the same fit can be explored through both CLI outputs and the one-import notebook workflow

## Ground Truth Components

| Component | Model | Parameters |
|-----------|-------|------------|
| `peak1` | `pseudovoigt` | amplitude `0.9`, center `0.65`, fwhmg `0.35`, fwhml `0.30` |
| `edge` | `erf` | amplitude `0.4`, center `-0.3`, sigma `0.45` |
| `bg` | `constant` | amplitude `0.06` |

Gaussian noise with `scale=0.012` and `seed=42` was added to the clean signal.

## How to Run

**Step 1 - regenerate the committed synthetic artifacts if needed:**

```bash
uv run poe generate-examples
```

**Step 2 - run the CLI fit:**

```bash
uv run spectrafit fit examples/peak-plus-edge/input.toml --noplot
```

Expected persistent CLI artifacts appear under:

- `examples/peak-plus-edge/outputs/live/cli/peak-plus-edge_fit.csv`
- `examples/peak-plus-edge/outputs/live/cli/peak-plus-edge_fit.html`
- `examples/peak-plus-edge/outputs/live/cli/peak-plus-edge_summary.json`

**Step 3 - open the local notebook:**

```bash
jupyter lab examples/peak-plus-edge/notebook.ipynb
```

The committed notebook is the primary beginner path for this example: it
imports `spectrafit.notebook as sf`, loads the local `data.csv` through
`sf.read(...)`, defines compact `sf.peak(...)` / `sf.background(...)` builders,
runs `sf.fit(...)`, and exports live notebook artifacts with one
`result.save(...)` call to `outputs/live/notebook/`. Advanced escape hatches
such as `sf.OptimizerConfig`, `result.to_toml(...)`, and the lower-level
`spectrafit.jupyter` APIs remain available when you need them.

Expected persistent notebook artifacts appear under:

- `examples/peak-plus-edge/outputs/live/notebook/fit_peak-plus-edge.csv`
- `examples/peak-plus-edge/outputs/live/notebook/fit_peak-plus-edge.html`
- `examples/peak-plus-edge/outputs/live/notebook/metric_peak-plus-edge.csv`
- `examples/peak-plus-edge/outputs/live/notebook/peaks_peak-plus-edge.csv`
- `examples/peak-plus-edge/outputs/live/notebook/report_peak-plus-edge.toml`
- `examples/peak-plus-edge/outputs/live/notebook/peak-plus-edge.lock`

**Optional Step 4 - generate a local validation overlay:**

```bash
uv run poe generate-plots
```

If you generate local validation plots, inspect
`examples/peak-plus-edge/fit_validation.html` to compare the synthetic data and
fitted shape. This HTML file is generated on demand and is not treated as a
committed source-of-truth artifact.

## Expected Outcome

After running both surfaces, you should be able to confirm:

- the pseudo-Voigt peak is recovered near `0.65`
- the smooth edge is separated from the peak instead of being absorbed as noise
- both `outputs/live/cli/` and `outputs/live/notebook/` contain the documented files

## Files

| File | Description |
|------|-------------|
| `input.toml` | v2 fitting configuration with a peak and smooth edge |
| `data.csv` | Synthetic spectrum with an edge-like background |
| `notebook.ipynb` | Runnable notebook rooted in this example |
| `fit_validation.html` | Generated Plotly validation overlay (via `uv run poe generate-plots`) |
| `outputs/live/cli/` | Persistent CLI artifacts for this example |
| `outputs/live/notebook/` | Persistent notebook artifacts for this example |

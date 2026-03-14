# Two-Peak Constrained Example

Fit two overlapping peaks — a Gaussian and a Pseudo-Voigt — on a flat linear
background, while enforcing physical constraints between components using
SpectraFit's **dot-notation constraint system**.

This is the best example for a scientist who wants to move beyond a simple
single-peak fit and learn how SpectraFit encodes physically meaningful
relationships directly in the v2 TOML.

## What this example teaches

1. How to express cross-component constraints directly in `input.toml`
2. How overlapping peaks behave in both CLI and notebook workflows
3. How to inspect the persistent live artifacts written under `outputs/live/`
4. How dot-notation expressions map to lmfit-compatible parameter names

## Constraints Demonstrated

### 1. Fixed peak separation — `expr = "p1.center + 1.0"`

```toml
[[components]]
id    = "p2"
model = "pseudovoigt"

[components.parameters]
center = { value = 0.5, vary = false, expr = "p1.center + 1.0" }
```

The center of `p2` is algebraically tied to `p1.center`.  The solver is free
to move `p1.center`, but the 1.0 eV gap between the two peaks is never broken.
`vary = false` is required whenever `expr` is set.

### 2. Coupled widths — `expr = "p2.fwhmg"`

```toml
fwhml = { value = 0.25, vary = false, expr = "p2.fwhmg" }
```

The Lorentzian width of `p2` tracks its own Gaussian width, enforcing a
symmetric pseudo-Voigt profile throughout the optimisation.

## How Dot-Notation Works

SpectraFit translates `"p1.center"` → `"p1_center"` (lmfit parameter name)
automatically at load time.  The expression string is passed directly to
lmfit's constraint engine, so any arithmetic lmfit supports is valid.

## Ground Truth Parameters

| Component | Model         | Parameter | Value | Varies | Constraint              |
|-----------|---------------|-----------|-------|--------|-------------------------|
| `p1`      | gaussian      | amplitude | 1.0   | yes    | —                       |
| `p1`      | gaussian      | center    | −0.5  | yes    | —                       |
| `p1`      | gaussian      | fwhmg     | 0.3   | yes    | —                       |
| `p2`      | pseudovoigt   | amplitude | 0.8   | yes    | —                       |
| `p2`      | pseudovoigt   | center    | 0.5   | no     | `p1.center + 1.0`       |
| `p2`      | pseudovoigt   | fwhmg     | 0.25  | yes    | —                       |
| `p2`      | pseudovoigt   | fwhml     | 0.25  | no     | `p2.fwhmg`              |
| `bg`      | linear        | slope     | 0.0   | no     | —                       |
| `bg`      | linear        | intercept | 0.02  | yes    | —                       |

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
uv run spectrafit fit examples/two-peak-constrained/input.toml --noplot
```

Expected persistent CLI artifacts appear under:

- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_fit.csv`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_fit.html`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_components.csv`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_correlation.csv`
- `examples/two-peak-constrained/outputs/live/cli/two-peak-constrained_summary.json`
- `examples/two-peak-constrained/outputs/live/cli/input.resolved.json`

Use these files when you want the resolved config plus the richer report-style
tables that make it easy to inspect parameter coupling and fit quality.

**Step 3 — open the local notebook:**

```bash
jupyter lab examples/two-peak-constrained/notebook.ipynb
```

The committed notebook is the primary beginner path for this example: it
imports `spectrafit.notebook as sf`, loads the local `data.csv` through
`sf.read(...)`, mirrors the TOML constraints with compact builders plus
`sf.tie("p1.center + 1.0")` / `sf.tie("p2.fwhmg")`, runs `sf.fit(...)`, and
exports live notebook artifacts with one `result.save(...)` call to
`outputs/live/notebook/`. Advanced escape hatches such as
`sf.OptimizerConfig`, `result.to_toml(...)`, and the lower-level
`spectrafit.jupyter` APIs remain available when you need them.

Expected persistent notebook artifacts appear under:

- `examples/two-peak-constrained/outputs/live/notebook/fit_two-peak-constrained.csv`
- `examples/two-peak-constrained/outputs/live/notebook/fit_two-peak-constrained.html`
- `examples/two-peak-constrained/outputs/live/notebook/metric_two-peak-constrained.csv`
- `examples/two-peak-constrained/outputs/live/notebook/peaks_two-peak-constrained.csv`
- `examples/two-peak-constrained/outputs/live/notebook/report_two-peak-constrained.toml`
- `examples/two-peak-constrained/outputs/live/notebook/two-peak-constrained.lock`

Use these when you want notebook-oriented CSV exports that can be inspected,
replotted, and compared while iterating on constraints.

**Optional Step 4 — generate a local validation overlay:**

```bash
uv run poe generate-plots
```

If you generate local validation plots, inspect
`examples/two-peak-constrained/fit_validation.html` to compare the synthetic
data and the expected fitted shape. This HTML file is generated on demand and
is not treated as a committed source-of-truth artifact.

## Expected outcome

After running both surfaces, you should be able to confirm:

- `p2.center` remains offset from `p1.center` by `+1.0`
- `p2.fwhml` follows `p2.fwhmg`
- the overlapping peaks are still separated in the exported fit data
- both `outputs/live/cli/` and `outputs/live/notebook/` contain the documented files

## Files

| File | Description |
|------|-------------|
| `input.toml` | v2 fitting configuration with constraints |
| `data.csv` | Synthetic spectrum (200 points, −2 to 2) |
| `notebook.ipynb` | Runnable notebook rooted in this example |
| `fit_validation.html` | Generated Plotly validation overlay (via `uv run poe generate-plots`) |
| `outputs/live/cli/` | Persistent CLI artifacts for this example |
| `outputs/live/notebook/` | Persistent notebook artifacts for this example |

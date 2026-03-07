# Two-Peak Constrained Example

Fit two overlapping peaks — a Gaussian and a Pseudo-Voigt — on a flat linear
background, while enforcing physical constraints between components using
SpectraFit's **dot-notation constraint system**.

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

**Step 1 — (re-)generate the synthetic data:**

```bash
uv run poe generate-examples
```

**Step 2 — run the fit:**

```bash
uv run spectrafit fit examples/two-peak-constrained/input.toml --noplot
```

## Files

| File        | Description                               |
|-------------|-------------------------------------------|
| `input.toml`| v2 fitting configuration with constraints |
| `data.csv`  | Synthetic spectrum (200 points, −2 to 2)  |

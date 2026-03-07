# Basic Example — Single Gaussian Peak

Fit a single Gaussian peak sitting on a flat linear background.
This is the simplest possible SpectraFit v2 configuration and is a good
starting point for learning the schema.

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

**Step 1 — (re-)generate the synthetic data:**

```bash
uv run poe generate-examples
```

**Step 2 — run the fit:**

```bash
uv run spectrafit fit examples/basic/input.toml --noplot
```

## Files

| File        | Description                               |
|-------------|-------------------------------------------|
| `input.toml`| v2 fitting configuration                  |
| `data.csv`  | Synthetic spectrum (200 points, −2 to 2)  |

## Schema Notes

- `schema_version = "2.0"` selects the v2 parser path.
- `[[components]]` blocks list models in fit order; the composite signal is
  their sum.
- Each parameter table accepts `value`, `bounds`, `vary`, and (optionally)
  `expr` for cross-component constraints.
- Model names are lower-case strings from the SpectraFit registry (e.g.
  `"gaussian"`, `"linear"`).

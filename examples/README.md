# SpectraFit v2 Examples

Ready-to-run fitting examples that demonstrate the v2 configuration schema.
Each example ships with a synthetic data file (`data.csv`) and a fully-
annotated `input.toml`.

## Examples

| Directory                 | Models used                        | Key feature                                    |
|---------------------------|------------------------------------|------------------------------------------------|
| `basic/`                  | Gaussian + Linear                  | Minimal single-peak fit; good starting point   |
| `two-peak-constrained/`   | Gaussian + Pseudo-Voigt + Linear   | Dot-notation cross-component constraints       |

## Quickstart

### Regenerate synthetic data

```bash
uv run poe generate-examples              # default seed=42
uv run poe generate-examples -- --seed 7  # reproducible alternative
```

### Run a fit

```bash
uv run spectrafit fit examples/basic/input.toml --noplot
uv run spectrafit fit examples/two-peak-constrained/input.toml --noplot
```

### Validate all examples (integration test)

```bash
uv run poe validate-examples
```

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

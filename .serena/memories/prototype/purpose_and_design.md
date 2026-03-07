# Prototype — Purpose, Need, and Design Rationale

## Why the prototype exists

All previous refactoring attempts in `docs/spikes/` failed because they inherited the
**deeply-nested 3-level dict + string-name recomposition** anti-pattern from the original
`spectrafit/` codebase. The root cause: every spike tried to refactor *in-place*, so the
nested `for` loops and `dict[str, Any]` contracts leaked into every new design.

The `prototype/` directory is a **clean-room reference implementation** — written from scratch
with zero imports from `spectrafit.*` — to prove out the correct architecture before the
full refactor is attempted again.

## What it is NOT

- Not a drop-in replacement for `spectrafit/` (different CLI, different output schema)
- Not subject to the same CI scope (`ruff check spectrafit/` does NOT cover `prototype/`)
- Not committed as production code; it is a living sandbox

## Core anti-patterns it avoids

| Anti-pattern (old) | Solution (prototype) |
|--------------------|----------------------|
| `dict[str, Any]` as pipeline contract | Pydantic v2 models with `extra="forbid"` |
| Nested `for` loops rebuilding string keys | `lmfit_param_name(id, field)` as single source |
| `@dataclass` for model metadata | `ModelInfo(BaseModel)` with `ConfigDict(frozen=True)` |
| `print()` for user output | `typer.echo()` / `typer.style()` |
| `output.lock` (TOML serialisation) | `output.json` via `json.dumps(model.model_dump(mode="json"))` |
| `min`/`max` as top-level keys | `bounds = [min, max]` inline table |
| Implicit parameter naming via f-strings | `lmfit_param_name(id, field)` only |
| lmfit model composition via manual dicts | `functools.reduce(operator.add, models)` |

## Key design decisions

- **`lmfit_param_name(id, field)`** — the single source of truth for `{id}_{field}` naming.
  No inline f-strings elsewhere. Enforces consistency across build, fit, and decompose steps.
- **`apply_hints()` pattern** — `model.set_param_hint()` on each individual model *before*
  `composite.make_params()`. lmfit applies prefix internally; no manual dict iteration.
- **Dot-notation expr** — `"p1.center + 1.0"` translated to `"p1_center + 1.0"` at parse
  time via `FitParameterSpec.translate_expr`. User-facing notation stays human-readable.
- **`ConfigError(ValueError)`** — wraps all parse/validation errors with `path` context for
  actionable diagnostics.
- **`extra="forbid"`** on all input Pydantic models — unknown fields raise immediately.

## How to use it as a reference

When refactoring a `spectrafit/` module, look at the corresponding prototype module:

| What to refactor | Prototype reference |
|------------------|---------------------|
| Model registry / functions | `prototype/model_functions.py` |
| Input schema / config loading | `prototype/input_output_interface.py` |
| Fitting pipeline | `prototype/core_fitting.py` |
| Plotting | `prototype/visualization.py` |
| Synthetic data / test fixtures | `prototype/synth_data.py` |
| Input config format | `prototype/input.toml` |

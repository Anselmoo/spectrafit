---
applyTo: "spectrafit/**/*.py,prototype/**/*.py"
---

# Prototype Reference Architecture

## What the Prototype Is

`prototype/` is a **clean-room reference implementation** with zero imports from
`spectrafit.*`. It was written from scratch to prove out the correct architecture before
the full refactor, avoiding the anti-patterns inherited by previous in-place spikes.

## What the Prototype Is NOT

- Not a drop-in replacement for `spectrafit/` (different CLI, different output schema)
- Not subject to CI ruff scope (`ruff check spectrafit/` does NOT cover `prototype/`)
- Not production code — it is a living sandbox and reference

## Module Mapping

| What to implement in `spectrafit/` | Prototype reference |
|------------------------------------|---------------------|
| Parameter naming | `prototype/model_functions.py` → `lmfit_param_name()`, `sanitize_component_id()` |
| Model functions + `ModelInfo` | `prototype/model_functions.py` → `spectrafit/models/registry.py` |
| Input Pydantic models | `prototype/input_output_interface.py` → `spectrafit/models/peak_models.py`, `spectrafit/models/data_config.py` |
| Fitting pipeline steps | `prototype/core_fitting.py` → `spectrafit/models/bundle.py`, `spectrafit/models/solver.py` |
| Plot output | `prototype/visualization.py` → `spectrafit/plotting.py` (deferred) |
| Synthetic test data | `prototype/synth_data.py` → `tests/fixtures/` |
| v2 input schema | `prototype/input.toml` → `tests/fixtures/sample_v2.toml` |

## Key Patterns (copy these, do not re-invent)

### 1. Single Naming Function

```python
# prototype/model_functions.py — mirrored in spectrafit/models/naming.py
def lmfit_param_name(component_id: str, field_name: str) -> str:
    """Return the lmfit parameter name for a component field."""
    return f"{sanitize_component_id(component_id)}_{field_name}"
```

**No inline f-strings** for parameter naming anywhere else.

### 2. apply_hints() Pattern

```python
# prototype/core_fitting.py — mirrored in spectrafit/models/bundle.py
def _apply_hints(model: lmfit.Model, component: ComponentSpec) -> lmfit.Parameters:
    for field_name, spec in component.parameters.items():
        lmfit_name = lmfit_param_name(component.id, field_name)
        spec.apply_to(model, lmfit_name)
    return model.make_params()
```

`set_param_hint()` is called on the individual model **before** `composite.make_params()`.

### 3. Composite Model via functools.reduce

```python
# Do this:
import functools, operator
composite = functools.reduce(operator.add, models)

# NOT this (manual dict iteration):
params = {}
for m in models:
    params.update(m.make_params())
```

### 4. Dot-Notation Expression Translation

```python
# User writes:  expr = "p1.center + 1.0"
# Translated to: "p1_center + 1.0"
from spectrafit.models.naming import translate_dot_notation
lmfit_expr = translate_dot_notation(user_expr)
```

Translation happens at **parse time** (in `FitParameter.translate_expr` validator).
The user-facing notation stays human-readable; lmfit sees only underscore form.

### 5. extra="forbid" on All Input Models

```python
class MyInputModel(BaseModel):
    model_config = ConfigDict(extra="forbid")  # Unknown fields raise immediately
```

### 6. ConfigError with path context

```python
from spectrafit.models.peak_models import ConfigError

raise ConfigError("Unknown model 'foo'", path=Path("input.toml"))
# Produces: "[input.toml] Unknown model 'foo'"
```

## Running the Prototype

```bash
# Generate synthetic data
uv run python prototype/synth_data.py

# Run full fitting pipeline
uv run python prototype/core_fitting.py prototype/input.toml

# Lint (prototype is excluded from CI; run manually)
uv run ruff check prototype/
```

## Invariant: prototype/ Must Stay Independent

`prototype/` must never import from `spectrafit.*`. If you are porting a pattern,
copy it (with adaptation) into `spectrafit/`. Do not add `spectrafit` imports to
`prototype/` to share code — create a shared utility in `spectrafit/` instead.

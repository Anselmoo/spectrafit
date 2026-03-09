# Phase 11 — scaffolding.py Pydantic Alignment + v2 TOML Output

## Root Cause
Three layers in `spectrafit/cli/commands/scaffolding.py` produce the banned v1 format:

| Layer | Problem | Fix |
|-------|---------|-----|
| `_PARAM_DEFAULTS` | `dict[str,dict[str,object]]` — raw dicts | `dict[str,FitParameter]` — validated models |
| `_build_peak()` | Returns `{model: {param: raw_dict}}` | `_build_component()` returns `Component` |
| `_build_config()` | Wraps in `{"fitting": {...}}` v1 | `{"components": [comp.model_dump(exclude_none=True)...], "minimizer": {...}, "optimizer": {...}}` |
| `new_config` default | `OutputFormatEnum.JSON` | `OutputFormatEnum.TOML` |
| `tomli_w` | `try/except ImportError` × 2 — it's a hard dep | Direct `import tomli_w` at module top |

## Verified Approach
`Component.model_dump(exclude_none=True)` + `tomli_w.dumps()` produces correct `[[components]]` TOML.
Round-trip through `UnifiedFittingConfig._migrate_v2_format` verified working.

## Implementation Steps (in order)

### 1. Replace _PARAM_DEFAULTS
```python
from spectrafit.models.peak_models import Component, FitParameter

_PARAM_DEFAULTS: dict[str, FitParameter] = {
    "amplitude": FitParameter(value=1.0, min=0.0, max=2.0),
    "center": FitParameter(value=0.0, min=-2.0, max=2.0),
    "fwhmg": FitParameter(value=0.1, min=0.02, max=0.5),
    "fwhml": FitParameter(value=0.1, min=0.01, max=0.5),
    "fwhmv": FitParameter(value=0.1, min=0.02, max=0.5),
    "gamma": FitParameter(value=0.5, min=0.0, max=1.0),
    "sigma": FitParameter(value=0.1, min=0.01, max=1.0),
    "width": FitParameter(value=0.1, min=0.02, max=0.5),
    "slope": FitParameter(value=0.0, min=-10.0, max=10.0),
    "intercept": FitParameter(value=0.0, min=-10.0, max=10.0),
    "decay": FitParameter(value=1.0, min=0.01, max=10.0),
    "exponent": FitParameter(value=1.0, min=0.1, max=10.0),
    "skewness": FitParameter(value=0.0, min=-5.0, max=5.0),
    "kurtosis": FitParameter(value=0.0, min=-5.0, max=5.0),
    "coefficient0": FitParameter(value=0.0, min=-10.0, max=10.0),
    "coefficient1": FitParameter(value=0.0, min=-10.0, max=10.0),
    "coefficient2": FitParameter(value=0.0, min=-10.0, max=10.0),
    "coefficient3": FitParameter(value=0.0, min=-10.0, max=10.0),
}
```

### 2. Update _default_for_param()
```python
def _default_for_param(name: str) -> FitParameter:
    return _PARAM_DEFAULTS.get(name, FitParameter(value=0.0, min=-1.0, max=1.0))
```

### 3. Replace _build_peak() with _build_component()
```python
def _build_component(model_name: str, num: int) -> Component:
    info = REGISTRY.get(model_name)
    return Component(
        id=str(num),
        model=model_name,
        parameters={p: _default_for_param(p) for p in info.parameters},
    )
```

### 4. Rewrite _build_config() — v2 format
```python
def _build_config(peaks: list[tuple[int, str]]) -> dict[str, object]:
    components = [_build_component(model, num) for num, model in peaks]
    return {
        "components": [c.model_dump(exclude_none=True) for c in components],
        "minimizer": {"nan_policy": "propagate", "calc_covar": True},
        "optimizer": {"max_nfev": 1000, "method": "leastsq"},
    }
```

### 5. Direct tomli_w import + simplify _write_config / _config_to_stdout
Remove `try/except ImportError` blocks. Add `import tomli_w` at module top.
Remove `_dict_to_toml` fallback import from convert.py.

### 6. Change new_config default fmt
Line ~442: `fmt: OutputFormatEnum = OutputFormatEnum.TOML`  (was JSON)

### 7. Tests
- `test_init_command.py`: add assertion that `"components"` in config, `"fitting"` NOT in config
- `tests/unit/test_new_config.py`: golden table for `_build_config()` + CLI smoke tests

## Expected Output (verified)
```toml
[[components]]
id = "p1"
model = "voigt"

[components.parameters.center]
value = 0.0
min = -2.0
max = 2.0
vary = true
...

[minimizer]
nan_policy = "propagate"
calc_covar = true

[optimizer]
max_nfev = 1000
method = "leastsq"
```

## Files Changed
- `spectrafit/cli/commands/scaffolding.py` — main change
- `tests/unit/test_init_command.py` — add v2 assertions
- `tests/unit/test_new_config.py` — new golden-table test file

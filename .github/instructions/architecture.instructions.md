---
applyTo: "spectrafit/**/*.py"
---

# SpectraFit Architecture — v2.0.0

## Pipeline Data Flow

```
CLI / Jupyter / API
  → UnifiedFittingConfig (spectrafit/core/fitting_config.py)  ← single validated entry point
  → FittingPipeline (spectrafit/core/pipeline.py)
      → load_data(DataConfig)           ← spectrafit/core/data_loader.py
      → PreProcessing                   ← spectrafit/core/preprocessing.py
      → SolverModels(df, config)        ← spectrafit/models/solver.py
          → config.build_composite_model()
              → build_composite_bundle(components)  ← spectrafit/models/bundle.py
                  → Component.to_lmfit_model()       ← spectrafit/models/peak_models.py
                  → functools.reduce(operator.add, models)
                  → Component.apply_parameters(params)
      → PostProcessing                  ← spectrafit/core/postprocessing.py
  → FittingResult → export / report
```

## Module Responsibilities

| Module | Responsibility |
|--------|---------------|
| `spectrafit/core/fitting_config.py` | `UnifiedFittingConfig` — single validated entry point; `components` computed field; `build_composite_model()` |
| `spectrafit/models/peak_models.py` | `FitParameter`, `Component` — Pydantic v2 models for a single parameter and a single spectral component |
| `spectrafit/models/bundle.py` | `CompositeModelBundle`, `build_composite_bundle()` — lmfit model composition via `model.__add__` |
| `spectrafit/models/naming.py` | `lmfit_param_name()`, `sanitize_component_id()`, `translate_dot_notation()` — **single source of truth for all parameter naming** |
| `spectrafit/models/fitting_context.py` | `FittingContext`, `FittingMode` — replaces legacy `global_: int` code smell |
| `spectrafit/models/data_config.py` | `DataConfig` — typed data-loading configuration |
| `spectrafit/models/solver.py` | `SolverModels` — orchestrates fit execution; uses `build_composite_model()` for standard fits |
| `spectrafit/models/registry.py` | `REGISTRY`, `ModelInfo`, `model_check()` — model name → function mapping |
| `spectrafit/models/types.py` | `FittingArgs`, `PeaksDict`, `PeakModelSpec` TypeAliases — **being phased out in v2.1.0** |
| `spectrafit/models/autopeak.py` | **Re-export shim only** — deprecated, scheduled for removal in v2.1.0 |
| `spectrafit/core/preprocessing.py` | `PreProcessing` — **FROZEN** (Layer 4, do not refactor until Phase 6+) |
| `spectrafit/core/postprocessing.py` | `PostProcessing` — **FROZEN** (Layer 4) |
| `spectrafit/plugins/` | Jupyter plugin — **FROZEN** until Phase 6+ |

## Critical Invariants

1. **All lmfit parameter names are built exclusively via `lmfit_param_name(id, field)`.**
   No inline f-strings for parameter naming anywhere in the codebase.

2. **`UnifiedFittingConfig` is the single validated entry point.**
   `FittingPipeline.__init__` accepts `UnifiedFittingConfig | dict[str, Any]`; the dict path
   coerces via `UnifiedFittingConfig.from_dict()`. No raw dict may cross module boundaries
   as a pipeline contract.

3. **`extra="forbid"` on all input Pydantic models.**
   Unknown fields must raise immediately. Use `model_config = ConfigDict(extra="forbid")`.

4. **lmfit model composition via `functools.reduce(operator.add, models)`.**
   Never iterate parameter dicts manually to build a composite model.

5. **`apply_hints()` pattern: `model.set_param_hint()` before `composite.make_params()`.**
   Per-component parameter hints are applied on individual models before composition.

## v1 Backward Compatibility

`UnifiedFittingConfig.migrate_v1_format()` (`@model_validator(mode="before")`) transparently
unwraps two legacy input shapes:

- Pattern 1: `{"fitting": {"parameters": {...}, "peaks": {...}}}` — v1 nested TOML
- Pattern 2: `{"parameters": {...}, "peaks": {...}}` — v1 flat with legacy minimizer/optimizer keys

The canonical v2 input format uses a flat `[[components]]` TOML array-of-tables.
See `prototype/input.toml` for the reference schema.

## Circular Import Risk

`spectrafit/core/__init__.py` eagerly imports `FittingPipeline`, which triggers the
postprocessing chain. **Do not move symbols** to `spectrafit/core/` if they are imported
(even transitively) by modules that `spectrafit/core/__init__.py` imports.
`spectrafit/models/model_parameters.py` must stay in `spectrafit/models/` for this reason.

## Frozen Modules (Phase 6+)

These modules are **not to be refactored until Phases 6+** of the migration plan:

- `spectrafit/core/preprocessing.py`
- `spectrafit/core/postprocessing.py`
- `spectrafit/core/export.py`
- `spectrafit/plugins/` (entire directory)
- `spectrafit/report/`
- `spectrafit/api/` (except additive changes)

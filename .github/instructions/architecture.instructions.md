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
| `spectrafit/models/fitting_context.py` | `FittingContext`, `FittingMode`, `EnvironmentMode`, `detect_environment()` — replaces legacy `global_: int` code smell; auto-detects CLI / Notebook / API |
| `spectrafit/models/fit_result.py` | `FitResult` — **complete output container**; sub-models `FitInsights`, `DataSummary`, `ConfidenceResults`, `VariableFitResult`, `FitConfigurations`; `from_legacy_dict()` bridge |
| `spectrafit/models/plot_config.py` | `PlotConfig(BaseModel, extra="forbid")` — typed plot configuration |
| `spectrafit/models/data_config.py` | `DataConfig` — typed data-loading configuration |
| `spectrafit/models/solver.py` | `SolverModels` — orchestrates fit execution; uses `build_composite_model()` for standard fits |
| `spectrafit/models/registry.py` | `REGISTRY`, `ModelInfo`, `model_check()` — model name → function mapping |
| `spectrafit/models/types.py` | `FittingArgs`, `PeaksDict`, `PeakModelSpec` TypeAliases — **being phased out in v2.1.0** |
| `spectrafit/models/autopeak.py` | **Re-export shim only** — deprecated, scheduled for removal in v2.1.0 |
| `spectrafit/jupyter/` | Core Jupyter integration — `SpectraFitNotebook`, `SolverResults(BaseModel)`, `ExportReport` |
| `spectrafit/jupyter/solver.py` | `SolverResults(BaseModel, frozen=True)` — typed Jupyter result view wrapping `FitResult`; replaces dict-access pattern |
| `spectrafit/cli/banner.py` | `render_startup_panel(console, env)` — Rich startup panel; TTY-gated |
| `spectrafit/cli/commands/scaffolding.py` | `init` command — `InitConfig(BaseModel)`, `InitEnvironment` enum, Rich wizard, TOML/notebook scaffolding |
| `spectrafit/core/preprocessing.py` | `PreProcessing` — **FROZEN** (Layer 4, do not refactor until Phase 6+) |
| `spectrafit/core/postprocessing.py` | `PostProcessing` — **FROZEN** (Layer 4) |
| `spectrafit/plugins/` | Re-export shims only — `plugins/notebook/` re-exports from `spectrafit/jupyter/` |

## Critical Invariants

1. **All lmfit parameter names are built exclusively via `lmfit_param_name(id, field)`.**
   No inline f-strings for parameter naming anywhere in the codebase.

2. **`UnifiedFittingConfig` is the single validated entry point.**
   `FittingPipeline.__init__` accepts `UnifiedFittingConfig | dict[str, Any]`; the dict path
   coerces via `UnifiedFittingConfig.from_dict()`. No raw dict may cross module boundaries
   as a pipeline contract.

3. **`extra="forbid"` on all input Pydantic models.**
   Unknown fields must raise immediately. Use `model_config = ConfigDict(extra="forbid")`.
   Exception: legacy result containers (`SolverAPI`, `ParameterSpec`, `FitStatisticsAPI`) keep
   `extra="allow"` with a comment: `# intentional: result container, v2.1 migration target`.

4. **lmfit model composition via `functools.reduce(operator.add, models)`.**
   Never iterate parameter dicts manually to build a composite model.

5. **`apply_hints()` pattern: `model.set_param_hint()` before `composite.make_params()`.**
   Per-component parameter hints are applied on individual models before composition.

6. **`FitResult` is the single authoritative output container.**
   All consumers (CLI, Jupyter display, export) receive a typed `FitResult` instance.
   No raw `FittingArgs` dict may cross module boundaries as a pipeline output contract.
   Bridge path: `FitResult.from_legacy_dict(args)` during the v2 migration period.

7. **`SolverResults` wraps `FitResult` for Jupyter display.**
   All result access in `spectrafit/jupyter/` goes through `SolverResults.<property>`.
   No `self.args_out["key"]` dict access anywhere in `spectrafit/jupyter/`.

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

These modules are **not to be refactored until Phase 6+ / v2.1.0**:

| Module | Status |
|--------|--------|
| `spectrafit/core/preprocessing.py` | **Scheduled for modernisation** — Layer 4 wrapper being replaced with pure functions + `PreprocessResult` model in R7 |
| `spectrafit/core/postprocessing.py` | **FROZEN** — Layer 4 |
| `spectrafit/core/export.py` | **FROZEN** — Layer 4 |
| `spectrafit/plugins/` | Re-export shims only — `plugins/notebook/` re-exports from `spectrafit/jupyter/`; do not add new code here |
| `spectrafit/report/`  | **FROZEN** (Layer 4) |
| `spectrafit/api/`     | Input models: `extra="forbid"`. Result containers: `extra="allow"` with comment. Additive changes only. |

# Codebase Structure

```
spectrafit/
├── cli/                   # Typer CLI (subcommands: fit, validate, convert, report, plugins)
│   ├── main.py            # App entry point (run())
│   ├── _types.py          # Shared Enums
│   ├── _callbacks.py      # version/verbose callbacks
│   └── commands/          # fit.py, validate.py, convert.py, report.py, scaffolding.py
├── api/                   # Pydantic v2 models (data contracts)
│   ├── cmd_model.py       # CMDModelAPI – CLI arg model
│   ├── config_model.py    # CLIConfig, PipelineConfig, OutputConfig
│   ├── models_model.py    # Per-parameter API models (AmplitudeAPI, CenterAPI, …)
│   ├── tools_model.py     # SolverModelsAPI, MinimizerConfig, OptimizerConfig
│   ├── report_model.py    # Report Pydantic models
│   └── validation_model.py# Scientific validation models
├── core/                  # Business logic (pipeline, preprocessing, data loading)
│   ├── pipeline.py        # FittingPipeline, FittingResult, fitting_routine_pipeline()
│   ├── fitting_config.py  # UnifiedFittingConfig (key model – not yet wired into pipeline)
│   ├── preprocessing.py   # PreProcessing class
│   ├── postprocessing.py  # PostProcessing class
│   ├── data_loader.py     # load_data()
│   ├── export.py          # SaveResult
│   └── config.py          # Additional config helpers
├── models/                # Mathematical models & solver
│   ├── regular.py         # Distribution functions (gaussian, pseudovoigt, …)
│   ├── distributions.py   # More distribution helpers
│   ├── solver.py          # SolverModels (extends ModelParameters)
│   ├── autopeak.py        # LEGACY: ModelParameters, FittingArgs TypeAlias, PeaksDict TypeAlias
│   │                      # (AutoPeak detection removed in v2.0.0; module pending decomposition)
│   ├── registry.py        # REGISTRY mapping model names → functions
│   ├── builtin.py         # Legacy SolverModels import shim
│   └── global_fitting.py  # GlobalFittingConfig
├── report/                # Reporting (PrintingResults, metrics, confidence intervals)
├── plugins/               # Jupyter plugin, Mössbauer plugin
│   └── notebook/          # SpectraFitNotebook, export, plotting
├── generators/            # Synthetic data generation
├── utilities/             # Transformer helpers
├── app/                   # Jupyter app entry
└── spectrafit.py          # Legacy thin shim (do not extend)
```

## Test Structure (v2.0.0)

**Active test suite** — `testpaths = ["tests"]` in pyproject.toml:
```
tests/
├── conftest.py            # Shared fixtures: energy_axis, sample_*_spectrum,
│                          # tmp_output_dir, sample_dataframe, custom markers
├── unit/                  # Fast unit tests (<1s, no I/O)
│   ├── test_types.py      # TypeAlias sanity (PeaksDict, FittingArgs)
│   ├── test_fitting_config.py  # UnifiedFittingConfig
│   ├── test_model_parameters.py  # ModelParameters (post-rehoming)
│   ├── test_global_fitting.py  # GlobalFittingConfig
│   └── test_registry.py   # ReferenceKeys.model_check()
├── integration/           # Pipeline + CLI end-to-end
│   ├── test_pipeline.py   # FittingPipeline with UnifiedFittingConfig
│   ├── test_cli_fit.py    # CLI fit subcommand
│   └── test_v1_compat.py  # rixs/config.json backward-compat smoke test
└── validation/            # Scientific correctness
    ├── test_analytical.py
    └── test_numerical_stability.py
```

**Legacy test dirs** (excluded from default runs, scheduled for deletion):
- `spectrafit/*/test/` — 8 dirs, 42 files, ~9 300 lines tightly coupled to
  `FittingArgs = dict[str, Any]`. Each deleted once the corresponding v2.0.0
  module is refactored and a new test is written in `tests/`.

## Prototype (reference implementation — `prototype/`)
A self-contained, zero-`spectrafit.*`-import fitting reference:
```
prototype/
├── input.toml                # Modern flat schema: [[components]], bounds=[min,max],
│                             # schema_version="1.0", expr="p1.center + 1.0"
├── model_functions.py        # numpy models, MODEL_REGISTRY, ModelInfo (Pydantic BaseModel)
├── input_output_interface.py # All Pydantic v2 I/O: FitParameterSpec, ComponentSpec,
│                             # SolverConfig, PrototypeInput, PrototypeOutput, ConfigError
├── core_fitting.py           # Typer CLI; lmfit pipeline via functools.reduce + apply_hints
├── visualization.py          # 3-panel matplotlib figure; returns Path | None
├── synth_data.py             # Synthetic CSV generator with typer CLI
├── synth.csv                 # Generated data (gitignored artifact)
├── output.json               # Fit result (gitignored artifact)
└── fit_plot.png              # Plot artifact (gitignored artifact)
```
**Design principles**: lmfit-native `__add__` composition, `lmfit_param_name(id, field)` as
single source for `{id}_{field}` naming, `extra="forbid"` on all input models,
dot-notation expr translation (`p1.center` → `p1_center`) at parse time.
This prototype is the **reference architecture** for the future `spectrafit/` v2 refactor.

## Key Data Flow
```
CLI args (dict[str,Any])
  → UnifiedFittingConfig (core/fitting_config.py)  ← NOT YET WIRED
  → FittingPipeline (core/pipeline.py)
      → load_data() → PreProcessing → SolverModels → PostProcessing
  → FittingResult → PrintingResults / export
```

## Current Status (v2.0.0 migration — Phases 0–5 complete)

- `FittingPipeline` now accepts `UnifiedFittingConfig` directly (also accepts dict for compat)
- `autopeak.py` is a re-export shim (deprecated, removal in v2.1.0)
- `SolverModels(df, config)` uses `config.build_composite_model()` for standard fits
- `DataConfig.from_unified(config)` drives `load_data()`
- `FittingContext` / `FittingMode` replace legacy `global_: int`
- `.github/copilot-instructions.md` fully updated; `.github/instructions/` created

## Remaining Work (Phase 6–8)

- Phase 6: Delete `FittingArgs` pipeline contract, legacy `spectrafit/*/test/` dirs
- Phase 7: ✅ DONE — `.github/copilot-instructions.md` + `.github/instructions/` updated
- Phase 8: Surface MCMC/emcee; `BatchFittingConfig`; `FitResult(BaseModel)` output model

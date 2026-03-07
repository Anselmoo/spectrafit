# Spike Landscape — What to Use, What to Skip

All spikes live in `docs/spikes/`. Status is from frontmatter. A spike being 🟢 Complete
means the decision was made and implementation landed in the main codebase — do NOT
re-implement. 🔴 Not Started = still open work. 🟡 In Progress = prototype is the POC.

---

## 🟢 COMPLETE — Already implemented, use as reference

### `tooling-poethepoet-task-runner-spike.md`
**Decision:** poe is the task runner. `uv run poe ci` = canonical CI gate.
`poe test`, `poe lint`, `poe format`, `poe typecheck`, `poe typecheck-legacy` all live.

### `tooling-mypy-to-ty-migration-spike.md`
**Decision:** `ty` runs in warn-only mode (`poe typecheck`); `mypy` stays as hard-fail
fallback (`poe typecheck-legacy`) until `ty` matures. Do not remove mypy yet.

### `architecture-peaks-string-integer-key-contract-spike.md`
**Decision:** `UnifiedFittingConfig` validates that `peaks` keys are positive string integers
(`"1"`, `"2"`, …) via `@model_validator(mode="before")`. Non-sequential keys (e.g. `"1"`, `"3"`)
are allowed. Implementation: `fitting_config.py`. Tests: `tests/unit/test_fitting_config.py`.

### `architecture-input-schema-versioning-backward-compat-spike.md`
**Decision:** No `schema_version` field. Auto-detection by structural key presence.
`migrate_v1_format()` @model_validator in `UnifiedFittingConfig` transparently unwraps:
- Pattern 1: `{"fitting": {"parameters": {...}, "peaks": {...}}}` → flattens
- Pattern 2: `{"parameters": {...}, "peaks": {...}}` → hoists minimizer/optimizer to root
Implementation: `spectrafit/core/fitting_config.py`. Tests: `tests/integration/test_v1_compat.py`.

### `architecture-conf-interval-pydantic-model-spike.md`
**Decision:** 🟢 Complete (frontmatter). Goal: replace `conf_interval: bool | dict[str, Any]`
with a proper Pydantic model; eliminate `.pop()` mutation in `postprocessing.py:146`.
Check `spectrafit/core/fitting_config.py` + `postprocessing.py` for current state.

### `architecture-global-fitting-pipeline-integration-spike.md`
**Decision:** 🟢 Complete (frontmatter). `GlobalMode(IntEnum)` replaces bare int constants;
`GlobalFittingConfig` integration strategy decided.
Check `spectrafit/models/global_fitting.py` + `spectrafit/core/fitting_config.py` for current state.

---

## 🟡 IN PROGRESS — Prototype is the proof-of-concept

### `architecture-peaks-pydantic-model-pipeline-spike.md`
**This spike IS the architectural blueprint for `prototype/`.**
The final decision (after 3 iterative sub-decisions in the document):

> Adopt the `Component` model as canonical peak representation.
> `FittingContext` replaces `global_: int` code smell.

**Migration sequence decided:**
```
Phase 1: FitParameter + Component (new file, no breakage)
Phase 2: FittingContext (replaces global_ int)
Phase 3: UnifiedFittingConfig update — peaks → components via migrate_to_components
         + validate_unique_lmfit_names + validate_expr_references_exist
         + to_lmfit_params() method
Phase 4: Delete ModelParameters.define_parameters* methods
         → SolverModels calls config.to_lmfit_params() directly
Phase 5: Pipeline wiring — DataConfig + FittingContext + remove to_solver_args()
[FROZEN: postprocessing, export, plotting, report, api, plugins → Phase 7]
```

**The prototype in `prototype/` validates all of Phase 1–5 end-to-end.**
Use `prototype/` as the reference implementation when executing this migration in `spectrafit/`.

Key architectural insight from this spike:
> lmfit parameter naming (`gaussian_amplitude_1`) is a cosmetic output concern, not an
> architectural constraint. What matters is lmfit-native `Model.__add__` composition +
> per-component `model.eval()` for decomposition. The current `spectrafit/` reimplements
> this manually and incompletely.

---

## 🔴 NOT STARTED — Open work, concrete plans exist

### `architecture-autopeak-legacy-decomposition-spike.md`
**Goal:** Eliminate `autopeak.py`'s dual identity (defunct auto-detection name + live symbols).
**Concrete migration table from spike:**

| Symbol | Move to |
|--------|---------|
| `ParameterConstraint`, `ModelParameterSpec`, `PeakModelSpec`, `PeaksDict`, `FittingArgs` | `spectrafit/models/types.py` |
| `GLOBAL_NONE/STANDARD/WITH_PRE` constants | `GlobalMode(IntEnum)` in `global_fitting.py` |
| `ReferenceKeys.model_check()` | standalone fn in `spectrafit/models/registry.py` |
| `ModelParameters` class | `spectrafit/core/model_parameters.py` |
| `automodel_check()`, `__automodels__` | DELETE (confirmed dead code) |

**Sequencing constraint:** Must settle `ModelParameters` home BEFORE touching `FittingPipeline`
parameter-building step. `autopeak.py` becomes re-export shim during transition.

### `architecture-lmfit-parameter-naming-contract-spike.md`
**Goal:** Pin the formula `f"{key_2}_{key_3}_{key_1}"` (= `gaussian_amplitude_1`) as an
explicit tested contract before any refactoring changes it.
**Status:** 🔴 Not Started — but the prototype has already solved this differently:
- Prototype uses `lmfit_param_name(id, field)` → `{id}_{field}` (e.g. `p1_amplitude`)
- The old naming formula (`model_param_index`) is a v1 concern; v2 uses component `id` as prefix
- **Action:** Write a characterisation test before touching `autopeak.py` parameter loop

### `api-mcp-server-design-spike.md`
**Goal:** Define MCP tool surface for SpectraFit v2.0.0 (fitting operations as MCP tools).
**Prerequisite:** `UnifiedFittingConfig` must be the single validated entry point first.
**Status:** Intentionally deferred — do not start until pipeline refactor (Phases 1–5) is done.
`UnifiedFittingConfig.model_json_schema()` will directly serve as the MCP input schema.

# Copilot Instructions for SpectraFit

> **Version:** v2.0.0 migration in progress on branch `v2.0.0`
> **Detailed instructions:** see `.github/instructions/` for scoped files loaded automatically.

---

## Project Overview

SpectraFit fits 1D–3D X-ray absorption / emission spectra using `lmfit` + `scipy`.
CLI-first (`typer`), also usable as a Python API and a core `spectrafit.jupyter`
surface.
Package management: `uv`. Build backend: `hatchling`. Python 3.12–3.13.

**Entry points:**
- `spectrafit` → `spectrafit.cli.main:run`
- `spectrafit-jupyter` → `spectrafit.app.app:jupyter`

---

## Tech Stack

| Layer | Libraries |
|-------|-----------|
| Fitting engine | lmfit, scipy, numpy |
| Data models | **pydantic v2** (`extra="forbid"` on all input models) |
| CLI | typer |
| Data handling | pandas |
| Reporting | plotly, matplotlib, tabulate |
| Package manager | uv |
| Type checker | ty (hard-fail) |
| Linter | ruff |

---

## Architecture Snapshot (v2.0.0)

```
CLI / Jupyter / API
  → UnifiedFittingConfig          ← single validated entry point
  → FittingPipeline
      → load_data(DataConfig)
      → LmfitSolverRuntime(df, config)
          → config.build_composite_model()
              → build_composite_bundle(components)  ← functools.reduce(+, models)
      → PostProcessing [FROZEN]
  → FittingResult
  → reporting/service.py + reporting/dashboard.py
```

**Key modules:**
- `spectrafit/core/fitting_config.py` — `UnifiedFittingConfig` (central model)
- `spectrafit/core/solver_runtime.py` — `LmfitSolverRuntime`, `SolverExecutionPlan`
- `spectrafit/models/peak_models.py` — `FitParameter`, `Component`
- `spectrafit/models/bundle.py` — `CompositeModelBundle`, `build_composite_bundle()`
- `spectrafit/models/solver.py` — transitional runtime residue; do not expand ownership here
- `spectrafit/models/naming.py` — `lmfit_param_name()` (SINGLE source for all param names)
- `spectrafit/models/fitting_context.py` — `FittingContext`, `FittingMode`
- `spectrafit/models/data_config.py` — `DataConfig`
- `spectrafit/jupyter/materializer.py` — supported notebook materialization API
- `spectrafit/workflow/validation.py` — reusable live example validation logic
- `spectrafit/reporting/service.py` — canonical reporting and dashboard projection
- `spectrafit/reporting/dashboard.py` — deterministic static PNG dashboards

---

## Critical Invariants

1. **All lmfit parameter names via `lmfit_param_name(id, field)` only.** No inline f-strings.
2. **`UnifiedFittingConfig` is the sole pipeline entry point.** Never pass raw dicts across modules.
3. **`extra="forbid"` on all input Pydantic models.**
4. **`functools.reduce(operator.add, models)` for lmfit model composition.** Never iterate dicts.
5. **`from __future__ import annotations` in every module.**
6. **No `sys.exit()` in business logic.** Raise typed exceptions.
7. **`translate_dot_notation()` at parse time.** User writes `p1.center`; lmfit sees `p1_center`.
8. **Do not introduce new `from_legacy_dict()` usage.** Prefer typed construction via
   `model_validate()`, explicit adapters, or `from_dict()` entry points.
9. **Use PEP 695 `type` keyword for all type aliases (not `TypeAlias`). Use `StrEnum` for all
    string enums (not `str, Enum`).**
10. **Runtime orchestration lives in `spectrafit.core.*`, not `spectrafit.models.*`.**
    New runtime planning/execution belongs in `spectrafit/core/solver_runtime.py` or adjacent
    `core` modules. Existing files such as `spectrafit/models/solver.py`,
    `spectrafit/models/parameter_builder.py`, and `spectrafit/models/fitting_request.py` are
    migration targets and must shrink or move over time, not gain new responsibilities.
11. **Jupyter is a core surface, not a plugin-owned workflow.** New notebook work belongs in
    `spectrafit.jupyter.*`; do not reintroduce plugin-era ownership or docs language.
12. **Notebook authoring must be typed-first.** No new user-facing `config_payload`,
    `resolved_config_payload`, or giant dict-editing notebook flows. Prefer `Component`,
    `FitParameter`, `DataConfig`, `UnifiedFittingConfig`, and `config.with_data_infile(...)`.
13. **Reusable workflow logic belongs in `spectrafit/`, not `scripts/`.** Keep scripts as thin
    wrappers over package-owned modules such as `spectrafit.workflow.validation`.
14. **Reporting ownership lives in `spectrafit.reporting.*`.** Treat `spectrafit.report.*` as
    frozen compatibility only; new report or dashboard work belongs in `spectrafit.reporting`.
15. **Do not commit heavyweight generated example artifacts as source-of-truth UX.** Large HTML
    files like `examples/*/fit_validation.html` should be generated on demand or in CI. If a
    committed reference artifact is needed, prefer a lightweight deterministic surface.
16. **Shipped example notebooks must stay aligned with the typed notebook contract.** When touching
    notebook generators/templates/examples, regenerate and verify that checked-in notebooks do not
    teach raw dict payload editing.
17. **Do not expose repository-layout example discovery as public product API.** Repo-local paths,
    example directories, and workflow constants may exist for internal tooling, but new public API
    should not require a checked-out repository layout.

---

## CI Gate

```bash
uv run poe ci   # ruff check + ty + pytest tests/
```

All three must be green before merging. The 5 pre-existing ty errors in
`fitting_config.py` and `plugins/notebook/core.py` are known — do not fix in
unrelated tasks.

When changing notebook materialization, example generation, reporting, or workflow
packaging, also run the most relevant focused suites, for example:

```bash
uv run pytest -q tests/unit/test_solver_runtime.py
uv run pytest -q tests/unit/test_notebook_materializer.py tests/unit/test_convert_command.py
uv run pytest -q tests/unit/test_plotting_shared_core.py tests/unit/test_result_bridge.py tests/unit/test_report.py
uv run pytest -q tests/validation/ -m validation
```

---

## Prototype Reference

`prototype/` is a clean-room reference with **zero `spectrafit.*` imports**.
It validates Phases 1–5 of the v2 migration architecture end-to-end.
Use it as the canonical pattern source when implementing new features.

**Never add `spectrafit.*` imports to `prototype/`.** Copy patterns into `spectrafit/`.

---

## User-Centered Repo Hygiene

- Keep end-user surfaces obvious:
  - CLI/runtime orchestration in `spectrafit.cli.*` / `spectrafit.core.*`
  - notebook runtime and materialization in `spectrafit.jupyter.*`
  - reporting and dashboard rendering in `spectrafit.reporting.*`
- Do not expose repository-layout assumptions as public package API unless they are
  intentionally supported.
- If an example, notebook, or generated artifact is committed, treat it as product
  documentation: it must match the current supported workflow, not a legacy or
  transitional path.
- Repo-generated artifacts must have an explicit policy:
  - generated HTML reference files should normally be gitignored or CI-produced
  - generated notebooks should only be committed if they are intentionally curated
    user-facing examples and are kept fresh with regeneration checks
- Prefer **Delete / Move / Modify / Add** decisions explicitly in reviews:
  - **Delete** stale generated artifacts and misleading compatibility-era docs
  - **Move** reusable logic out of `scripts/` and runtime logic / pipeline entry
    contracts out of `models/`
  - **Modify** examples/docs when the supported UX changes
  - **Add** focused CI freshness checks when generated examples must remain in git

---

## Detailed Instructions

Scoped instruction files are auto-loaded by VS Code Copilot:

| File | Scope |
|------|-------|
| `.github/instructions/architecture.instructions.md` | `spectrafit/**/*.py` |
| `.github/instructions/code-style.instructions.md` | `spectrafit/**/*.py`, `tests/**/*.py`, `prototype/**/*.py` |
| `.github/instructions/testing.instructions.md` | `tests/**/*.py`, `spectrafit/**/test/**/*.py` |
| `.github/instructions/prototype-reference.instructions.md` | `spectrafit/**/*.py`, `prototype/**/*.py` |
| `.github/instructions/state-of-the-art.instructions.md` | `spectrafit/**/*.py`, `docs/**/*.md` |

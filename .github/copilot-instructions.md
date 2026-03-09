# Copilot Instructions for SpectraFit

> **Version:** v2.0.0 migration in progress on branch `v2.0.0`
> **Detailed instructions:** see `.github/instructions/` for scoped files loaded automatically.

---

## Project Overview

SpectraFit fits 1D–3D X-ray absorption / emission spectra using `lmfit` + `scipy`.
CLI-first (`typer`), also usable as a Python API and Jupyter notebook plugin.
Package management: `uv`. Build backend: `hatchling`. Python 3.11–3.13.

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
| Reporting | tabulate, seaborn |
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
      → SolverModels(df, config)
          → config.build_composite_model()
              → build_composite_bundle(components)  ← functools.reduce(+, models)
      → PostProcessing [FROZEN]
  → FittingResult
```

**Key modules:**
- `spectrafit/core/fitting_config.py` — `UnifiedFittingConfig` (central model)
- `spectrafit/models/peak_models.py` — `FitParameter`, `Component`
- `spectrafit/models/bundle.py` — `CompositeModelBundle`, `build_composite_bundle()`
- `spectrafit/models/naming.py` — `lmfit_param_name()` (SINGLE source for all param names)
- `spectrafit/models/fitting_context.py` — `FittingContext`, `FittingMode`
- `spectrafit/models/data_config.py` — `DataConfig`

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

---

## CI Gate

```bash
uv run poe ci   # ruff check + ty + pytest tests/
```

All three must be green before merging. The 5 pre-existing ty errors in
`fitting_config.py` and `plugins/notebook/core.py` are known — do not fix in
unrelated tasks.

---

## Prototype Reference

`prototype/` is a clean-room reference with **zero `spectrafit.*` imports**.
It validates Phases 1–5 of the v2 migration architecture end-to-end.
Use it as the canonical pattern source when implementing new features.

**Never add `spectrafit.*` imports to `prototype/`.** Copy patterns into `spectrafit/`.

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
